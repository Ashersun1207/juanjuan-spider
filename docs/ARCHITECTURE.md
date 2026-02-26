# web-scraper — 架构文档

_卷卷的通用网页抓取工具，能力覆盖所有需要浏览器渲染的场景。_

---

## 定位

通用爬虫工具，核心能力：反检测 + 智能正文提取 + 多格式输出。
适用场景不限于金融——新闻、研报、论坛、产品页、文档站、任何需要绕反爬的网页。

## 技术栈

| 层 | 技术 | 说明 |
|---|---|---|
| 浏览器引擎 | Playwright (Chromium) | 支持 JS 渲染、SPA |
| 反检测 | playwright-stealth 2.x | 指纹伪装、webdriver 隐藏 |
| 正文提取 | readability-lxml (Mozilla Readability) | 去导航/广告/脚本，提取正文 |
| HTML→Markdown | markdownify | 结构化输出 |
| 语言 | Python 3.x | Playwright Python 生态更成熟 |

## 架构概览

```
URL → Playwright (Stealth) → 原始 HTML
                                ↓
                    Readability 正文提取（可 --raw 跳过）
                                ↓
                    格式化（markdown / text / html / screenshot）
                                ↓
                    clean_markdown（过滤 CSS/JS 残留）
                                ↓
                    截断（--max-chars）→ 输出
```

## 核心流程

1. **启动浏览器**：Chromium headless，可选代理（默认 Clash 7897）
2. **反检测注入**：Stealth.apply_stealth_sync() — 在每个 page 上注入
3. **导航**：networkidle 优先，超时降级 domcontentloaded
4. **可选操作**：等待（--wait）、滚动（--scroll）、执行 JS（--js）、Cookie 注入
5. **内容获取**：--selector 指定元素 或 全页 page.content()
6. **正文提取**：Readability 算法去噪（除非 --raw / --selector）
7. **格式化**：markdown / text（strip img）/ html / screenshot
8. **后处理**：clean_markdown 过滤残留 + max-chars 截断

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

1. 单进程单页，无并发队列
2. 无登录态管理（仅 cookie 文件导入）
3. Cloudflare Turnstile / hCaptcha 无法自动绕过
4. 重度 SPA（无 SSR）数据可能不完整
5. clean_markdown 启发式规则，偶有误判

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
