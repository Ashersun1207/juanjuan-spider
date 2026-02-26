"""
金融站点适配器 — Investing.com / Yahoo Finance / Myfxbook / Bloomberg / WSJ / FT。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from spider.adapters.default import DefaultAdapter
from spider.core.result import CrawlResult


@dataclass
class InvestingAdapter(DefaultAdapter):
    """Investing.com 适配器。"""
    name: str = "investing"
    domains: list[str] = field(default_factory=lambda: ["investing.com"])
    scroll: bool = True
    extra_wait: float = 2

    def transform(self, result: CrawlResult) -> CrawlResult:
        md = result.markdown
        md = re.sub(r"(?:Download the App|Install|Sign In|Join for free)[^\n]*\n?", "", md)
        md = re.sub(r"(?:Advertisement|Advertise)[^\n]*\n?", "", md)
        md = re.sub(r"\n{3,}", "\n\n", md).strip()
        return result.model_copy(update={"markdown": md})


@dataclass
class YahooFinanceAdapter(DefaultAdapter):
    """Yahoo Finance 适配器。"""
    name: str = "yahoo_finance"
    domains: list[str] = field(default_factory=lambda: ["finance.yahoo.com"])
    scroll: bool = True
    extra_wait: float = 2

    def transform(self, result: CrawlResult) -> CrawlResult:
        md = result.markdown
        md = re.sub(r"(?:Sign in|Try the app|Get the app|Yahoo Finance Plus)[^\n]*\n?", "", md)
        md = re.sub(r"\n{3,}", "\n\n", md).strip()
        return result.model_copy(update={"markdown": md})


@dataclass
class MyfxbookAdapter(DefaultAdapter):
    """Myfxbook 适配器。"""
    name: str = "myfxbook"
    domains: list[str] = field(default_factory=lambda: ["myfxbook.com"])
    scroll: bool = True
    extra_wait: float = 1

    def transform(self, result: CrawlResult) -> CrawlResult:
        md = result.markdown
        md = re.sub(r"(?:Join|Login|Register|Sign Up|Free Sign Up)[^\n]*\n?", "", md)
        md = re.sub(r"\n{3,}", "\n\n", md).strip()
        return result.model_copy(update={"markdown": md})


@dataclass
class BloombergAdapter(DefaultAdapter):
    """
    Bloomberg 适配器。

    Bloomberg 有 Cloudflare 防护 + 付费墙。
    大部分内容需要订阅。能抓到的通常只有标题和摘要。
    """
    name: str = "bloomberg"
    domains: list[str] = field(default_factory=lambda: ["bloomberg.com"])
    scroll: bool = True
    extra_wait: float = 3

    def transform(self, result: CrawlResult) -> CrawlResult:
        md = result.markdown
        if len(md) < 500:
            return result.model_copy(update={
                "status": "partial",
                "metadata": {**result.metadata, "hint": "Bloomberg 付费墙，仅抓到摘要"},
            })
        md = re.sub(r"(?:Subscribe|Sign In|Already a subscriber)[^\n]*\n?", "", md)
        md = re.sub(r"\n{3,}", "\n\n", md).strip()
        return result.model_copy(update={"markdown": md})


@dataclass
class WSJAdapter(DefaultAdapter):
    """
    Wall Street Journal 适配器。

    WSJ 有付费墙，大部分内容需订阅。
    """
    name: str = "wsj"
    domains: list[str] = field(default_factory=lambda: ["wsj.com"])
    scroll: bool = True
    extra_wait: float = 2

    def transform(self, result: CrawlResult) -> CrawlResult:
        md = result.markdown
        if len(md) < 200:
            return result.model_copy(update={
                "status": "partial",
                "metadata": {**result.metadata, "hint": "WSJ 付费墙，内容受限"},
            })
        md = re.sub(r"(?:Subscribe|Sign In|Already a member)[^\n]*\n?", "", md)
        md = re.sub(r"\n{3,}", "\n\n", md).strip()
        return result.model_copy(update={"markdown": md})


@dataclass
class FTAdapter(DefaultAdapter):
    """Financial Times 适配器。"""
    name: str = "ft"
    domains: list[str] = field(default_factory=lambda: ["ft.com"])
    scroll: bool = True
    extra_wait: float = 2

    def transform(self, result: CrawlResult) -> CrawlResult:
        md = result.markdown
        md = re.sub(r"(?:Subscribe|Sign In|Already a subscriber|Try for \$1)[^\n]*\n?", "", md)
        md = re.sub(r"\n{3,}", "\n\n", md).strip()
        return result.model_copy(update={"markdown": md})
