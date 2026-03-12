# 架构链 — 架构演进决策

---

## A1: 5 层分包

**为什么分 5 层？**
```
core/      — 配置、路由、提取器（引擎无关）
engines/   — Crawl4AI + HTTP（可插拔）
adapters/  — 站点适配器（transform + config 定制）
storage/   — SQLite + 文件双写
infra/     — MCP Server
```
- 每层职责单一，新增引擎/适配器不改核心
- 参考 Crawlee 的 ContextPipeline 思想

## A2: 双引擎路由

**为什么两个引擎？**
- Crawl4AI（浏览器）：SPA/JS 渲染/反检测
- HTTP（httpx+markdownify）：静态页，快 10 倍、省资源

**路由逻辑**：
- BROWSER_REQUIRED 列表 → 强制 Crawl4AI
- STATIC_SAFE 列表 → 强制 HTTP
- 其他 → 默认 Crawl4AI（安全优先）

## A3: 三层去噪

**为什么三层？**
1. **引擎级**：excluded_tags 去 nav/footer/aside（通用，所有站点受益）
2. **适配器**：站点专用 transform（regex 删特定噪音）
3. **提取器**：trafilatura 深度正文提取（学术级精度）

**为什么不只用 trafilatura？**
- 引擎级先削减 60%+ 噪音，trafilatura 处理更小输入更准确
- 适配器处理 trafilatura 不覆盖的站点特异噪音（如重复导航链接）

## A4: SQLite + 文件双写

**为什么不只用 SQLite？**
- markdown 文件人类可读，Agent 可 `read` 命令直接读
- SQLite 负责查询（域名/时间/关键词），文件负责存内容

**为什么不只用文件？**
- 去重需要 content_hash 索引
- 按域名/时间查询文件系统做不到

## A5: MCP 调 main.crawl()

**为什么不让 MCP 独立实现管道？**
- L9 教训：MCP 独立实现导致 trafilatura/adapter 全部失效
- 单一真相源：CLI/MCP/未来 API 都调同一个 crawl()
- 管道任何改动自动同步到所有入口
