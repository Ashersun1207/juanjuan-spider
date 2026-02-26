# juanjuan-spider — 决策记录

---

## 核心原则

**不造轮子。找最成熟可靠的开源项目集成，在上面做适配和优化。**

- 选项目标准：GitHub 10K+ ⭐、活跃维护、社区大
- 我们只做：选型、封装 CLI、场景适配、输出优化
- 我们不做：重新实现浏览器引擎、反检测算法、内容提取器

---

## D1: 定位为通用爬虫工具（2026-02-26）

**背景**：讨论 web-scraper 的定位
**决策**：通用工具，不局限于金融场景，覆盖所有需要浏览器渲染+反检测的抓取需求
**理由**：
- 爬虫能力是通用的，金融只是使用场景之一
- 新闻、论坛、产品页、文档站、研报都会用到
- 保持通用性，未来可独立发展或集成到任何项目
**影响**：架构设计不针对特定领域，站点适配器作为可插拔模块

## D2: 独立仓库 + Python 技术栈（2026-02-26）

**背景**：放 gainlab-mcp 里还是独立仓库？Python 还是改写 TS？
**决策**：独立仓库 `web-scraper/`，保持 Python
**理由**：
- Playwright Python 生态比 Node 成熟（stealth 库、readability 等）
- 独立仓库方便单独维护和升级依赖
- gainlab-mcp 那边加 tool 代理调用即可
**影响**：技术栈不统一（Python vs TS），但利大于弊

## D3: Readability 作为默认正文提取（2026-02-25）

**背景**：v0.1 内容提取靠启发式去 nav/header/footer，效果一般
**决策**：引入 readability-lxml（Mozilla Readability Python 移植），作为默认提取方式
**理由**：
- Firefox 阅读模式验证过的算法，成熟可靠
- 自动去广告/导航/侧边栏，输出干净正文
- `--raw` 可跳过，保留灵活性
**影响**：新增依赖 readability-lxml，输出质量显著提升

## D4: 代理策略 — 默认走 Clash（2026-02-25）

**背景**：很多目标站点需要代理才能访问
**决策**：默认走本机 Clash（127.0.0.1:7897），`--no-proxy` 可关
**理由**：本机 Clash 稳定可用，不需要额外代理服务
**影响**：国内站点记得加 --no-proxy

## D5: 底层切换到 Crawl4AI（2026-02-26）

**背景**：自写的 Playwright+Stealth+Readability 在 HN/SPA/金十等站点效果差
**决策**：用 Crawl4AI（58K+ ⭐）替代自写引擎，scrape.py 变成薄封装
**理由**：
- 不造轮子，集成成熟项目再优化
- Crawl4AI 原生支持：异步、fit markdown（智能去噪）、反检测、深度爬取
- HN 从空→有内容，金十从只有标题→14K chars
- 社区活跃（50K+），持续维护
**影响**：需要 Python 3.12+（用 venv 隔离），依赖变多但功能大幅增强

## D6: Python 3.12 venv 隔离（2026-02-26）

**背景**：系统 Python 3.9，Crawl4AI 需要 3.10+
**决策**：在项目内用 `python3.12 -m venv .venv`，不动系统 Python
**理由**：隔离干净，不影响其他工具
**影响**：运行需先 `source .venv/bin/activate`

## D7: 分层包结构 + 双引擎路由（2026-02-26）

**背景**：scrape.py 单文件已 150 行，需加存储和 MCP，继续塞不下
**决策**：拆成 spider/ 包，5 层（core/engines/adapters/storage/infra）+ 双引擎自动路由
**理由**：
- 参考 Crawlee 架构（ContextPipeline + Router + Session）大幅简化
- Router 按域名自动选 Crawl4AI（JS渲染）或 HTTP（静态页）
- 每层职责单一，新增引擎/适配器不改核心
**影响**：代码量从 150 行→1998 行（含测试），但每个文件 ≤200 行

## D8: SQLite + 文件双写存储（2026-02-26）

**背景**：抓完 stdout 输出，用完即弃，无法查历史/去重/缓存
**决策**：SQLite 存元数据（url/domain/hash/时间），pages/ 目录存 markdown 文件
**理由**：
- SQLite 查询快（按域名/时间/关键词），单文件免部署
- markdown 文件人类可读，Agent 可直接 read
- content_hash 去重：同 URL 内容没变不重复存
- 不用 ORM，直接 sqlite3 模块，50 行搞定
**影响**：storage/ 目录 gitignore，不提交爬取数据

## D9: Crawl4AI 引擎级去噪 + 站点适配器（2026-02-26）

**背景**：BBC 30K 字符中 60%+ 是导航菜单，正文被淹没
**决策**：两层去噪——引擎级（excluded_tags/selector）+ 站点适配器（transform）
**理由**：
- 引擎级：通用规则（去 nav/footer/header/aside/广告），所有站点受益
- 适配器：站点专用清洗（BBC 去重复导航链接、CNBC 去 Skip Navigation）
- 实测 BBC -56%、CNBC -53%，正文可读性大幅提升
**影响**：新增 adapters/news.py，Router 自动注册

## D10: MCP Server — 4 tools stdio 模式（2026-02-26）

**背景**：Spider 只能 CLI 用，Agent 无法调用
**决策**：MCP Server 暴露 4 个 tools（scrape/batch/query/screenshot），stdio 模式
**理由**：
- stdio 最简单，Claude Desktop / OpenClaw 直接配就能用
- 4 个 tools 覆盖：单抓、批量、查历史、截图
- 复用引擎和存储实例，不重复初始化
**影响**：新增 spider/mcp/，启动 `python3 -m spider.mcp.server`

## D11: trafilatura 内容提取层（2026-02-26）

**背景**：adapter 只做 regex 删噪音，信噪比仍然低；HTTP 引擎没有 fit_markdown
**决策**：集成 trafilatura 2.0.0 作为 Engine→Adapter 之间的提取层
**对比**：

| 维度 | trafilatura | readability-lxml | 手写 regex |
|---|---|---|---|
| F-Score (750文档) | **0.914** | 0.801 | ~0.5 |
| 元数据提取 | ✅ | ❌ | ❌ |
| 维护 | 活跃 (ACL 2021) | 低频 | 自维护 |

**理由**：
- 学术评测冠军，精度+召回全面领先
- 自带元数据提取（author/date/sitename），省大量 adapter 工作
- 质量评分择优：trafilatura vs 引擎 fit_markdown，取更好的
- HTTP 引擎的 fit_markdown 空白问题一并解决
**影响**：新增 spider/core/extractor.py，main.py +3行集成，+1 依赖

## D12: adapter 不再覆盖 fit_markdown（2026-02-26）

**背景**：所有 adapter 的 transform() 都执行 `fit_markdown=md`，把 Crawl4AI 自带的 Readability 结果覆盖了
**决策**：adapter 只清洗 markdown（raw），不碰 fit_markdown
**理由**：这是 bug，不是 feature。fit_markdown 应该由引擎或 Extractor 产生
**影响**：4 个 adapter 文件修改

---

_Last updated: 2026-02-26_
