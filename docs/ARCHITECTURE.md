# juanjuan-spider — 架构文档

_卷卷的通用网页抓取工具，能力覆盖所有需要浏览器渲染的场景。_

---

## 定位

通用爬虫工具，核心能力：反检测 + 智能正文提取 + 多格式输出。
适用场景不限于金融——新闻、研报、论坛、产品页、文档站、任何需要绕反爬的网页。

## 技术栈

| 层 | 技术 | 说明 |
|---|---|---|
| 核心引擎 | **Crawl4AI 0.8.x** (58K+ ⭐) | 异步、LLM-ready、反检测、fit markdown |
| 浏览器 | Playwright (Chromium) via Crawl4AI | JS 渲染、SPA 支持 |
| 反检测 | Crawl4AI enable_stealth + patchright | 指纹轮换、UA 随机化 |
| 内容提取 | Crawl4AI markdown generator | raw markdown + fit markdown（智能去噪） |
| 封装层 | scrape.py（CLI 薄封装） | 保持简单 CLI 接口 |
| 语言 | Python 3.12+ | venv 隔离 |

## 架构概览

```
scrape.py (CLI 入口)
    ↓
Crawl4AI AsyncWebCrawler
    ├── BrowserConfig（代理/stealth/headed）
    └── CrawlerRunConfig（超时/选择器/JS/滚动）
          ↓
    Playwright Chromium（反检测注入）
          ↓
    页面渲染 → HTML → Markdown Generator
          ↓
    raw_markdown / fit_markdown / html / screenshot
          ↓
    截断（--max-chars）→ 输出
```

## 设计原则

**不造轮子，集成成熟项目，在上面优化。**

- Crawl4AI 做重活（浏览器管理、反检测、内容提取）
- scrape.py 做薄封装（CLI 接口 + 我们的默认值）
- 后续优化聚焦在：站点适配、输出质量、与其他工具集成

## 代理策略

- 默认走 `http://127.0.0.1:7897`（本机 Clash）
- `--no-proxy` 直连（国内站点 / 不需要代理时）
- 未来可扩展代理轮换

## 输出格式

| 格式 | 用途 |
|---|---|
| markdown（默认） | Agent 消费、人类阅读 |
| text | 纯文本，token 最省 |
| html | 需要二次解析时 |
| screenshot | 视觉验证、截图存档 |

## 已知限制

1. Cloudflare Turnstile / hCaptcha 无法自动绕过（Bloomberg / Investing.com）
2. Reddit 需登录态
3. 部分重度 SPA 可能需 --scroll + --wait 配合

## 演进方向

- **P1**：MCP Server 封装（Agent 原生调用）
- **P1**：站点适配器系统（针对特定站点优化提取逻辑）
- **P1**：Cloudflare challenge 检测 + 重试
- **P2**：批量 URL + 并发
- **P2**：登录态管理（浏览器 profile 复用）
- **P2**：表格专用提取（→ JSON/CSV）
- **P3**：OpenClaw Skill 封装
- **P3**：页面变更监控（定期 diff 告警）

---

_Last updated: 2026-02-26_
