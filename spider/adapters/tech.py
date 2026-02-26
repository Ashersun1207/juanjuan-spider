"""
科技/知识站点适配器 — TechCrunch / The Verge / Wikipedia / HN。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from spider.adapters.default import DefaultAdapter
from spider.core.result import CrawlResult


@dataclass
class TechCrunchAdapter(DefaultAdapter):
    """TechCrunch 适配器。"""
    name: str = "techcrunch"
    domains: list[str] = field(default_factory=lambda: ["techcrunch.com"])
    scroll: bool = True

    def transform(self, result: CrawlResult) -> CrawlResult:
        md = result.markdown
        md = re.sub(r"(?:Log in|Sign up|Newsletter|Subscribe)[^\n]*\n?", "", md)
        md = re.sub(r"(?:© 20\d\d TechCrunch)[^\n]*\n?", "", md)
        md = re.sub(r"\n{3,}", "\n\n", md).strip()
        return result.model_copy(update={"markdown": md})


@dataclass
class TheVergeAdapter(DefaultAdapter):
    """The Verge 适配器。"""
    name: str = "theverge"
    domains: list[str] = field(default_factory=lambda: ["theverge.com"])
    scroll: bool = True

    def transform(self, result: CrawlResult) -> CrawlResult:
        md = result.markdown
        md = re.sub(r"(?:The Verge homepage|Site search|Filed under)[^\n]*\n?", "", md)
        md = re.sub(r"\n{3,}", "\n\n", md).strip()
        return result.model_copy(update={"markdown": md})


@dataclass
class WikipediaAdapter(DefaultAdapter):
    """
    Wikipedia 适配器。

    注意：Wikipedia 通过代理可能 403，Router 会标记为直连。
    内容质量高，直接用 HTTP 引擎即可。
    """
    name: str = "wikipedia"
    domains: list[str] = field(default_factory=lambda: ["wikipedia.org"])

    def transform(self, result: CrawlResult) -> CrawlResult:
        md = result.markdown
        # 去掉编辑链接和引用标记
        md = re.sub(r"\[edit\]", "", md)
        md = re.sub(r"\[\d+\]", "", md)
        # 去掉导航
        md = re.sub(r"(?:From Wikipedia|Jump to navigation|Jump to search)[^\n]*\n?", "", md)
        md = re.sub(r"\n{3,}", "\n\n", md).strip()
        return result.model_copy(update={"markdown": md})


@dataclass
class HackerNewsAdapter(DefaultAdapter):
    """
    Hacker News 适配器。

    HN 的 HTML 是嵌套 table 布局，markdownify 转换出大量管道符残骸。
    清洗策略：删表格标记 → 提取 "标题 (来源) / N points / N comments" 结构。
    更好方案：Phase B 用 HN API (/v0/topstories.json)。
    """
    name: str = "hackernews"
    domains: list[str] = field(default_factory=lambda: ["news.ycombinator.com"])

    def transform(self, result: CrawlResult) -> CrawlResult:
        md = result.markdown
        # 删除所有表格管道符和分隔行
        md = re.sub(r"\|[^\n]*\|", "", md)
        md = re.sub(r"^\s*-+\s*$", "", md, flags=re.MULTILINE)
        # 删空链接和残留 UI 文本
        md = re.sub(r"\[hide\]\([^\)]+\)", "", md)
        md = re.sub(r"\[login\]\([^\)]+\)", "", md)
        md = re.sub(r"\[More\]\([^\)]+\)", "", md)
        md = re.sub(r"\d+\.\s*$", "", md, flags=re.MULTILINE)  # 孤立序号
        # 合并连续空行
        md = re.sub(r"\n{3,}", "\n\n", md).strip()
        if not md or len(md) < 200:
            return result.model_copy(update={
                "markdown": md,
                "metadata": {**result.metadata, "hint": "HN 表格布局清洗后内容较少，建议用 API: https://hacker-news.firebaseio.com/v0/topstories.json"},
            })
        return result.model_copy(update={"markdown": md})
