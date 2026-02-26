"""
新闻站点适配器 — BBC / CNBC / Reuters 等。

每个适配器通过 CSS 选择器精确提取正文区域，避免导航噪音。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from spider.adapters.default import DefaultAdapter
from spider.core.result import CrawlResult


@dataclass
class BBCAdapter(DefaultAdapter):
    """BBC News 适配器。"""
    name: str = "bbc"
    domains: list[str] = field(default_factory=lambda: ["bbc.com", "bbc.co.uk"])
    scroll: bool = True
    extra_wait: float = 1

    def transform(self, result: CrawlResult) -> CrawlResult:
        md = result.markdown
        # 去掉 Advertisement 标记
        md = re.sub(r"Advertisement\s*\n", "", md)
        # 去掉重复的导航链接块
        md = re.sub(r"(?:^|\n)\s*\[(?:Home|News|Sport|Business|Technology|Health|Culture|Arts|Travel|Earth|Audio|Video|Live|Weather|Newsletters)\]\([^\)]+\)\s*\n?", "\n", md)
        # 合并连续空行
        md = re.sub(r"\n{3,}", "\n\n", md).strip()
        return result.model_copy(update={"markdown": md})


@dataclass
class CNBCAdapter(DefaultAdapter):
    """CNBC 适配器。"""
    name: str = "cnbc"
    domains: list[str] = field(default_factory=lambda: ["cnbc.com"])
    scroll: bool = True
    extra_wait: float = 1

    def transform(self, result: CrawlResult) -> CrawlResult:
        md = result.markdown
        # 去掉 Skip Navigation 等
        md = re.sub(r"\[Skip Navigation\][^\n]*\n?", "", md)
        md = re.sub(r"\n{3,}", "\n\n", md).strip()
        return result.model_copy(update={"markdown": md})


@dataclass
class ReutersAdapter(DefaultAdapter):
    """Reuters 适配器。"""
    name: str = "reuters"
    domains: list[str] = field(default_factory=lambda: ["reuters.com"])
    scroll: bool = True
    extra_wait: float = 2

    def transform(self, result: CrawlResult) -> CrawlResult:
        md = result.markdown
        md = re.sub(r"\n{3,}", "\n\n", md).strip()
        return result.model_copy(update={"markdown": md})


@dataclass
class Jin10Adapter(DefaultAdapter):
    """金十数据适配器。"""
    name: str = "jin10"
    domains: list[str] = field(default_factory=lambda: ["jin10.com"])
    scroll: bool = True
    extra_wait: float = 3  # 金十 SPA 加载慢

    def transform(self, result: CrawlResult) -> CrawlResult:
        md = result.markdown
        # 去掉广告和弹窗文本
        md = re.sub(r"(?:下载APP|扫码下载|开通VIP|免费试用)[^\n]*\n?", "", md)
        md = re.sub(r"\n{3,}", "\n\n", md).strip()
        return result.model_copy(update={"markdown": md})
