"""
内容提取器 — trafilatura 正文提取 + 质量评估。

位于 Engine 和 Adapter 之间，对所有引擎的输出做通用正文提取。
不改变 markdown（raw），只补充/改进 fit_markdown。
"""

from __future__ import annotations

import re

from spider.core.result import CrawlResult


class ContentExtractor:
    """
    通用内容提取器。

    策略：
    1. 如果没有 HTML → 跳过
    2. 用 trafilatura 从 HTML 提取正文 markdown
    3. 与引擎的 fit_markdown 比较质量，择优
    4. 提取元数据（标题/作者/日期）补充到 result.metadata
    """

    def extract(self, result: CrawlResult) -> CrawlResult:
        """对抓取结果做正文提取。"""
        if not result.html or result.status == "failed":
            return result

        import trafilatura

        # 1. trafilatura 提取正文（markdown 格式）
        traf_md = trafilatura.extract(
            result.html,
            output_format="markdown",
            include_links=True,
            include_tables=True,
            include_comments=False,
            favor_precision=True,
        )

        # 2. trafilatura 提取元数据
        meta_doc = trafilatura.bare_extraction(result.html)

        updates: dict = {}

        # 3. fit_markdown 择优
        if traf_md:
            engine_fit = result.fit_markdown
            traf_score = _quality_score(traf_md)
            engine_score = _quality_score(engine_fit) if engine_fit else 0

            if traf_score >= engine_score:
                updates["fit_markdown"] = traf_md

        # 4. 补充元数据
        if meta_doc:
            extra_meta: dict = {}
            for key in ("author", "date", "sitename", "categories", "tags"):
                val = getattr(meta_doc, key, None)
                if val:
                    extra_meta[key] = val
            if extra_meta:
                updates["metadata"] = {**result.metadata, **extra_meta}

            if not result.title and getattr(meta_doc, "title", None):
                updates["title"] = meta_doc.title

        if updates:
            return result.model_copy(update=updates)
        return result


def _quality_score(text: str) -> float:
    """
    内容质量评分（0~1）。

    维度：
    - 文本长度（太短=提取失败）
    - 链接密度（链接字符占比越高=越多噪音）
    - 段落结构（有自然段落=正文特征）
    """
    if not text:
        return 0.0

    length = len(text)
    if length < 100:
        return 0.1

    # 链接密度：[text](url) 的文字部分占总文本比例
    links = re.findall(r"\[([^\]]*)\]\([^\)]+\)", text)
    link_chars = sum(len(link) for link in links)
    link_density = link_chars / length

    # 段落结构：50字以上的段落数
    paragraphs = [p for p in text.split("\n\n") if len(p.strip()) > 50]
    para_score = min(len(paragraphs) / 3, 1.0)

    # 综合评分
    score = (
        min(length / 2000, 1.0) * 0.3       # 长度分（2000字满分）
        + (1 - link_density) * 0.4           # 链接密度越低越好
        + para_score * 0.3                   # 段落结构分
    )

    return round(score, 3)
