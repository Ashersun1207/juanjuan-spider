# 开源爬虫项目调研 — juanjuan-spider 能力借鉴

_调研目的：不造轮子，找成熟项目中值得借鉴的能力，集成到 juanjuan-spider。_
_调研日期：2026-02-26_

---

## 调研项目

| 项目 | ⭐ | 语言 | 定位 |
|---|---|---|---|
| **Crawl4AI** | 58K+ | Python | LLM-ready 通用爬虫，异步，智能 markdown |
| **Firecrawl** | 70K+ | TS/Python SDK | 全站爬取 → markdown，SaaS + 开源 |
| **Crawlee** | 20K+ | Node.js/Python | 反封锁，生产级爬虫框架 |
| **MediaCrawler** | 25K+ | Python | **中文社交平台**（小红书/抖音/B站/微博/知乎/快手/贴吧） |

---

## 逐项拆解

### 1. Crawl4AI（58K⭐）

**核心能力：**
| 能力 | 说明 | 借鉴价值 |
|---|---|---|
| fit_markdown | 启发式过滤噪音，只留正文 | ⭐⭐⭐ 我们 Readability 不如它 |
| 异步引擎 | AsyncWebCrawler，并发高效 | ⭐⭐⭐ 我们是同步单页 |
| enable_stealth + patchright | 双层反检测 | ⭐⭐⭐ 比单独 playwright-stealth 强 |
| 深度爬取 | BFS/DFS 递归发现子页面 | ⭐⭐ 暂不急需 |
| LLM 结构化提取 | 传 schema，LLM 自动解析 | ⭐⭐ 有用但可后做 |
| 缓存系统 | aiosqlite 本地缓存 | ⭐ 锦上添花 |
| crash recovery | 长爬取断点恢复 | ⭐ 大规模才需要 |

**结论：fit_markdown + 异步 + 反检测 三件套值得直接用。**

### 2. Firecrawl（70K⭐）

**核心能力：**
| 能力 | 说明 | 借鉴价值 |
|---|---|---|
| only_main_content | 自动提取正文 | ⭐⭐ Crawl4AI 的 fit 已覆盖 |
| include/exclude paths | URL 过滤规则 | ⭐⭐ 深度爬取时有用 |
| map endpoint | 快速发现站点所有 URL | ⭐⭐ 有意思但不急 |
| 自然语言 crawl prompts | 描述需求自动配置爬取 | ⭐ 花哨，实际不如手动精确 |
| 多格式输出 | markdown + links + screenshot | ⭐ 我们已有 |
| token 效率 | markdown 比 HTML 省 67% token | ✅ 已知 |

**结论：主要是 SaaS 模式的产品打磨，技术上 Crawl4AI 已覆盖大部分。URL 过滤规则可以借鉴。**

### 3. Crawlee（20K⭐）

**核心能力：**
| 能力 | 说明 | 借鉴价值 |
|---|---|---|
| 自动反封锁 | 指纹轮换 + 请求频率控制 + 重试策略 | ⭐⭐⭐ 生产级反封锁 |
| 代理轮换 | 内置代理管理器 | ⭐⭐ 我们只有单代理 |
| 请求队列 | 持久化队列，支持优先级 | ⭐⭐ 批量爬取需要 |
| 自动扩展 | 根据系统资源动态调并发 | ⭐ 过度设计 |
| HTTP + 浏览器混合 | 简单页面用 HTTP，复杂的用浏览器 | ⭐⭐ 省资源好思路 |

**结论：反封锁策略（指纹轮换+频率控制+重试）是核心价值。但 Crawlee 是 Node.js 为主，Python 版较新。**

### 4. MediaCrawler（25K⭐）

**核心能力：**
| 能力 | 说明 | 借鉴价值 |
|---|---|---|
| 7 大中文平台 | 小红书/抖音/快手/B站/微博/贴吧/知乎 | ⭐⭐⭐ **我们完全没有** |
| 登录态保存 | Playwright 保存登录 context | ⭐⭐⭐ 解决我们的 Reddit 等需登录站点 |
| JS 签名获取 | 利用登录态浏览器上下文拿签名参数 | ⭐⭐⭐ 绕加密不用逆向 |
| 关键词搜索 | 按关键词搜索平台内容 | ⭐⭐⭐ 我们没有平台内搜索能力 |
| 指定帖子/创作者 | 精确抓取指定内容 | ⭐⭐⭐ |
| 评论爬取 | 二级评论、评论词云 | ⭐⭐ |
| IP 代理池 | 多代理自动轮换 | ⭐⭐ |
| 多存储方式 | CSV/JSON/Excel/SQLite/MySQL | ⭐⭐ |
| WebUI | 可视化操作界面 | ⭐ 锦上添花 |

**结论：中文社交平台能力是我们的空白区。登录态管理 + JS 签名思路非常值得借鉴。**

---

## 能力矩阵 — juanjuan-spider 现状 vs 可借鉴

| 能力维度 | juanjuan-spider 现状 | 借鉴来源 | 优先级 |
|---|---|---|---|
| **英文通用网页** | ✅ 基本可用 | Crawl4AI | — |
| **智能去噪 markdown** | ❌ Readability 不够好 | Crawl4AI fit_markdown | P0 |
| **异步/并发** | ❌ 同步单页 | Crawl4AI async | P0 |
| **反检测** | ⚠️ playwright-stealth 单层 | Crawl4AI stealth+patchright | P0 |
| **中文社交平台** | ❌ 完全没有 | MediaCrawler | P1 |
| **登录态管理** | ❌ 只有 cookie 文件 | MediaCrawler | P1 |
| **JS 签名/反爬绕过** | ❌ | MediaCrawler | P1 |
| **平台内搜索** | ❌ | MediaCrawler | P1 |
| **代理轮换** | ❌ 单代理 | Crawlee / MediaCrawler | P2 |
| **指纹轮换** | ❌ 硬编码 UA | Crawlee | P2 |
| **深度爬取** | ❌ | Crawl4AI / Firecrawl | P2 |
| **LLM 结构化提取** | ❌ | Crawl4AI / ScrapeGraphAI | P2 |
| **批量队列** | ❌ | Crawlee | P2 |
| **URL 过滤规则** | ❌ | Firecrawl | P3 |
| **断点恢复** | ❌ | Crawl4AI | P3 |

---

## 集成方案建议

### 方案：双引擎架构

```
juanjuan-spider (scrape.py CLI)
    │
    ├── 英文/通用网页 → Crawl4AI（已集成）
    │     ├── fit_markdown
    │     ├── 异步引擎
    │     └── stealth + patchright
    │
    └── 中文社交平台 → MediaCrawler（待集成）
          ├── 小红书 / 抖音 / B站 / 微博 / 知乎 / 快手 / 贴吧
          ├── 登录态管理
          └── JS 签名获取
```

**不是把两个项目合并成一个**，而是：
- scrape.py 作为统一入口
- 根据目标 URL/平台自动路由到对应引擎
- 两个引擎独立维护、独立升级

### 实施优先级

| 阶段 | 内容 | 依赖 |
|---|---|---|
| **P0** | Crawl4AI 集成完善（已基本完成） | ✅ 已做 |
| **P1** | MediaCrawler 集成（中文平台能力） | 需安装 + 适配 |
| **P2** | 代理轮换 + 指纹轮换 | 借鉴 Crawlee 策略 |
| **P2** | LLM 结构化提取 | 借鉴 Crawl4AI 能力 |
| **P3** | 深度爬取 + 批量队列 | 按需 |

---

_Last updated: 2026-02-26_
