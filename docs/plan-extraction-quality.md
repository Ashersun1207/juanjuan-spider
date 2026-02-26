# 内容提取质量优化方案

_v0.5 核心升级 — 从"能抓到"到"抓得好"_

---

## 问题诊断

### 现状数据（基于 storage/pages/ 实际文件）

| 网站 | 文件大小 | 信噪比 | 主要问题 |
|---|---|---|---|
| HN | 10KB | **低** | 表格残骸 `\| --- \|` 满屏，不可读 |
| BBC 首页 | 30KB | **低** | 导航 `[Home][News][Sport]...` 重复 2 遍、Advertisement 残留、Register/SignIn 未清 |
| Yahoo Finance | 48KB | **极低** | 90% 是重复标题链接+Taboola 广告+视频推荐 |
| Wikipedia | 486KB | 高 | 内容好但 `[edit]` `[123]` 标记残留 |
| arXiv | 小 | 高 | 纯文本，几乎无噪音 |
| The Verge | 50KB | 中低 | 大量列表链接、分类导航 |

### 根因分析

```
问题 1：adapter.transform() 把 fit_markdown 覆盖为清洗后的全文
          → Crawl4AI 自带的 Readability 提取结果被丢弃

问题 2：HTTP 引擎的 fit_markdown 始终为空
          → httpx + markdownify 没有正文提取能力，只做 HTML→MD 转换

问题 3：adapter 只做"删噪音"（regex 删几行），不做"提正文"
          → 列表页/首页的导航、侧边栏占比 60-80%，regex 删不完

问题 4：没有文章页 vs 列表页区分
          → 同一域名，文章页需要提取正文，列表页需要提取链接列表
```

### 数据管道现状

```
URL → Router → Engine(抓取原始HTML) → Adapter.transform(regex删噪) → 输出
                  │                          │
                  │ Crawl4AI: raw_markdown    │ fit_markdown 被覆盖
                  │          fit_markdown ←───┘ (浪费了)
                  │
                  │ HTTP:    raw_markdown(markdownify全文转换)
                  │          fit_markdown="" (空)
```

---

## 方案设计

### 目标

| 指标 | 现在 | 目标 |
|---|---|---|
| 文章页信噪比 | ~40% | >85% |
| 列表页可读性 | 不可读（表格/链接混乱） | 结构化标题+链接列表 |
| 无 adapter 站点的质量 | 等于 raw_markdown（全是噪音） | 自动提取正文 |
| 新站点适配成本 | 必须写 adapter | 多数情况不用写 |

### 核心思路：插入 Extractor 层

```
URL → Router → Engine(抓取) → Extractor(提取正文) → Adapter(精调) → 输出
                                  ↑ 新增
```

**不改现有架构**，在 Engine 和 Adapter 之间加一层 `Extractor`，专做正文提取。

### 新数据管道

```
URL → Router → Engine → ┬─ Crawl4AI fit_markdown ──┐
                         │                           ├→ Extractor 择优 → Adapter → 输出
                         └─ trafilatura(HTML) ───────┘
                         
                         HTTP → trafilatura(HTML) → Adapter → 输出
```

---

## Phase A：修现有 Bug（不加依赖）

**耗时：~30 分钟**

### A1. 停止覆盖 fit_markdown

**问题**：所有 adapter 的 `transform()` 都执行 `fit_markdown=md`，把 Crawl4AI 的 Readability 结果覆盖了。

**改法**：adapter 只清洗 `markdown`（raw），不碰 `fit_markdown`。

```python
# 之前（错误）
def transform(self, result: CrawlResult) -> CrawlResult:
    md = result.markdown
    md = re.sub(r"...", "", md)
    return result.model_copy(update={"markdown": md, "fit_markdown": md})  # ← 覆盖了

# 之后（正确）
def transform(self, result: CrawlResult) -> CrawlResult:
    md = result.markdown
    md = re.sub(r"...", "", md)
    return result.model_copy(update={"markdown": md})  # fit_markdown 保持引擎原值
```

**影响文件**：`news.py` `tech.py` `finance.py` `social.py`（所有 adapter）

### A2. 补全 Crawl4AI excluded_selector

**现状**：已有基础排除规则，补充常见噪音选择器。

```python
# crawl4ai_engine.py — 在现有基础上补充
"excluded_selector": ",".join([
    # 已有的...
    "[role='navigation']", "[role='banner']", "[role='contentinfo']",
    ".navbar", ".menu-bar", ".site-footer", ".cookie-banner",
    ".advertisement", "#cookie-consent", "#cookie-banner",
    "[class*='cookie']", "[id*='cookie']",
    # 新增
    ".sidebar", "[role='complementary']",        # 侧边栏
    ".social-share", ".share-buttons",           # 社交分享
    ".related-articles", ".recommended",         # 推荐文章
    ".newsletter-signup", ".subscribe-form",     # 订阅表单
    "[class*='popup']", "[class*='modal']",      # 弹窗
    "[class*='advert']", "[class*='sponsor']",   # 广告
    "figure figcaption",                         # 图片说明（可选）
]),
```

### A3. HN 适配器改用 API

```python
@dataclass
class HackerNewsAdapter(DefaultAdapter):
    name: str = "hackernews"
    domains: list[str] = field(default_factory=lambda: ["news.ycombinator.com"])
    use_api: bool = True  # 标记使用 API 而非页面抓取

    def transform(self, result: CrawlResult) -> CrawlResult:
        # 如果抓到的是 HTML 表格残骸，尝试用 API 数据替代
        md = result.markdown
        if "| --- |" in md or md.count("|") > 50:
            # 标记为需要 API 重抓
            return result.model_copy(update={
                "metadata": {**result.metadata, "hint": "HN 建议用 API: /v0/topstories.json"},
            })
        return result
```

> 完整 API 集成放 Phase B（需要在 engine 层加 API fetch 路径）。

---

## Phase B：集成 trafilatura 提取层

**耗时：~2-3 小时**

### 为什么选 trafilatura

| 维度 | trafilatura | readability-lxml | Crawl4AI fit_markdown |
|---|---|---|---|
| F-Score (750 文档基准) | **0.914** | 0.801 | 未知（非标准评测） |
| Precision | 0.925 | 0.891 | — |
| Recall | 0.904 | 0.729 | — |
| 学术引用 | ACL 2021 论文 | 无 | 无 |
| 用户 | HuggingFace / IBM / Microsoft Research | — | — |
| 输出格式 | TXT / MD / JSON / XML / CSV | HTML 片段 | markdown |
| 元数据提取 | ✅ 标题/作者/日期/分类 | ❌ | 部分 |
| 维护状态 | 活跃（2.0.0, 2024） | 低频 | 活跃 |
| 依赖 | lxml, courlan, htmldate | lxml | playwright |
| 速度 | 基准 1x（最快一档） | 5.8x | 取决于页面 |

**结论**：trafilatura 在精度、召回、速度三项全面领先，且自带元数据提取（标题/作者/日期），这些我们手写的 adapter 完全没做。

### 架构：新增 `spider/core/extractor.py`

```python
"""
内容提取器 — trafilatura 正文提取 + 质量评估。

位于 Engine 和 Adapter 之间，对所有引擎的输出做通用正文提取。
"""

from __future__ import annotations
from spider.core.result import CrawlResult

class ContentExtractor:
    """
    通用内容提取器。
    
    策略：
    1. 如果引擎已有高质量 fit_markdown → 保留
    2. 否则用 trafilatura 从 HTML 提取正文
    3. 提取元数据（标题/作者/日期）补充到 result.metadata
    """

    def extract(self, result: CrawlResult) -> CrawlResult:
        """对抓取结果做正文提取。"""
        
        # 如果没有 HTML，跳过（比如 API 直接返回的数据）
        if not result.html:
            return result
        
        # trafilatura 提取
        import trafilatura
        
        # Markdown 格式输出
        extracted_md = trafilatura.extract(
            result.html,
            output_format="markdown",
            include_links=True,
            include_tables=True,
            include_comments=False,
            favor_precision=True,  # 优先精度，减少噪音
        )
        
        # 元数据提取
        metadata = trafilatura.bare_extraction(
            result.html,
            only_with_metadata=False,
        )
        
        # 决策：用哪个作为 fit_markdown
        updates = {}
        
        if extracted_md:
            # 质量比较：trafilatura vs 引擎 fit_markdown
            engine_fit = result.fit_markdown
            traf_score = self._quality_score(extracted_md)
            engine_score = self._quality_score(engine_fit) if engine_fit else 0
            
            if traf_score >= engine_score:
                updates["fit_markdown"] = extracted_md
            # 否则保留引擎的 fit_markdown
        
        # 补充元数据
        if metadata and isinstance(metadata, dict):
            extra_meta = {}
            for key in ("author", "date", "sitename", "categories", "tags"):
                if metadata.get(key):
                    extra_meta[key] = metadata[key]
            if extra_meta:
                updates["metadata"] = {**result.metadata, **extra_meta}
            # 如果原 title 为空，用 trafilatura 提取的
            if not result.title and metadata.get("title"):
                updates["title"] = metadata["title"]
        
        if updates:
            return result.model_copy(update=updates)
        return result

    def _quality_score(self, text: str) -> float:
        """
        简单的内容质量评分。
        
        评估维度：
        - 文本长度（太短=提取失败）
        - 噪音比（链接密度、特殊字符密度）
        - 段落结构（有自然段落=正文）
        """
        if not text:
            return 0.0
        
        length = len(text)
        if length < 100:
            return 0.1
        
        # 链接密度：[text](url) 的占比
        import re
        links = re.findall(r'\[([^\]]*)\]\([^\)]+\)', text)
        link_chars = sum(len(l) for l in links)
        link_density = link_chars / length if length > 0 else 0
        
        # 段落结构：换行分段
        paragraphs = [p for p in text.split('\n\n') if len(p.strip()) > 50]
        para_score = min(len(paragraphs) / 3, 1.0)  # 3段以上满分
        
        # 综合评分
        score = (
            min(length / 2000, 1.0) * 0.3 +    # 长度分（2000字满分）
            (1 - link_density) * 0.4 +           # 链接密度越低越好
            para_score * 0.3                      # 段落结构分
        )
        
        return round(score, 3)
```

### 集成到 main.py

```python
# main.py — 在 adapter.transform 之前插入 extractor

from spider.core.extractor import ContentExtractor

async def crawl(url, ...):
    ...
    # 抓取
    result = await engine.fetch(url, fc)
    
    # >>> 新增：内容提取 <<<
    extractor = ContentExtractor()
    result = extractor.extract(result)
    
    # 适配器后处理（仍然可以做站点特有的精调）
    result = adapter.transform(result)
    
    # 存储
    ...
```

### HTTP 引擎改造

HTTP 引擎当前 `fit_markdown=""` 始终为空。集成 trafilatura 后自动补上：

```python
# http_engine.py — 不需要改
# 因为 Extractor 层会从 result.html 用 trafilatura 提取
# HTTP 引擎只需要确保 html 字段有值（已经有了 ✅）
```

### 依赖安装

```bash
# requirements.txt 新增
trafilatura>=2.0.0
```

```bash
# 安装（约 30MB，含 lxml/courlan/htmldate）
.venv/bin/pip install trafilatura
```

---

## Phase B+：adapter 职责精简

trafilatura 接管通用正文提取后，adapter 的职责从"删噪音"变为"站点特有精调"：

### 改造前后对比

```python
# 改造前：adapter 又删噪音又覆盖 fit_markdown（职责混乱）
class BBCAdapter(DefaultAdapter):
    def transform(self, result):
        md = result.markdown
        md = re.sub(r"Advertisement\s*\n", "", md)
        md = re.sub(r"导航链接...", "\n", md)
        md = re.sub(r"\n{3,}", "\n\n", md)
        return result.model_copy(update={"markdown": md, "fit_markdown": md})

# 改造后：adapter 只做站点特有的事，正文提取交给 Extractor
class BBCAdapter(DefaultAdapter):
    def transform(self, result):
        # fit_markdown 已经由 Extractor 处理好了
        # 这里只做 BBC 特有的微调（如果需要的话）
        return result
```

**大部分 adapter 的 transform() 可以删空**，因为 trafilatura 已经处理了 90% 的噪音。

只有特殊情况才需要 adapter：
- Bloomberg/WSJ 付费墙检测 → 保留
- Twitter/YouTube 抓不到内容的降级提示 → 保留
- HN API 集成 → 保留

---

## 文件改动清单

| 文件 | 改动 | Phase |
|---|---|---|
| `spider/core/extractor.py` | **新增** ~100 行 | B |
| `spider/main.py` | +3 行（import + 调用 extractor） | B |
| `spider/adapters/news.py` | 删 `fit_markdown=md`，精简 transform | A |
| `spider/adapters/tech.py` | 同上 | A |
| `spider/adapters/finance.py` | 同上 | A |
| `spider/adapters/social.py` | 同上 | A |
| `spider/engines/crawl4ai_engine.py` | 补充 excluded_selector | A |
| `requirements.txt` | +1 行 `trafilatura>=2.0.0` | B |
| `tests/test_extractor.py` | **新增** ~80 行 | B |

**总代码量变化**：+180 行（extractor + tests），adapter 减少 ~50 行 → 净增 ~130 行

### 代码量预估

```
当前：1,854 行（spider/）+ 469 行（tests/）= 2,323 行
改后：1,934 行（spider/）+ 549 行（tests/）= 2,483 行
目标上限：2,500 行 ✅
```

---

## 验证计划

### Phase A 验证

```bash
# 1. 跑现有 48 个 tests
.venv/bin/pytest tests/ -q

# 2. 实测 BBC 首页，对比改前改后的 fit_markdown 信噪比
.venv/bin/python3 scrape.py https://www.bbc.com/business --format fit

# 3. 实测 HN，检查表格残骸是否减少
.venv/bin/python3 scrape.py https://news.ycombinator.com --format fit
```

### Phase B 验证

```bash
# 1. 新增 test_extractor.py 测试
.venv/bin/pytest tests/test_extractor.py -v

# 2. 5 站对比测试（改前 vs 改后的 char_count + 噪音链接数）
for url in \
    "https://www.bbc.com/business" \
    "https://finance.yahoo.com" \
    "https://news.ycombinator.com" \
    "https://www.reuters.com/business" \
    "https://paulgraham.com/greatwork.html"; do
    echo "=== $url ==="
    .venv/bin/python3 scrape.py "$url" --format fit 2>/dev/null | head -20
    echo ""
done

# 3. 质量指标对比表
# 手动检查每个站点的：
# - fit_markdown 字符数
# - 链接密度（链接字符 / 总字符）
# - 正文段落数
# - 是否包含导航/广告文本
```

---

## 风险与缓解

| 风险 | 可能性 | 缓解 |
|---|---|---|
| trafilatura 对中文页面效果差 | 中 | 它有中文支持（评测含中文），但需实测知乎/金十 |
| trafilatura 与 Crawl4AI 结果冲突 | 低 | quality_score 自动择优，保留更好的 |
| 新依赖增加 .venv 体积 | 确定 | ~30MB，可接受 |
| 列表页提取后内容太少 | 中 | 列表页本来就是链接为主，fit_markdown 短是正常的 |
| adapter 精简后失去站点特有清洗 | 低 | 保留 adapter 框架，需要时随时加回 |

---

## 不做的事（YAGNI）

- ❌ 不做 Phase C（双提取 + 质量评分自动选择）— 等 B 跑一段时间再看
- ❌ 不做 Jina Reader fallback — 外部 API 依赖，先用本地方案
- ❌ 不做文章/列表页自动分类器 — trafilatura 的 `favor_precision` 已经处理了
- ❌ 不做自定义 Readability 算法 — 用成熟方案

---

## 执行顺序

```
Phase A（30 min）
  1. 修所有 adapter 的 fit_markdown 覆盖 bug
  2. 补全 Crawl4AI excluded_selector
  3. 跑 tests + 实测验证

Phase B（2-3 h）
  4. pip install trafilatura
  5. 新建 spider/core/extractor.py
  6. 集成到 main.py
  7. 精简 adapter transform()
  8. 写 test_extractor.py
  9. 5 站对比验证
  10. 更新文档（ARCHITECTURE.md + status.md）
  11. commit + sync
```

---

_Created: 2026-02-26 | Decision: D11 — trafilatura 提取层_
