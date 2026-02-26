# juanjuan-spider — 项目状态

---

## 版本

**v0.4.1** (2026-02-26)

## 目录结构（当前）

```
juanjuan-spider/
├── scrape.py              # CLI 入口（保持兼容，新增 --save / --no-cache）
├── requirements.txt       # 生产依赖
├── requirements-dev.txt   # 开发依赖（pytest 等）
├── spider/                # 主包
│   ├── __init__.py        # from spider import crawl
│   ├── main.py            # crawl() 核心函数（串联 Router→Engine→Adapter→Storage）
│   ├── core/
│   │   ├── engine.py      # BaseEngine 抽象基类 + FetchConfig
│   │   ├── result.py      # CrawlResult Pydantic 模型（统一输出）
│   │   └── router.py      # URL → (Engine, Adapter) 路由
│   ├── engines/
│   │   ├── crawl4ai_engine.py  # Crawl4AI 浏览器引擎（主力）
│   │   └── http_engine.py     # httpx 轻量引擎（静态页面）
│   ├── adapters/
│   │   ├── default.py     # DefaultAdapter 基类（可子类化定制站点）
│   │   └── news.py        # BBC / CNBC / Reuters / 金十 适配器
│   ├── storage/
│   │   └── sqlite.py      # SQLite 元数据 + pages/ 文件双写存储
│   ├── mcp/
│   │   ├── server.py      # MCP Server（4 tools: scrape/batch/query/screenshot）
│   │   └── __main__.py    # python3 -m spider.mcp 启动
│   └── infra/
│       └── config.py      # SpiderConfig (pydantic-settings，SPIDER_ 前缀)
├── tests/                 # 48 tests，全绿
│   ├── test_result.py     # CrawlResult 模型（10 tests）
│   ├── test_router.py     # Router 路由逻辑（10 tests）
│   ├── test_storage.py    # SQLite CRUD + 缓存（16 tests）
│   ├── test_config.py     # 配置加载（5 tests）
│   ├── test_adapter.py    # 适配器（4 tests）
│   └── test_mcp.py        # MCP Server（3 tests）
├── storage/               # 运行时数据（gitignore）
│   ├── spider.db          # SQLite 元数据
│   └── pages/YYYY-MM/     # markdown 文件（按月分目录）
├── docs/
│   ├── ARCHITECTURE.md    # 完整架构设计
│   ├── decisions.md       # D1-D6 技术决策
│   ├── lessons.md         # 教训记录
│   ├── status.md          # 本文件
│   ├── research-crawler-deep-review.md       # 4 项目横向对比
│   ├── research-crawlee-architecture.md      # Crawlee 源码深度分析
│   └── research-open-source-crawlers.md      # 初步调研
└── scripts/
    └── project-boot.sh    # 会话恢复脚本
```

## 完成功能

| 功能 | 版本 | 说明 |
|---|---|---|
| 分层包结构 | v0.4 | spider/ 包，5 层架构 |
| CrawlResult 统一模型 | v0.4 | Pydantic v2，含 hash/char_count 计算字段 |
| 双引擎路由 | v0.4 | Crawl4AI（JS渲染）+ HTTP（静态）自动选择 |
| 适配器系统 | v0.4 | DefaultAdapter 可子类化，域名→适配器注册 |
| SQLite 存储 | v0.4 | 元数据+文件双写，去重，缓存查询，按域名/时间/关键词搜索 |
| pydantic-settings 配置 | v0.4 | SPIDER_ 环境变量覆盖 |
| CLI 向后兼容 | v0.4 | 原有参数全保留，新增 --save / --no-cache |
| 43 单元测试 | v0.4 | 全绿，覆盖4个核心模块 |
| 反检测/代理/Cookie | v0.3 | Crawl4AI 引擎支持 |
| Playwright + Stealth | v0.3 | enable_stealth=True |
| MCP Server | v0.4.1 | 4 tools（scrape/batch/query/screenshot），stdio 模式 |
| Crawl4AI 去噪 | v0.4.1 | excluded_tags/selector 过滤导航/页脚/广告 |
| 新闻适配器 | v0.4.1 | BBC(-56%) / CNBC(-53%) / Reuters / 金十 |

## 进行中

_无_

## 待做（按优先级）

### P1
- [x] ~~MCP Server（4 tools: scrape/batch/query/screenshot）~~ ✅
- [x] ~~新闻适配器（BBC/CNBC/Reuters/金十）~~ ✅
- [ ] Jina Reader L1 fallback（spider/engines/jina_engine.py）
- [ ] 知乎 / 小红书 适配器（需登录态管理）

### P2
- [ ] 登录态管理（SessionManager — Playwright context 持久化）
- [ ] 代理管理（ProxyManager — 轮换+健康检查）
- [ ] 批量 URL 抓取（--urls file.txt / spider_batch tool）
- [ ] Cloudflare challenge 检测 + 重试

### P3
- [ ] OpenClaw Skill 封装
- [ ] 页面变更监控（定期 diff + 通知）
- [ ] 深度爬取（spider_deep_crawl）
- [ ] 集成到 gainlab-mcp 作为 tool

## 已验证站点

| 站点 | 引擎 | 状态 | 备注 |
|---|---|---|---|
| HN | HTTP | ✅ | 自动路由静态引擎，1.6s |
| arXiv | HTTP | ✅ | 静态引擎，0.8s |
| BBC Business | Crawl4AI | ✅ | 适配器去噪，30K→13K(-56%)，7.8s |
| CNBC Economy | Crawl4AI | ✅ | 适配器去噪，24K→11K(-53%)，6.4s |
| 知乎 | Crawl4AI | ⚠️ | 引擎路由正确，需登录态 |
| GitHub | Crawl4AI | ⚠️ | SPA，从 STATIC_SAFE 移除，走浏览器 |
| Myfxbook | Crawl4AI | ✅ | v0.3 已测 |
| Yahoo Japan News | Crawl4AI | ✅ | v0.3 已测 |
| Bloomberg | Crawl4AI | ❌ | Cloudflare 拦截 |
| Reddit | Crawl4AI | ❌ | 需登录态 |
| Reuters | Crawl4AI | ⚠️ | 有适配器，待实测 |

## 扩展指南

### 新增站点适配器

```python
# spider/adapters/zhihu.py
from dataclasses import dataclass, field
from spider.adapters.default import DefaultAdapter
from spider.core.result import CrawlResult

@dataclass
class ZhihuAdapter(DefaultAdapter):
    name: str = "zhihu"
    domains: list = field(default_factory=lambda: ["zhihu.com"])
    needs_login: bool = True
    scroll: bool = True

    def transform(self, result: CrawlResult) -> CrawlResult:
        # 知乎专用清洗
        cleaned = result.markdown.replace("登录查看更多", "")
        return result.model_copy(update={"markdown": cleaned})
```

然后在 `spider/core/router.py` 的 `BROWSER_REQUIRED` 注册，并在 `spider/main.py` 或用户代码中 `router.register_adapter("zhihu.com", ZhihuAdapter())` 即可。

### 新增引擎

继承 `BaseEngine`，实现 `fetch()` 方法，在 Router 中注册：

```python
class JinaEngine(BaseEngine):
    name = "jina"
    async def fetch(self, url, config=None) -> CrawlResult: ...
```

### 查询存储

```python
from spider.storage.sqlite import SpiderStorage
s = SpiderStorage("storage/spider.db", "storage/pages")
s.recent(20)                    # 最近20条
s.get_by_domain("zhihu.com")    # 按域名
s.search("Python教程")           # 关键词搜索
s.get_cached("https://...", max_age_seconds=3600)  # 缓存查询
```

## 依赖版本

| 包 | 版本 |
|---|---|
| Crawl4AI | 0.8.0 |
| httpx | 0.28.1 |
| markdownify | 最新 |
| pydantic | 2.12.5 |
| pydantic-settings | 2.13.1 |
| playwright | 1.58.0 |
| pytest | 9.0.2 |

---

_Last updated: 2026-02-26 v0.4.0_
