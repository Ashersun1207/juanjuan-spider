# 需求链 — 需求→实现追踪

---

## REQ1: "通用爬虫，不只金融"
**来源**：定位讨论
**转化**：架构不针对特定领域，适配器可插拔
**实现**：v0.4 完成，16 个适配器覆盖新闻/技术/金融/论坛

## REQ2: "不造轮子"
**来源**：核心原则
**转化**：集成 Crawl4AI（58K⭐）+ trafilatura（学术冠军）
**实现**：v0.3 + v0.5 完成

## REQ3: Agent 可调用
**来源**：Spider 只能 CLI 用
**转化**：MCP Server 4 tools（scrape/batch/query/screenshot）
**实现**：v0.4 完成，stdio 模式

## REQ4: 历史可查、去重
**来源**：抓完即弃不可接受
**转化**：SQLite + 文件双写 + content_hash 去重
**实现**：v0.4 完成
