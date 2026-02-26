# 开源爬虫项目深度调研报告

> 调研日期：2026-02-26  
> 调研对象：Crawl4AI、Firecrawl、Crawlee、MediaCrawler  
> 数据来源：GitHub API、Serper 搜索、HackerNews、Reddit、技术博客

---

## 目录

1. [Crawl4AI](#1-crawl4ai)
2. [Firecrawl](#2-firecrawl)
3. [Crawlee](#3-crawlee)
4. [MediaCrawler](#4-mediacrawler)
5. [综合对比表](#5-综合对比表)
6. [借鉴建议与排序](#6-借鉴建议与排序)

---

## 1. Crawl4AI

**GitHub**: github.com/unclecode/crawl4ai

### 一句话结论

> ✅ **推荐借鉴**——社区最活跃的 AI 友好型爬虫，完全开源免费，适合作为 Python 爬虫核心能力参考，但要注意 commit 频率近期下降。

---

### A. GitHub 真实活跃度

| 指标 | 数据 |
|------|------|
| ⭐ Stars | **61,010** |
| 创建时间 | 2024-05-09（约 21 个月） |
| Stars 增速评估 | 正常有机增长，无短期暴涨异常 |
| 最新 Release | v0.8.0（2026-01-16） |
| 最近 3 个月 Commits | **仅 9 次**（⚠️ 明显偏低） |
| Contributor 数量 | 54 人 |
| Open Issues | 179 |
| Closed Issues | 749（关闭率 ~81%） |
| Open PRs | 73 |
| Merged PRs | 163（合并率 ~38%） |
| 代码规模 | 约 148MB，Python 为主（99%） |
| CI/工作流数量 | 7 个 GitHub Actions workflows |
| 测试目录数量 | 23 个 test 目录（48 个测试文件） |

**Star 增长评估**：从 2024-05 创建至今 61K stars，速度极快但为 AI 爆发期正常现象，无明显刷星特征（早期 star 时间戳分布自然）。

**⚠️ 活跃度警告**：近 3 个月只有 9 次 commit，明显偏少。查看 release 历史：v0.7.5→v0.7.6→v0.7.7→v0.7.8（2025-10~12）→v0.8.0（2026-01），发布节奏放缓，核心维护力度存疑。

---

### B. 社区评价摘要

**正面评价：**
- "Crawl4AI is an amazing open-source library that solves many LLM-scraping headaches"（HN）
- 被大量 AI 项目引用为首选 Python 爬虫库
- 文档完整，有专属 Discord，社区活跃
- "它是适合 RAG 系统的高质量数据来源"

**负面评价：**
- Reddit r/webscraping："has anyone gotten crawl4ai to actually work? For me it hasn't worked beyond anything super easy to do"
- HN 讨论中有人指出："Tools like crawl4ai make it simple to obtain paywalled content including ebooks, forums"（伦理争议）
- API 变更频繁：v0.7 → v0.8 有 breaking change，旧文档失效
- Dynamic content 处理存在 bug（GitHub issue #1165）
- 部分用户反映配置复杂，学习曲线陡

**Scrapeless 对比评测结论（第三方）**：
- 擅长自适应爬取和域名特定模式识别，控制精度高
- 对重度 JS 渲染网站能力不如 Firecrawl

---

### C. 技术质量

| 维度 | 评估 |
|------|------|
| 文档完整度 | ✅ 优秀，有专属文档站 docs.crawl4ai.com |
| 测试覆盖 | ✅ 23 个测试目录，7 个 CI workflows |
| 依赖健康度 | ⚠️ 依赖 Playwright，Playwright 版本变化频繁 |
| API 稳定性 | ⚠️ v0→v0.8 期间有多次 breaking change |
| 架构清晰度 | ✅ 模块化设计，CrawlerRunConfig 等配置对象清晰 |

**技术亮点**：
- 自适应爬取（Adaptive Crawling）：智能判断何时停止，而非盲目爬完 N 页
- 支持 CSS 选择器 / XPath / Regex / LLM 解析混用
- 支持 Virtual Scroll（无限滚动）
- 支持 PDF 解析
- 异步架构（async-first）

---

### D. 商业模式风险

| 指标 | 情况 |
|------|------|
| License | **Apache-2.0** ✅（无传染性，商用友好） |
| 开源版阉割 | 无，完全开源 |
| 融资情况 | 目前无 VC 融资，靠 GitHub Sponsors 维持 |
| 商业风险 | 低，但单人/小团队维护风险存在 |

**注意**：GitHub 页面出现 "Sponsorship Program Now Open for startups and enterprises"，表明开始探索商业化。目前仍完全免费，但关注未来走向。

---

### E. 适合借鉴的具体能力

1. **自适应爬取策略**：基于信息量判断停止时机，而非固定页数
2. **LLM-ready Markdown 输出**：清洁 HTML→Markdown 转换管道
3. **多策略提取器**：CSS/XPath/Regex/LLM 可混合使用的提取架构
4. **Virtual Scroll 处理**：无限滚动页面的自动化处理
5. **异步 Playwright 封装**：`CrawlerRunConfig` 配置对象设计模式

---

## 2. Firecrawl

**GitHub**: github.com/mendableai/firecrawl

### 一句话结论

> ⚠️ **谨慎使用**——API 能力强大，托管版简单好用，但 AGPL 许可证有传染风险，自托管版功能严重阉割，VC 融资后商业化压力明显。

---

### A. GitHub 真实活跃度

| 指标 | 数据 |
|------|------|
| ⭐ Stars | **85,788**（4 个中最多） |
| 创建时间 | 2024-04-15（约 22 个月） |
| Stars 增速评估 | 异常快，但配合 $14.5M 融资公关有合理解释 |
| 最新 Release | v2.8.0（2026-02-03） |
| 最近 3 个月 Commits | **391 次**（最活跃） |
| Contributor 数量 | **131 人**（最多） |
| Open Issues | 约 42（issues only，排除 PRs） |
| Closed Issues | 样本估算 600+ |
| Open PRs | **151** |
| Closed PRs | **1,860** |
| 代码规模 | 83MB，TypeScript 70% + Python 19% + Rust 7% |
| CI/工作流数量 | **22 个**（最多，工程化程度最高） |
| 测试目录数量 | 20+ 个 `__tests__` 目录，含 e2e/unit 测试 |

**Star 增长评估**：85K stars 背后有 YC S22 + $14.5M Series A 公关加持，HN 多次上首页，属于媒体驱动增长，非刷星。

---

### B. 社区评价摘要

**正面评价：**
- "简单好用，一个 API 调用搞定整站抓取"
- "markdown 输出质量最高，token 节省 67%"
- Zapier、Replit、Lovable 等主流公司在用
- 官方 SDK 质量高（Python + Node.js + Go + Rust + C#）

**负面评价：**
- Reddit r/AI_Agents："Firecrawl sucks for extraction at scale — markdown chunks from Firecrawl lead to really poor retrieval in RAG"
- Reddit r/LocalLLaMA："Firecrawl is so pathetic they say they are open source but their self hosted version is so shit and it seems like it's forcibly made to be [broken]"
- Reddit r/LocalLLaMA（2025）："Firecrawl stopped being useful — Self-Host seems broken on the MCP and the engine does not support 'desktop browser' crawl anymore"
- HN 评论："Firecrawl is a highly dubious company. Their job ads for bot 'agents' seemed like a try to get free labour"
- HN："Firecrawl explicitly blocks Reddit. Yet one of your examples mentions checking Reddit"（功能名不副实）
- eesel.ai 独立评测："credit-based pricing makes it easy to burn through credits very quickly on large-scale crawls"
- self-hosted 版本缺少 Fire-engine（防检测核心引擎），实际反爬能力大打折扣

---

### C. 技术质量

| 维度 | 评估 |
|------|------|
| 文档完整度 | ✅ 优秀，docs.firecrawl.dev 详细 |
| 测试覆盖 | ✅ 最完整，e2e + unit + integration |
| 依赖健康度 | ✅ TypeScript 生态，依赖较新 |
| API 稳定性 | ⚠️ v0→v1→v2 有 breaking change，但有迁移指南 |
| 工程化程度 | ✅ 最高，22 个 CI workflows |

**技术亮点**：
- `/extract` 端点：自然语言描述 schema，AI 自动提取结构化数据
- FIRE-1 导航 Agent：能自动点击、填表、解验证码
- 全站 Markdown 化（LLMs.txt 格式）
- 批量 URL 处理（一次提交数千 URLs）
- 自动判断"需要浏览器 vs HTTP 直接请求"节省资源

---

### D. 商业模式风险

| 指标 | 情况 |
|------|------|
| License | **AGPL-3.0** ⚠️（有传染性！） |
| 融资情况 | YC S22 + **$14.5M Series A**（2025-08，Nexus Venture Partners） |
| 总融资 | $16.2M |
| 投资人 | Shopify CEO Tobi Lütke 也投了 |
| 开源版阉割 | **严重！** 自托管版缺少 Fire-engine（防检测核心），功能约为云版 30% |
| 商业化压力 | 高，VC 融资后需要变现 |

**AGPL 风险详解**：
- 如果你的商业产品集成了 AGPL 代码并对外提供服务，**必须开源你的整个服务代码**
- 需要商业授权才能闭源使用（需向 Mendable 公司付费）
- GitHub issue #1964："Can firecrawl be self-hosted as an internal crawler without violating AGPL?"——社区争议明显

---

### E. 适合借鉴的具体能力

1. **自然语言 Schema 提取**：`/extract` 端点的设计思路，用 AI 替代脆弱的 CSS 选择器
2. **智能路由**：自动判断页面是否需要浏览器渲染
3. **LLMs.txt 格式**：整站内容压缩成单文件的思路
4. **批量任务架构**：提交 → 返回 job_id → 异步轮询的设计模式
5. **多格式输出**：markdown/html/json/screenshot 统一接口

---

## 3. Crawlee

**GitHub**: github.com/apify/crawlee

### 一句话结论

> ✅ **强烈推荐参考**——最成熟稳定的爬虫框架，10 年积累，Apache-2.0 许可，工程质量最高，完全开源，公司 bootstrapped 无 VC 激进变现压力。

---

### A. GitHub 真实活跃度

| 指标 | 数据 |
|------|------|
| ⭐ Stars | **21,876** |
| 创建时间 | 2016-08-26（**10 年历史**） |
| Stars 增速评估 | 有机稳定增长，无异常 |
| 最新 Release | v3.16.0（2026-02-06） |
| 最近 3 个月 Commits | **69 次**（稳定） |
| Contributor 数量 | **110 人** |
| Open Issues | 138 |
| Closed Issues | 944（关闭率 **87%**，最高） |
| Open PRs | 43 |
| Closed/Merged PRs | **1,518/1,983**（合并率 **77%**，最高） |
| 代码规模 | 157MB，TypeScript 59% + MDX 文档 31% |
| CI/工作流数量 | 12 个 GitHub Actions workflows |
| 测试目录数量 | **181 个**（压倒性最多） |

**Star 增长评估**：10 年时间积累 21K stars，远低于 Crawl4AI/Firecrawl，但**质量远超**。真实用户驱动，无媒体炒作。

**⭐ 活跃度最可靠**：issues 关闭率 87%、PR 合并率 77% 是 4 个项目中最高的，说明维护团队响应快、质量管控严。

---

### B. 社区评价摘要

**正面评价：**
- Reddit r/webscraping："My production go-to is Crawlee (open-source from Apify). It unifies HTTP scraping (efficient like Scrapy) and browser automation (Playwright) in one framework"
- "removes a lot of the complexity of writing your own crawler, handles retries, concurrency, storage automatically"
- "最接近生产级别的开源爬虫，Scrapy 的 JS 版"
- 文档质量极高，有完整的示例库

**负面评价：**
- 主要语言是 TypeScript/JavaScript，Python 用户需要用 crawlee-python（独立项目）
- Apify 平台强绑定设计——默认存储 / 代理配置都往 Apify Cloud 倾斜
- LinkedIn 案例：Crawlee 有域名跳转过滤 bug（reddit.com → www.reddit.com 被误判为不同域名）
- 调度器较重，轻量任务比 requests/httpx 复杂很多

**HN/Reddit 综合**：负面很少，主要是"对 Python 用户不够友好"，JS/TS 栈用户评价极高。

---

### C. 技术质量

| 维度 | 评估 |
|------|------|
| 文档完整度 | ✅ 顶级，有专属文档站 crawlee.dev |
| 测试覆盖 | ✅ **181 个测试目录**，覆盖最全 |
| 依赖健康度 | ✅ 支持 Puppeteer/Playwright/Cheerio/JSDOM，依赖主流稳定 |
| API 稳定性 | ✅ v3.x 长期稳定，semantic versioning 严格遵守 |
| 工程化程度 | ✅ Monorepo 结构，分包管理清晰 |

**技术亮点**：
- **统一接口**：Cheerio（轻量）/ JSDOM / Playwright / Puppeteer 无缝切换
- **内置存储层**：键值存储、数据集存储、请求队列（可换后端）
- **智能代理轮换**：内置代理池管理，带 session 粘性
- **请求调度器**：并发控制、重试、去重、优先级
- **Headful + Headless**：两种模式统一 API
- **Session 管理**：登录态持久化

---

### D. 商业模式风险

| 指标 | 情况 |
|------|------|
| License | **Apache-2.0** ✅（无传染性） |
| 融资情况 | **Bootstrapped（自筹资金）**，无 VC |
| 公司营收 | Apify 2024 年营收 $13.3M，盈利 |
| 开源版阉割 | **轻微**：默认存储推 Apify Cloud，但完全可替换 |
| 商业化风险 | 低，公司盈利且无 VC 追投回报压力 |

**Apify 商业模式**：开源 Crawlee 作为引流，Apify Cloud（Actor 平台）收费。这种模式健康——开源版功能完整，不强制用云。

---

### E. 适合借鉴的具体能力

1. **统一爬虫接口架构**：不同 backend（HTTP/Playwright/Puppeteer）统一 API 设计
2. **请求队列管理**：去重、重试、优先级、持久化的完整队列实现
3. **Session 池**：多账号/多 Cookie 的 session 池管理
4. **代理轮换中间件**：带 session 粘性的智能代理管理
5. **存储抽象层**：键值存储/数据集存储解耦设计（可替换 local/cloud）
6. **并发调度器**：Autopilot 自动调整并发数

---

## 4. MediaCrawler

**GitHub**: github.com/NanmiCoder/MediaCrawler

### 一句话结论

> ⚠️ **谨慎使用，不推荐商用**——专注中国社交平台爬取，技术思路可参考，但许可证禁止商用，法律风险高，核心作者维护压力大，随时有被平台封杀风险。

---

### A. GitHub 真实活跃度

| 指标 | 数据 |
|------|------|
| ⭐ Stars | **44,305** |
| 创建时间 | 2023-06-09（约 32 个月） |
| Stars 增速评估 | 中国社区正常增长，无刷星异常 |
| 最新 Release | **无 release tag**（⚠️ 从未发版） |
| 最近 3 个月 Commits | **80 次**（较活跃） |
| Contributor 数量 | 61 人（含主要贡献者约 5-10 人） |
| Open Issues | 131 |
| Closed Issues | 435（关闭率 **77%**） |
| Open PRs | 2 |
| Closed PRs | 212（合并率 ~61%） |
| 代码规模 | 28MB（最小），Python 100% |
| CI/工作流数量 | **1 个**（⚠️ 最少） |
| 测试目录数量 | 3 个（⚠️ 基本没有测试） |

**Star 增长评估**：44K stars 但从未发过正式 release，说明用户主要是拉代码直接跑，项目定位更像"学习参考"而非"工程库"。

---

### B. 社区评价摘要

**正面评价：**
- "无需逆向加密算法，门槛低，利用 Playwright 保留登录态"
- "覆盖平台最全：小红书/抖音/快手/B站/微博/贴吧/知乎"
- CSDN/掘金 上大量实战教程，中文社区友好
- "适合做舆情监控、竞品分析的数据采集"

**负面评价：**
- 许可证明确写"**仅限非商业学习用途**"，商用违法
- 2025-01 腾讯向 GitHub 发 DMCA 投诉类似项目（同类工具被下架风险）
- 小红书/抖音等平台频繁更新反爬机制，代码可能随时失效
- "实测 1000 条零封号"——但需要精心维护 Cookie 和滑块验证
- 没有正式 release，稳定性靠用户自己判断
- 单个核心作者（NanmiCoder）主导，团队单薄

---

### C. 技术质量

| 维度 | 评估 |
|------|------|
| 文档完整度 | ⚠️ 仅 README，无专属文档站 |
| 测试覆盖 | ❌ 基本没有测试（3 个目录，内容极少） |
| 依赖健康度 | ⚠️ 依赖 Playwright + 各平台私有 API，极易因平台更新失效 |
| API 稳定性 | ❌ 无版本管理，随时 breaking |
| 架构清晰度 | ✅ 代码结构清晰，可读性高 |

**技术原理**：
- 利用 Playwright 保持登录态浏览器环境
- 通过执行 JS 表达式获取平台加密参数（绕过签名验证）
- 支持 IP 代理池 + Cookie 池
- 支持数据存储到 MySQL/CSV

---

### D. 商业模式风险

| 指标 | 情况 |
|------|------|
| License | **NON-COMMERCIAL LEARNING LICENSE 1.1**（自定义许可证）❌ |
| 商用情况 | **明确禁止**商业用途 |
| 融资情况 | 个人项目，无融资 |
| 法律风险 | 高：①违反平台 ToS ②DMCA 下架风险 ③国内数据法规风险 |
| 平台封杀风险 | 极高，各平台持续对抗 |

**License 全文关键条款**：
> "The Software is limited to learning and research purposes only, and may not be used for large-scale crawling or activities that disrupt platform operations."
> "Without the written consent of the copyright owner, the Software may not be used for any commercial purposes."

---

### E. 适合借鉴的具体能力

1. **Playwright 登录态持久化**：保存 browser context，复用登录 session 的思路
2. **JS 表达式注入获取加密参数**：无需逆向算法，直接从浏览器上下文取值
3. **多平台适配架构**：各平台一个 crawler 类，统一接口不同实现
4. **IP + Cookie 双池管理**：结合 IP 轮换和多账号 Cookie 的反封策略
5. **异步 + 协程架构**：asyncio 驱动的高效并发爬取模式

---

## 5. 综合对比表

| 维度 | Crawl4AI | Firecrawl | Crawlee | MediaCrawler |
|------|----------|-----------|---------|--------------|
| **Stars** | 61K | **85K** | 21K | 44K |
| **历史年限** | 1.8年 | 1.8年 | **10年** | 2.6年 |
| **License** | Apache-2.0 ✅ | AGPL-3.0 ⚠️ | Apache-2.0 ✅ | 禁商用 ❌ |
| **近3月Commits** | 9 ⚠️ | **391** ✅ | 69 ✅ | 80 ✅ |
| **Contributors** | 54 | **131** | 110 | 61 |
| **Issue关闭率** | 81% | ~75% | **87%** ✅ | 77% |
| **PR合并率** | 38% ⚠️ | 46% | **77%** ✅ | 61% |
| **测试目录数** | 23 | 20+ | **181** ✅ | 3 ❌ |
| **CI workflows** | 7 | **22** | 12 | 1 ❌ |
| **有正式release** | ✅ | ✅ | ✅ | ❌ |
| **主语言** | Python | TypeScript | TypeScript | Python |
| **VC融资** | 无 ✅ | $16.2M ⚠️ | 无 ✅ | 无 ✅ |
| **自托管完整性** | ✅ 完整 | ⚠️ 阉割版 | ✅ 完整 | N/A |
| **商业可用** | ✅ | ⚠️ 需审慎 | ✅ | ❌ |
| **LLM友好输出** | ✅ 原生支持 | ✅ 最佳 | ⚠️ 需自配 | ❌ 不适用 |
| **中国平台支持** | ❌ | ❌ | ❌ | ✅ 专精 |
| **文档质量** | ✅ 好 | ✅ 最好 | ✅ 最好 | ⚠️ 仅README |
| **综合工程质量** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |

---

## 6. 借鉴建议与排序

### 🥇 第一名：Crawlee（强烈推荐借鉴架构）

**理由**：
- 10 年工程积累，是 4 个项目中最经得起推敲的
- Apache-2.0，商用无顾虑
- PR 合并率 77%、Issue 关闭率 87% 说明维护团队专业
- 181 个测试目录，工程质量远超其他
- Bootstrapped 公司盈利，无变现焦虑

**juanjuan-spider 可借鉴**：
- 请求队列的去重+重试+优先级架构
- 统一的 crawler 抽象层（HTTP/Browser 无缝切换）
- Session 池和代理池的管理模式
- 存储抽象层（本地/云可插拔）

---

### 🥈 第二名：Crawl4AI（推荐借鉴AI提取能力）

**理由**：
- 最接近我们自己需求（Python + LLM-friendly 输出）
- Apache-2.0，可直接使用代码
- 自适应爬取策略是创新亮点

**juanjuan-spider 可借鉴**：
- Adaptive Crawling 的停止策略设计
- LLM-ready Markdown 转换管道
- 多策略提取器（CSS/XPath/LLM 混用）架构

**注意**：近 3 个月仅 9 次 commit，PR 合并率只有 38%，需持续关注是否进入维护停滞。

---

### 🥉 第三名：Firecrawl（选择性参考，绝不直接使用）

**理由**：
- AGPL-3.0 有传染风险，商用前必须法律审查
- 自托管版严重阉割，核心防检测引擎不开源
- VC 驱动可能激进变现

**juanjuan-spider 可借鉴（仅思路，不用代码）**：
- `/extract` 端点的自然语言 schema 设计理念
- 智能路由（HTTP vs Browser）的判断逻辑
- 批量任务 + 异步轮询的 API 设计模式

---

### 第四名：MediaCrawler（仅学习，绝不商用）

**理由**：
- 许可证明确禁止商业使用
- 法律风险：违反平台 ToS + 数据安全法规
- 测试极少，无正式 release，稳定性差

**juanjuan-spider 可借鉴（仅思路）**：
- Playwright 登录态持久化的具体实现方式
- 多账号 Cookie 池管理的代码模式（仅参考，需重写）

---

### 最终建议

对于 juanjuan-spider 项目：

1. **架构参考**：主要看 Crawlee，学习其请求调度、Session 管理、存储抽象
2. **AI提取**：主要看 Crawl4AI，学习其 LLM-ready 输出管道和自适应停止策略
3. **中国平台**：MediaCrawler 的 Playwright 登录态保持方案可参考，但代码需从零重写
4. **Firecrawl**：作为竞品了解即可，代码不要直接集成（AGPL 风险）

> **核心原则**：借鉴架构和设计思路，代码自己实现，使用 Apache-2.0 或 MIT 依赖。

---

*报告生成时间：2026-02-26 | 数据来自 GitHub API v3 + Serper Search*
