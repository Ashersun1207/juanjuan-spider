# 升级链 — 系统能力跃升记录

---

## E1: v0.1 — 手写 Playwright 引擎（2026-02-25）
- Playwright + stealth + 手写 markdown 转换
- 基本能抓，但很多站点效果差
- 单文件 scrape.py

## E2: v0.2 — Readability 提取（2026-02-25）
- 引入 readability-lxml
- 内容质量提升，自动去广告/导航
- 但复杂站点仍然噪音多

## E3: v0.3 — Crawl4AI 替代自写引擎（2026-02-26）
- 底层切换到 Crawl4AI（58K⭐）
- HN 从空→有内容，金十从标题→14K chars
- 质的飞跃

## E4: v0.4 — 包结构 + 双引擎 + 适配器 + 存储（2026-02-26）
- 5 层架构（core/engines/adapters/storage/infra）
- 双引擎路由（Crawl4AI + HTTP）
- SQLite + 文件双写
- MCP Server 4 tools
- 59 tests
- 从"脚本"变成"工具"

## E5: v0.5 — trafilatura 提取层（2026-02-26）
- 集成 trafilatura（F-Score 0.914）
- 引擎级去噪 + 适配器精调 + trafilatura 深度提取
- 三层去噪管道完成
- 从"能抓"到"抓得干净"
