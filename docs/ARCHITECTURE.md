# juanjuan-spider — 架构设计

_可演进的通用爬虫，支持 MCP 接入，供 Agent / AI 工具调用。_

---

## 设计原则

1. **不造轮子** — 集成成熟项目（Crawl4AI 等），在上面做适配和优化
2. **可演进** — 分层解耦，换引擎不影响上层，加功能不改核心
3. **MCP 原生** — Agent / AI 工具通过 MCP 协议直接调用
4. **CLI 兼容** — 人类也能命令行直接用

## 架构总览

```
┌──────────────────────────────────────────────────┐
│                  接入层 (Interface)                │
│                                                    │
│   ┌──────────┐  ┌──────────┐  ┌────────────────┐ │
│   │   CLI    │  │ MCP Server│  │  Python API    │ │
│   │ scrape.py│  │ (stdio)   │  │  import spider │ │
│   └────┬─────┘  └────┬─────┘  └──────┬─────────┘ │
│        └──────────────┼───────────────┘           │
├──────────────────────┬┤───────────────────────────┤
│                  核心层 (Core)                      │
│                      │                             │
│   ┌──────────────────▼──────────────────────────┐ │
│   │              Router (路由器)                  │ │
│   │  URL/平台 → 选引擎 → 选适配器 → 选输出格式  │ │
│   └──────────────────┬──────────────────────────┘ │
│                      │                             │
│   ┌──────────────────▼──────────────────────────┐ │
│   │           Engine (引擎层)                     │ │
│   │                                              │ │
│   │  ┌────────────┐  ┌────────────┐  ┌────────┐ │ │
│   │  │ Crawl4AI   │  │  HTTP轻量  │  │ 未来…  │ │ │
│   │  │ (浏览器渲染)│  │ (无需浏览器)│  │        │ │ │
│   │  └────────────┘  └────────────┘  └────────┘ │ │
│   └──────────────────┬──────────────────────────┘ │
│                      │                             │
│   ┌──────────────────▼──────────────────────────┐ │
│   │       Extractor (内容提取层) — v0.5 新增      │ │
│   │                                              │ │
│   │  trafilatura 正文提取 + 质量评分择优          │ │
│   │  自动提取元数据 (author/date/sitename)        │ │
│   └──────────────────┬──────────────────────────┘ │
│                      │                             │
│   ┌──────────────────▼──────────────────────────┐ │
│   │         Adapter (站点适配器)                  │ │
│   │                                              │ │
│   │  通用默认 │ 知乎 │ 小红书 │ 微博 │ Reddit… │ │
│   │  (每个适配器做站点特有精调，不负责正文提取)   │ │
│   └──────────────────┬──────────────────────────┘ │
│                      │                             │
│   ┌──────────────────▼──────────────────────────┐ │
│   │          Output (输出层)                      │ │
│   │                                              │ │
│   │  markdown │ fit │ JSON │ text │ screenshot   │ │
│   └─────────────────────────────────────────────┘ │
├───────────────────────────────────────────────────┤
│                 基础设施层 (Infra)                  │
│                                                    │
│  ┌─────────┐ ┌──────────┐ ┌───────┐ ┌──────────┐│
│  │ Session │ │  Proxy   │ │ Cache │ │  Config  ││
│  │ Manager │ │  Manager │ │       │ │          ││
│  │(登录态) │ │(代理轮换)│ │(结果) │ │(yaml/env)││
│  └─────────┘ └──────────┘ └───────┘ └──────────┘│
└───────────────────────────────────────────────────┘
```

## 各层职责

### 接入层 (Interface)

| 接口 | 说明 | 用户 |
|---|---|---|
| **CLI** | `scrape.py <URL> [选项]` | 人类 / 卷卷直接调用 |
| **MCP Server** | stdio 模式，暴露 tools | Claude / OpenClaw / 其他 Agent |
| **Python API** | `from spider import crawl` | 代码集成 |

三个接口共用同一个 Core，只是入口不同。

### MCP Tools 设计

```yaml
tools:
  - spider_scrape          # 抓取单个 URL → markdown/JSON
    params: url, format, selector, wait, scroll, max_chars
    
  - spider_screenshot      # 网页截图
    params: url, full_page, viewport
    
  - spider_search          # 平台内搜索（知乎/小红书/微博等）
    params: platform, keyword, limit
    
  - spider_batch           # 批量抓取
    params: urls[], format, concurrency
    
  - spider_deep_crawl      # 深度爬取（递归发现子页面）
    params: url, max_depth, max_pages, include_patterns
```

### 核心层 (Core)

**Router（路由器）**
```python
def route(url: str) -> tuple[Engine, Adapter]:
    """
    URL 进来 → 判断用哪个引擎 + 哪个适配器
    
    规则：
    - zhihu.com → Crawl4AI + ZhihuAdapter
    - xiaohongshu.com → Crawl4AI + XHSAdapter  
    - weibo.com → Crawl4AI + WeiboAdapter
    - reddit.com → Crawl4AI + RedditAdapter (需登录态)
    - 静态页面 → HTTP轻量引擎
    - 其他 → Crawl4AI + DefaultAdapter
    """
```

**Engine（引擎层）**

统一接口，可插拔：
```python
class BaseEngine(ABC):
    async def fetch(self, url, config) -> RawResult
    async def screenshot(self, url, config) -> bytes
    async def close(self)
```

当前实现：
- `Crawl4AIEngine` — 浏览器渲染，反检测，主力引擎
- `HTTPEngine` — 简单 HTTP 请求（不需要 JS 渲染的页面，省资源）

**Adapter（站点适配器）**

每个适配器是一个配置+逻辑包：
```python
class BaseAdapter:
    name: str              # "zhihu" / "xhs" / "default"
    domains: list[str]     # ["zhihu.com", "zhuanlan.zhihu.com"]
    needs_login: bool      # 是否需要登录态
    wait_for: str | None   # 等待某个元素出现
    css_selector: str | None  # 只提取这部分
    js_code: str | None    # 页面加载后执行的 JS
    scroll: bool           # 是否需要滚动
    
    def transform(self, raw: RawResult) -> CleanResult:
        """站点专用的清洗/转换逻辑"""
```

**Output（输出层）**

统一输出格式：
```python
class CrawlResult:
    url: str
    title: str
    markdown: str          # 原始 markdown
    fit_markdown: str      # 智能去噪版
    html: str
    text: str
    screenshot: bytes | None
    metadata: dict         # 提取时间、字符数、引擎信息等
    links: list[str]
```

### 基础设施层 (Infra)

| 模块 | 说明 | 参考 |
|---|---|---|
| **SessionManager** | 登录态保存/复用（Playwright context） | MediaCrawler 思路 |
| **ProxyManager** | 代理池管理、轮换、健康检查 | Crawlee 设计 |
| **Cache** | 结果缓存（SQLite），避免重复抓取 | Crawl4AI 缓存 |
| **Config** | YAML 配置 + 环境变量 | — |

## 目录结构（v0.4 实际）

```
juanjuan-spider/
├── scrape.py              # CLI 入口（向后兼容 + --save / --no-cache）
├── requirements.txt       # 生产依赖
├── requirements-dev.txt   # 开发依赖
│
├── spider/                # Python 包
│   ├── __init__.py        # from spider import crawl, CrawlResult
│   ├── main.py            # crawl() 核心函数，串联 Router→Engine→Adapter→Storage
│   ├── core/
│   │   ├── router.py      # URL → (Engine, Adapter) 路由
│   │   ├── engine.py      # BaseEngine 抽象基类 + FetchConfig
│   │   ├── extractor.py   # ContentExtractor — trafilatura 正文提取 + 质量择优 (v0.5)
│   │   └── result.py      # CrawlResult Pydantic 数据模型
│   ├── engines/
│   │   ├── crawl4ai_engine.py  # Crawl4AI 浏览器渲染引擎（主力）
│   │   └── http_engine.py      # httpx 轻量引擎（静态页面）
│   ├── adapters/
│   │   ├── default.py     # DefaultAdapter 基类（可子类化）
│   │   ├── news.py        # BBC / CNBC / Reuters / 金十
│   │   ├── social.py      # Reddit / X / Medium / YouTube
│   │   ├── finance.py     # Investing / Yahoo Finance / Myfxbook / Bloomberg / WSJ / FT
│   │   └── tech.py        # TechCrunch / The Verge / Wikipedia / HN
│   ├── storage/
│   │   └── sqlite.py      # SQLite 元数据 + pages/ 文件双写
│   ├── mcp/
│   │   ├── server.py      # MCP Server（4 tools）
│   │   └── __main__.py    # python3 -m spider.mcp 启动
│   └── infra/
│       ├── session.py     # 登录态管理
│       ├── proxy.py       # 代理管理
│       └── config.py      # SpiderConfig (pydantic-settings)
│
├── storage/               # 运行时数据（gitignore）
│   ├── spider.db          # SQLite 元数据索引
│   └── pages/YYYY-MM/     # markdown 文件（按月分目录）
│
├── scripts/
│   ├── project-boot.sh    # 新会话启动恢复
│   ├── verify.sh          # commit 前验证（V1-V9）
│   └── sync.sh            # 文档+memory 自动同步
│
├── tests/                 # pytest 测试
├── docs/                  # 项目文档
└── .venv/                 # Python 3.12 虚拟环境
```

## 演进路线

| 阶段 | 做什么 | 状态 |
|---|---|---|
| **v0.1-v0.3** | Playwright → Crawl4AI 引擎 + CLI | ✅ 完成 |
| **v0.4** | 分层重构 + SQLite 存储 + MCP Server + 适配器 + 去噪 | ✅ 完成 |
| **v0.5（当前）** | trafilatura 提取层 + 24站适配器 + 质量评分择优 + 58 tests | ✅ 完成 |
| **v0.6** | 代理管理 + 批量/深度爬取 | 待做 |
| **v1.0** | 稳定 API + 完整测试 + OpenClaw Skill | 待做 |

## 参考项目

| 借鉴内容 | 来源 | license |
|---|---|---|
| 分层架构 + 请求队列 + Session 池 + 存储抽象 | **Crawlee** | Apache-2.0 ✅ |
| LLM-ready markdown + 异步引擎 + 反检测 | **Crawl4AI** | Apache-2.0 ✅ |
| Playwright 登录态持久化思路 | **MediaCrawler** | 仅参考思路，代码自写 |
| MCP tool 设计 | **mcp-crawl4ai** | MIT ✅ |

---

_Last updated: 2026-02-26 (v0.5 — trafilatura 提取层)_
