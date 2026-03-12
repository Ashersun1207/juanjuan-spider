# 推理链 — 完整决策推理过程

_格式：输入 → 约束 → 候选方案 → 分析 → 排除 → 结论 → 验证_

---

## R1: 自写引擎 vs 集成成熟项目

**输入**：Playwright+Stealth+Readability 自写引擎在多个站点效果差
**约束**：不造轮子是核心原则；需要反检测+JS 渲染+智能去噪
**候选**：A) 继续优化自写 B) Crawl4AI（58K⭐）C) Scrapy+Splash D) crawlee
**分析**：
- A: 已写 150 行，每个站点都要调适配器，维护成本高
- B: 原生 async + fit_markdown + 反检测，HN 从空→有内容
- C: Splash 额外服务，部署复杂
- D: Node.js 生态，和现有 Python 不兼容
**排除**：A（效果差）C（复杂）D（语言不同）
**结论**：B — Crawl4AI 作为主引擎
**验证**：BBC/HN/金十/CNBC 全部提升

## R2: 正文提取 — regex vs 专业库

**输入**：24 个 adapter 都是 regex 删几行，信噪比仍低
**约束**：正文提取是已解决问题
**候选**：A) trafilatura B) readability-lxml C) 继续 regex
**分析**：trafilatura F-Score 0.914 > readability 0.801 >> regex ~0.5
**结论**：trafilatura 作为提取层，质量评分择优
**验证**：BBC raw 3.6K → fit 2.8K 纯正文

## R3: 存储方案

**输入**：抓完 stdout 输出，用完即弃
**约束**：需要去重/缓存/历史查询，免部署
**候选**：A) SQLite B) PostgreSQL C) 文件系统 D) SQLite+文件双写
**分析**：SQLite 免部署 + 文件人类可读 + Agent 可 read
**排除**：B（太重）C（查询慢）
**结论**：D — SQLite 存元数据 + pages/ 存 markdown
**验证**：content_hash 去重正常，按域名/时间查询 < 10ms

## R4: MCP Server 入口

**输入**：Agent 无法调用 Spider
**约束**：需要 stdio 模式（最简单），复用引擎
**候选**：A) MCP 独立实现管道 B) MCP 调 main.crawl()
**分析**：A 导致两套代码漂移（L9 教训）；B 单一真相源
**结论**：B — MCP 调 main.crawl()
**验证**：CLI 和 MCP 输出一致
