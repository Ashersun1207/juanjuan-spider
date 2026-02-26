# web-scraper — 决策记录

---

## D1: 定位为 GainLab 生态配套（2026-02-26）

**背景**：讨论 web-scraper 是做独立产品还是内部工具
**决策**：GainLab 生态配套，不做独立 SaaS
**理由**：
- 正面竞争 Firecrawl/Crawlee 不划算（对手有先发 + 融资）
- 作为 GainLab Agent 的数据补充能力更有价值
- FMP/EODHD 覆盖不到的数据（新闻正文、EA 实盘、研报）靠爬虫补齐
**影响**：不需要做 UI / 计费 / 用户体系，专注抓取质量和 Agent 集成

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

---

_Last updated: 2026-02-26_
