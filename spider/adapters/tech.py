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
        return result.model_copy(update={"markdown": md, "fit_markdown": md})


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
        return result.model_copy(update={"markdown": md, "fit_markdown": md})


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
        return result.model_copy(update={"markdown": md, "fit_markdown": md})


@dataclass
class HackerNewsAdapter(DefaultAdapter):
    """Hacker News 适配器。"""
    name: str = "hackernews"
    domains: list[str] = field(default_factory=lambda: ["news.ycombinator.com"])

    def transform(self, result: CrawlResult) -> CrawlResult:
        md = result.markdown
        # HN 的表格结构转换比较乱，尝试清理
        md = re.sub(r"\| *\| *\| *\| *\|", "", md)
        md = re.sub(r"\| *-+ *\| *-+ *\| *-+ *\| *-+ *\|", "", md)
        md = re.sub(r"\n{3,}", "\n\n", md).strip()
        return result.model_copy(update={"markdown": md, "fit_markdown": md})
