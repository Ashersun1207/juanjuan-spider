# Crawlee Python 架构深度分析

> 基于 crawlee-python 源码实际阅读，为 juanjuan-spider 项目提供架构参考。
> 日期: 2025-02-25

---

## 1. 分层架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                      用户层 (User API)                           │
│  crawler.run() / @router.handler('label') / await ctx.push_data │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    具体 Crawler 层                                │
│  PlaywrightCrawler / HttpCrawler / BeautifulSoupCrawler / ...    │
│  每种 Crawler 通过 ContextPipeline.compose() 注入自己的中间件链    │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│              AbstractHttpCrawler 层 (HTTP 通用逻辑)              │
│  _create_static_content_crawler_pipeline():                      │
│    pre_nav_hooks → make_http_request → status_code_check         │
│    → parse_response → blocked_check                              │
│  含: HttpParser 抽象 / enqueue_links / extract_links             │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                   BasicCrawler 层 (核心引擎)                     │
│  请求调度 / 重试 / Session 管理 / 自动缩放 / 统计 / 存储         │
│  核心循环: AutoscaledPool → fetch_request → context_pipeline     │
│           → router(handler) → commit_result                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    基础设施层 (Infrastructure)                    │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐ │
│  │ StorageClient│ │ EventManager │ │ Configuration            │ │
│  │ (FS/Mem/SQL/ │ │ (Local/     │ │ (pydantic-settings       │ │
│  │  Redis)      │ │  Platform)  │ │  + env vars)             │ │
│  └──────────────┘ └──────────────┘ └──────────────────────────┘ │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐ │
│  │ HttpClient   │ │ SessionPool  │ │ ProxyConfiguration       │ │
│  │ (Impit/Curl/ │ │ + Session    │ │ (轮询/分层/自定义)        │ │
│  │  Playwright) │ │              │ │                          │ │
│  └──────────────┘ └──────────────┘ └──────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │ ServiceLocator (全局单例, 惰性初始化, 管理上述所有服务)         ││
│  └──────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

**代码依据**: `src/crawlee/_service_locator.py` 中 `ServiceLocator` 类管理三个核心服务:
- `Configuration` — 全局配置
- `EventManager` — 事件管理
- `StorageClient` — 存储后端

---

## 2. 每层的核心类和职责

### 2.1 BasicCrawler — 核心引擎 (`_basic_crawler.py`, ~1679行)

**职责**: 请求调度、重试、生命周期管理

**核心属性**:
```python
class BasicCrawler(Generic[TCrawlingContext, TStatisticsState]):
    _request_manager: RequestManager          # 请求队列
    _session_pool: SessionPool                # Session 池
    _proxy_configuration: ProxyConfiguration  # 代理配置
    _http_client: HttpClient                  # HTTP 客户端
    _router: Router[TCrawlingContext]          # 请求路由
    _context_pipeline: ContextPipeline        # 中间件管道
    _autoscaled_pool: AutoscaledPool          # 自动缩放并发池
    _statistics: Statistics                   # 统计
    _snapshotter: Snapshotter                 # 系统资源快照
```

**关键设计**: BasicCrawler 是 **泛型类**，`TCrawlingContext` 类型参数决定了用户 handler 收到什么样的上下文。子类通过 `_context_pipeline` 逐步增强上下文。

### 2.2 AbstractHttpCrawler — HTTP 抽象层 (`_abstract_http_crawler.py`)

**职责**: HTTP 请求的发送、响应解析、链接提取的通用逻辑

**中间件管道** (`_create_static_content_crawler_pipeline`):
```python
ContextPipeline()
    .compose(self._execute_pre_navigation_hooks)   # 前置钩子
    .compose(self._make_http_request)              # 发 HTTP 请求
    .compose(self._handle_status_code_response)    # 状态码检查
    .compose(self._parse_http_response)            # 解析响应
    .compose(self._handle_blocked_request_by_content)  # 反爬检测
```

**关键**: `AbstractHttpParser` 抽象解析器 — BeautifulSoup / Parsel / 原始HTTP 分别有各自的 Parser 实现。

### 2.3 PlaywrightCrawler — 浏览器层 (`_playwright_crawler.py`)

**中间件管道**:
```python
ContextPipeline()
    .compose(self._open_page)                        # 打开浏览器页面
    .compose(self._navigate)                         # 导航到 URL
    .compose(self._handle_status_code_response)      # 状态码检查
    .compose(self._handle_blocked_request_by_content) # 反爬检测
```

**关键**: `BrowserPool` 管理浏览器实例和页面，支持指纹生成 (`FingerprintGenerator`)。

### 2.4 ContextPipeline — 中间件管道 (`_context_pipeline.py`)

这是 Crawlee 最精妙的设计之一：

```python
class ContextPipeline(Generic[TCrawlingContext]):
    def compose(self, middleware) -> ContextPipeline[TMiddlewareCrawlingContext]:
        """链式注册中间件，返回新的 Pipeline 实例（不可变链表）"""
        return ContextPipeline(
            _middleware=middleware,
            _parent=self,
        )

    async def __call__(self, crawling_context, final_context_consumer):
        """按序执行中间件链，最后调用用户 handler"""
```

**每个中间件是一个 AsyncGenerator**，`yield` 前是初始化，`yield` 后是清理。与 Python 的 `contextmanager` 模式一致。异常通过 `asend()` 传回中间件的清理阶段。

### 2.5 Router — 请求路由 (`router.py`)

```python
class Router(Generic[TCrawlingContext]):
    _default_handler: RequestHandler | None
    _handlers_by_label: dict[str, RequestHandler]

    # 基于 request.label 分发到对应 handler
    async def __call__(self, context):
        if context.request.label in self._handlers_by_label:
            return await self._handlers_by_label[label](context)
        return await self._default_handler(context)
```

**设计亮点**: Router 本身实现了 `RequestHandler` 的调用签名（`__call__`），所以它可以直接传给 `BasicCrawler(request_handler=router)`。

### 2.6 Request 模型 (`_request.py`)

```python
class Request(BaseModel):
    url: str
    unique_key: str           # 去重键
    method: HttpMethod        # GET/POST/...
    headers: HttpHeaders
    payload: HttpPayload | None
    user_data: UserData       # 包含 label, crawlee_data 等
    retry_count: int
    no_retry: bool
    loaded_url: str | None    # 重定向后的实际 URL
    # + CrawleeRequestData: state, session_rotation_count, crawl_depth, session_id, etc.
```

**关键**: `UserData` 是一个 Pydantic model + MutableMapping 混合体，`label` 用于路由，`__crawlee` 命名空间存放框架内部元数据。

### 2.7 Configuration (`configuration.py`)

```python
class Configuration(BaseSettings):  # pydantic-settings
    model_config = SettingsConfigDict(populate_by_name=True)

    internal_timeout: timedelta | None
    log_level: LogLevel = 'INFO'
    purge_on_start: bool = True
    persist_state_interval: timedelta = timedelta(minutes=1)
    max_used_cpu_ratio: float
    max_used_memory_ratio: float
    storage_dir: str = './storage'
    # ... 所有字段支持 CRAWLEE_ 前缀的环境变量
```

**设计**: 基于 pydantic-settings，支持环境变量覆盖 + 类型验证 + 默认值。全局唯一实例通过 ServiceLocator 管理。

---

## 3. 请求生命周期流程图

```
用户: crawler.run(['https://example.com'])
  │
  ▼
┌─────────────────────────────────────────────┐
│ 1. add_requests()                            │
│    - robots.txt 检查 (如果启用)               │
│    - Request.from_url() 创建 Request 对象     │
│    - 加入 RequestQueue (通过 RequestManager)  │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│ 2. AutoscaledPool.run()                      │
│    循环调用:                                  │
│    - __is_finished_function() → 检查队列空?   │
│    - __is_task_ready_function() → 有待处理?   │
│    - __run_task_function() → 执行下面的流程    │
│    并发度根据系统资源 (CPU/内存) 自动调整       │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│ 3. __run_task_function()                     │
│    a. request_manager.fetch_next_request()   │
│    b. 获取 Session (如果启用 session pool)    │
│    c. 获取 ProxyInfo (如果有代理配置)         │
│    d. 创建 BasicCrawlingContext              │
│    e. 记录统计开始                            │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│ 4. _run_request_handler(context)             │
│    执行 context_pipeline:                    │
│                                              │
│    [BasicCrawler 层]                         │
│    └─ _check_url_after_redirects             │
│                                              │
│    [AbstractHttpCrawler 层] (HTTP 爬虫)       │
│    ├─ _execute_pre_navigation_hooks          │
│    ├─ _make_http_request                     │
│    ├─ _handle_status_code_response           │
│    ├─ _parse_http_response                   │
│    └─ _handle_blocked_request_by_content     │
│                                              │
│    [PlaywrightCrawler 层] (浏览器爬虫)        │
│    ├─ _open_page                             │
│    ├─ _navigate                              │
│    ├─ _handle_status_code_response           │
│    └─ _handle_blocked_request_by_content     │
│                                              │
│    最后调用: router(final_context)            │
│    → 用户定义的 request_handler               │
└─────────────────┬───────────────────────────┘
                  │
         ┌────────┴─────────┐
         │                  │
    ✅ 成功              ❌ 异常
         │                  │
         ▼                  ▼
┌────────────────┐  ┌──────────────────────────┐
│ 5a. 提交结果    │  │ 5b. 错误处理              │
│ - push_data    │  │ - RequestHandlerError     │
│ - add_requests │  │   → _handle_request_error │
│ - KVS 写入    │  │   → retry_count++         │
│ - mark_handled │  │   → reclaim_request       │
│ - session.     │  │ - SessionError            │
│   mark_good()  │  │   → session.retire()      │
│ - 记录统计完成  │  │   → session_rotation++    │
└────────────────┘  │   → reclaim_request       │
                    │ - 超过 max_retries?        │
                    │   → failed_request_handler │
                    │   → mark_handled + ERROR   │
                    └──────────────────────────┘
```

**代码依据**: `__run_task_function()` 方法 (line 1385-1508) 包含完整的错误分支处理。

---

## 4. 扩展点设计分析

### 4.1 添加新 Crawler 类型

**方式**: 继承 `BasicCrawler` 或 `AbstractHttpCrawler`，注入自定义 `ContextPipeline`。

```python
# PlaywrightCrawler 的做法:
kwargs['_context_pipeline'] = (
    ContextPipeline()
    .compose(self._open_page)
    .compose(self._navigate)
    .compose(self._handle_status_code_response)
    .compose(self._handle_blocked_request_by_content)
)
kwargs['_additional_context_managers'] = [self._browser_pool]
super().__init__(**kwargs)
```

**关键**: 子类通过 `_context_pipeline` 参数定义自己的中间件链，通过 `_additional_context_managers` 注入需要生命周期管理的资源（如浏览器池）。

继承层级:
```
BasicCrawler
├── AbstractHttpCrawler (+ HttpParser 抽象)
│   ├── HttpCrawler (原始 HTTP)
│   ├── BeautifulSoupCrawler (+ BS4 Parser)
│   ├── ParselCrawler (+ Parsel Parser)
│   └── 自定义 HTTP Crawler
└── PlaywrightCrawler (+ BrowserPool)
    └── 自定义浏览器 Crawler
```

### 4.2 添加新存储后端

**方式**: 实现 `StorageClient` 抽象基类。

```python
class StorageClient(ABC):
    @abstractmethod
    async def create_dataset_client(self, *, id, name, alias, configuration) -> DatasetClient
    @abstractmethod
    async def create_kvs_client(self, *, id, name, alias, configuration) -> KeyValueStoreClient
    @abstractmethod
    async def create_rq_client(self, *, id, name, alias, configuration) -> RequestQueueClient
```

Crawlee 已实现的存储后端（`src/crawlee/storage_clients/`）:
- `_file_system/` — 文件系统（默认）
- `_memory/` — 内存
- `_sql/` — SQL 数据库
- `_redis/` — Redis

每个后端需要实现三个子客户端:
- `DatasetClient` — push_data / get_data / iterate_items
- `KeyValueStoreClient` — get_value / set_value
- `RequestQueueClient` — add_batch / fetch_next / mark_handled / reclaim

**注册**: 通过 `ServiceLocator.set_storage_client()` 或构造 BasicCrawler 时传入 `storage_client` 参数。

### 4.3 添加新 HTTP 客户端

实现 `BaseHttpClient` 接口:
```python
class BaseHttpClient(ABC):
    @abstractmethod
    async def send_request(self, url, method, headers, payload, session, proxy_info) -> HttpResponse
```

已有实现: `ImpitHttpClient`（默认）、`CurlImpersonateHttpClient`、`PlaywrightHttpClient`

### 4.4 自定义 Session 创建

```python
SessionPool(
    create_session_function=lambda: Session(
        max_age=timedelta(minutes=30),
        max_error_score=5.0,
    )
)
```

### 4.5 自定义代理策略

```python
ProxyConfiguration(
    # 方式1: URL 列表轮询
    proxy_urls=['http://proxy1:8080', 'http://proxy2:8080'],
    # 方式2: 分层代理（自动升级）
    tiered_proxy_urls=[['http://cheap:8080'], ['http://premium:8080']],
    # 方式3: 完全自定义
    new_url_function=lambda session_id, request: 'http://custom:8080',
)
```

---

## 5. Session 和代理管理

### 5.1 Session (`sessions/_session.py`)

```python
class Session:
    _id: str                    # 唯一标识
    _max_age: timedelta         # 最大存活时间 (默认 50min)
    _max_error_score: float     # 最大错误分 (默认 3.0)
    _error_score_decrement: float  # 成功后扣减 (默认 0.5)
    _max_usage_count: int       # 最大使用次数 (默认 50)
    _cookies: SessionCookies    # Cookie 管理
    _blocked_status_codes: set  # 封禁状态码 {401, 403, 429}

    @property
    def is_usable(self) -> bool:
        return not (self.is_blocked or self.is_expired or self.is_max_usage_count_reached)

    def mark_good(self):  # 成功 → usage_count++, error_score -= decrement
    def mark_bad(self):   # 失败 → error_score += 1, usage_count++
    def retire(self):     # 主动退役 → error_score += max_error_score
```

### 5.2 SessionPool (`sessions/_session_pool.py`)

```python
class SessionPool:
    _max_pool_size: int = 1000
    # 实现为 async context manager
    # 支持持久化 (通过 RecoverableState + KVS)
    async def get_session(self) -> Session  # 随机取一个可用的
    async def get_session_by_id(self, session_id) -> Session | None
```

### 5.3 Session 与 Proxy 的联动

在 `__run_task_function()` 中:
```python
session = await self._get_session()         # 从池中取
proxy_info = await self._get_proxy_info(request, session)  # session.id 作为 proxy session_id
# → 同一个 session 总是绑定同一个 proxy URL
```

---

## 6. 错误处理和重试

### 6.1 错误类型层级

```python
SessionError                 # 触发 session 轮转，不计入 max_request_retries
├── ProxyError               # 代理错误
RequestHandlerError          # 用户 handler 异常，包含 crawling_context
ContextPipelineInitializationError  # 中间件初始化失败
ContextPipelineFinalizationError    # 中间件清理失败
ContextPipelineInterruptedError     # 中间件主动中断（跳过请求）
HttpStatusCodeError          # HTTP 状态码错误
├── HttpClientStatusCodeError # 4xx 客户端错误
UserDefinedErrorHandlerError # 用户 error handler 自己抛的异常
RequestCollisionError        # Session 冲突（请求绑定的 session 已失效）
```

### 6.2 重试策略

```python
# 两套独立的重试机制:

# 1. 请求重试 (max_request_retries, 默认 3)
#    适用: RequestHandlerError, ContextPipelineInitializationError
#    流程: retry_count++ → error_handler(可选) → reclaim_request
#    超限: → failed_request_handler → mark_handled(ERROR)

# 2. Session 轮转 (max_session_rotations, 默认 10)
#    适用: SessionError, ProxyError
#    流程: session.retire() → session_rotation_count++ → reclaim_request
#    独立于请求重试计数!
```

### 6.3 自定义错误处理

```python
@crawler.error_handler
async def on_error(context, error):
    # 在重试之前调用
    # 可以返回新的 Request 替换当前请求

@crawler.failed_request_handler
async def on_failed(context, error):
    # 在所有重试耗尽后调用
    # 可以做兜底处理，如记录到数据库
```

---

## 7. 配置管理

### 7.1 全局配置 (Configuration)

基于 `pydantic-settings`，支持:
- 代码中直接传参: `Configuration(log_level='DEBUG')`
- 环境变量: `CRAWLEE_LOG_LEVEL=DEBUG`
- 还支持 `APIFY_` 前缀（Apify 平台兼容）

### 7.2 ServiceLocator 模式

```python
# 全局单例
service_locator = ServiceLocator()

# 惰性初始化 — 第一次 get 时才创建默认实例
service_locator.get_configuration()   # → Configuration()
service_locator.get_event_manager()   # → LocalEventManager()
service_locator.get_storage_client()  # → FileSystemStorageClient()

# 设置自定义实例 (必须在第一次 get 之前)
service_locator.set_storage_client(RedisStorageClient())
```

**注意**: 一旦服务被获取过，就不能再设置新的（抛 `ServiceConflictError`）。这保证了全局一致性。

### 7.3 Crawler 级别配置覆盖

BasicCrawler 构造函数允许覆盖:
```python
BasicCrawler(
    configuration=Configuration(...),   # 覆盖全局配置
    event_manager=CustomEventManager(), # 覆盖事件管理器
    storage_client=CustomStorageClient(), # 覆盖存储后端
    # + 所有运行时参数如 max_request_retries, concurrency_settings 等
)
```

每个 Crawler 实例有自己的 `_service_locator` 副本。

---

## 8. MCP 相关

### 8.1 Crawlee 本身没有 MCP 支持

Crawlee 本身是爬虫框架，不提供 MCP server 功能。

### 8.2 Apify 有官方 MCP Server

- **仓库**: [apify/apify-mcp-server](https://github.com/apify/apify-mcp-server)
- **服务**: mcp.apify.com — 让 AI Agent 通过 MCP 协议调用 Apify 平台上的 Actor（包括 Crawlee 构建的爬虫）
- **原理**: MCP Server 暴露 Apify Actor 作为 tools，不是直接操作 Crawlee 实例

### 8.3 社区方案

搜索结果显示社区主要通过 Apify 平台 MCP Server 间接使用 Crawlee 能力，没有发现独立的 "Crawlee MCP Server"。

**对 juanjuan-spider 的启示**: 如果需要 MCP 集成，应该是在爬虫之上封装一层 MCP Server（暴露 `start_crawl`, `get_results`, `list_tasks` 等 tool），而不是在爬虫内部实现。

---

## 9. 对 juanjuan-spider 的具体建议

### 9.1 ✅ 值得学的

| Crawlee 设计 | 建议 | 原因 |
|---|---|---|
| **ContextPipeline (中间件管道)** | 核心学习 | AsyncGenerator 中间件模式优雅，支持初始化+清理，异常传播正确。我们可以简化为 3-4 层: 反爬检测 → HTTP请求 → 解析 → 数据提取 |
| **Router (标签路由)** | 直接采用 | 代码极简（~80行），基于 `request.label` 分发。对我们的多平台爬虫（Twitter/Reddit/Polymarket）非常适合 |
| **Request 模型** | 参考简化 | Pydantic model 管理 URL + 元数据 + 去重键 + 状态机。我们可以精简掉 `CrawleeRequestData` 中不需要的字段 |
| **Session 管理** | 参考设计 | error_score 机制（mark_good/mark_bad）+ 自动退役 + Cookie 绑定。对我们的反爬场景有用 |
| **分层代理 (tiered_proxy_urls)** | 值得参考 | 自动根据域名封禁率升级代理层级，巧妙。我们的场景可能需要 |
| **错误分类** | 采用思路 | `SessionError` 独立于请求重试、`ContextPipelineInterruptedError` 跳过请求 —— 不同错误走不同处理路径 |
| **pydantic-settings 配置** | 采用 | 环境变量 + 类型安全 + 默认值，一行搞定 |

### 9.2 ❌ 太重不需要的

| Crawlee 设计 | 跳过原因 |
|---|---|
| **AutoscaledPool + Snapshotter** | 根据 CPU/内存自动调整并发度。我们是轻量级爬虫，固定并发或简单的 semaphore 就够了 |
| **5种存储后端 (FS/Mem/SQL/Redis)** | 我们固定用 SQLite + 文件系统就够了，不需要这么多抽象层 |
| **ServiceLocator 全局单例** | 我们的爬虫实例少，直接依赖注入更清晰。ServiceLocator 是为了 Apify 平台的多实例场景设计的 |
| **BrowserPool + 指纹生成** | 我们暂不需要浏览器爬虫，即使需要可以后加 |
| **RequestQueue 持久化 + 断点续爬** | 我们的任务通常几分钟完成，不需要复杂的持久化队列。内存队列 + 简单重试就够 |
| **Statistics + ErrorTracker** | 我们可以用简单的计数器 + 日志，不需要完整的统计系统 |
| **StorageInstanceManager + 缓存** | 复杂的存储实例生命周期管理。我们用简单的工厂方法就够 |

### 9.3 🎯 我们的特殊需求

1. **多平台统一接口**: Crawlee 的 Crawler 抽象是围绕 "HTTP 请求 → HTML 解析" 设计的。我们需要适配 API-first 的平台（Twitter API, Reddit API, Polymarket API），这些不需要 HTML 解析但需要认证管理、Rate Limiting、分页逻辑。

2. **数据标准化层**: Crawlee 不关心输出数据的格式（push_data 是 generic dict）。我们需要在 Crawler 之上加一层数据标准化（统一的信号/信息模型）。

3. **MCP 集成层**: 作为 MCP tools 暴露给 AI Agent，需要一个 MCP Server 包装层。Crawlee 没有这个。

4. **调度和编排**: Crawlee 是单次 `run()` 模型（跑完就结束）。我们需要定时/事件触发的持续运行模式。

5. **轻量级**: 我们不需要 Crawlee 那种 "企业级通用爬虫框架" 的复杂度。目标是 **几千行代码** 覆盖我们的场景。

### 9.4 📐 推荐的 juanjuan-spider 架构

基于 Crawlee 的启发，但大幅简化:

```
┌────────────────────────────────────────────────┐
│              MCP Server Layer                   │
│  暴露 tools: crawl_url, search_topic,          │
│  get_latest_signals, list_sources              │
└────────────────────┬───────────────────────────┘
                     │
┌────────────────────▼───────────────────────────┐
│           Orchestrator Layer                    │
│  任务调度 / 定时触发 / 去重 / 结果聚合          │
└────────────────────┬───────────────────────────┘
                     │
┌────────────────────▼───────────────────────────┐
│           Spider Layer (学 Crawlee 的模式)       │
│                                                 │
│  BaseSpider (类比 BasicCrawler，但简化版)        │
│  ├── 中间件管道 (ContextPipeline 思路)           │
│  │   rate_limit → auth → request → parse        │
│  ├── Router (标签路由，直接学 Crawlee)            │
│  ├── Session 管理 (error_score 机制)             │
│  └── 重试逻辑 (SessionError 独立于 RequestError) │
│                                                 │
│  具体 Spider:                                    │
│  ├── HttpSpider (httpx + 简单解析)               │
│  ├── ApiSpider (REST API 专用，含分页/认证)       │
│  └── BrowserSpider (Playwright, 后期需要时加)     │
└────────────────────┬───────────────────────────┘
                     │
┌────────────────────▼───────────────────────────┐
│           Data Layer                            │
│  ├── Request (Pydantic model, 学 Crawlee)       │
│  ├── Result (标准化数据模型)                     │
│  ├── Storage (SQLite + 文件, 不需要抽象多后端)    │
│  └── Config (pydantic-settings, 学 Crawlee)     │
└────────────────────────────────────────────────┘
```

### 9.5 🔑 核心实现优先级

1. **P0 — Request + Router + 中间件管道**: 这是骨架。直接参考 Crawlee 的 `Request`、`Router`、`ContextPipeline`，各简化到 100 行以内。
2. **P0 — BaseSpider + HttpSpider**: 实现 `run()` + 简单并发（`asyncio.Semaphore`）+ 重试。
3. **P1 — Session + 代理管理**: 参考 Crawlee 的 `Session` 错误评分机制。
4. **P1 — ApiSpider**: 针对 REST API 的分页、认证、Rate Limit 封装。
5. **P2 — MCP Server 包装层**。
6. **P2 — 调度 + 持续运行模式**。

---

## 附录: Crawlee 代码量参考

| 文件 | 行数 | 说明 |
|---|---|---|
| `_basic_crawler.py` | ~1679 | 核心引擎，功能最密集 |
| `_context_pipeline.py` | ~120 | 中间件管道，代码极精炼 |
| `router.py` | ~80 | 请求路由，极简 |
| `_request.py` | ~400 | Request 模型 |
| `configuration.py` | ~200 | 全局配置 |
| `_session.py` | ~200 | Session 类 |
| `_session_pool.py` | ~220 | Session 池 |
| `_service_locator.py` | ~100 | 服务定位器 |
| `proxy_configuration.py` | ~200 | 代理配置 |
| `errors.py` | ~120 | 错误类型 |

**总结**: Crawlee Python 的核心代码约 3000 行（不含存储后端和浏览器层）。设计精良但偏重通用性。juanjuan-spider 应该取其精华（ContextPipeline、Router、Session error_score、配置模式），去其复杂度（AutoscaledPool、多存储后端、ServiceLocator），加上我们独有的需求（API 爬虫、MCP 集成、数据标准化）。目标代码量控制在 2000 行以内。