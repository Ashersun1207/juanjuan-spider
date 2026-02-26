# web-scraper — 项目状态

---

## 版本

**v0.2** (2026-02-26)

## 完成

| 功能 | 版本 | 日期 |
|---|---|---|
| Playwright + Stealth 基础抓取 | v0.1 | 2026-02-25 |
| Readability 正文提取 | v0.2 | 2026-02-25 |
| clean_markdown 后处理 | v0.2 | 2026-02-25 |
| --max-chars / --timeout 参数 | v0.2 | 2026-02-25 |
| --scroll 自动滚动 | v0.1 | 2026-02-25 |
| --cookie / --js 支持 | v0.1 | 2026-02-25 |
| --selector CSS 选择器 | v0.1 | 2026-02-25 |
| --headed 调试模式 | v0.1 | 2026-02-25 |

## 进行中

_无_

## 待做

### P1 — 近期
- [ ] MCP Server 封装（Python MCP SDK）
- [ ] 金融站点适配器（Myfxbook 表格 → JSON）
- [ ] Cloudflare challenge 检测 + 自动重试
- [ ] 批量 URL 输入（--urls file.txt）

### P2 — 按需
- [ ] 登录态管理（浏览器 profile 保存/复用）
- [ ] 代理轮换
- [ ] 表格专用提取（--extract-tables → CSV/JSON）
- [ ] 并发抓取（asyncio + 连接池）

### P3 — 远期
- [ ] OpenClaw Skill 封装
- [ ] 页面变更监控（定期 diff）
- [ ] 集成到 gainlab-mcp 作为 tool

## 已验证站点

| 站点 | 状态 | 备注 |
|---|---|---|
| Myfxbook | ✅ | 核心数据可抓 |
| MQL5 | ❌ | 代理出口 SSL 被封，非工具问题 |

## 依赖版本

| 包 | 版本 |
|---|---|
| playwright | 1.58.0 |
| playwright-stealth | 2.0.2 |
| readability-lxml | 0.8.4.1 |
| markdownify | 1.2.2 |
| chromium (playwright) | 145.0.7632.6 |

---

_Last updated: 2026-02-26_
