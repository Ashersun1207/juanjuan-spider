"""
社交/社区平台适配器 — Reddit / X(Twitter) / Medium / YouTube / Trends24。

这些平台反爬严格，适配器主要做：
1. 标记需要登录态
2. 调整等待策略
3. 清洗输出噪音
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from spider.adapters.default import DefaultAdapter
from spider.core.result import CrawlResult


@dataclass
class RedditAdapter(DefaultAdapter):
    """
    Reddit 适配器。

    Reddit 反爬严格，代理 IP 大概率被封。
    最佳策略：走 old.reddit.com（轻量 HTML）或用 Reddit API。
    """
    name: str = "reddit"
    domains: list[str] = field(default_factory=lambda: ["reddit.com", "old.reddit.com"])
    scroll: bool = True
    extra_wait: float = 2

    def customize_config(self, config):
        """Reddit 用 old.reddit.com 成功率更高。"""
        config = super().customize_config(config)
        return config

    def transform(self, result: CrawlResult) -> CrawlResult:
        md = result.markdown
        # 去掉 Reddit 的大量 UI 文本
        md = re.sub(r"(?:Get the Reddit app|Log In|Sign Up|Get app)[^\n]*\n?", "", md)
        md = re.sub(r"(?:Share|Save|Hide|Report|More)\s*\n", "", md)
        md = re.sub(r"\n{3,}", "\n\n", md).strip()
        return result.model_copy(update={"markdown": md})


@dataclass
class Trends24Adapter(DefaultAdapter):
    """
    Trends24.in 适配器 — 第三方 Twitter 趋势聚合。

    抓取美国/全球 Twitter 趋势榜单，无需登录。
    页面是静态 HTML，直接爬取即可。
    """
    name: str = "trends24"
    domains: list[str] = field(default_factory=lambda: ["trends24.in"])
    needs_login: bool = False
    scroll: bool = False
    extra_wait: float = 1

    def transform(self, result: CrawlResult) -> CrawlResult:
        """清洗 trends24 的输出，保留趋势名称和链接。"""
        md = result.markdown
        # 去掉页面标题和时间戳
        md = re.sub(r"# .* Trends for last.*\n+", "", md)
        md = re.sub(r"### \d+ .* ago\n+", "", md)
        md = re.sub(r"\n{3,}", "\n\n", md).strip()
        return result.model_copy(update={"markdown": md})


@dataclass
class TwitterAdapter(DefaultAdapter):
    """
    X/Twitter 适配器。

    Twitter 几乎不可能直接抓（需登录 + 重度 SPA）。
    推荐替代方案：
    - Nitter 镜像（如果还在运行）
    - Twitter/X API
    - Serper 搜索 site:x.com
    """
    name: str = "twitter"
    domains: list[str] = field(default_factory=lambda: ["x.com", "twitter.com"])
    needs_login: bool = True
    scroll: bool = True
    extra_wait: float = 3

    def transform(self, result: CrawlResult) -> CrawlResult:
        md = result.markdown
        if len(md) < 100:
            # Twitter 基本抓不到内容，标记为需要 API
            return result.model_copy(update={
                "status": "partial",
                "metadata": {**result.metadata, "hint": "Twitter 需要登录态或 API，建议用 Serper 搜索 site:x.com"},
            })
        return result


@dataclass
class MediumAdapter(DefaultAdapter):
    """Medium 适配器。"""
    name: str = "medium"
    domains: list[str] = field(default_factory=lambda: ["medium.com"])
    scroll: bool = True

    def transform(self, result: CrawlResult) -> CrawlResult:
        md = result.markdown
        # 去掉 Medium 的推广和注册提示
        md = re.sub(r"(?:Open in app|Sign up|Sign in|Member-only story|Get started)[^\n]*\n?", "", md)
        md = re.sub(r"(?:Follow|Clap|Share|Listen)[^\n]*\n?", "", md)
        md = re.sub(r"\n{3,}", "\n\n", md).strip()
        return result.model_copy(update={"markdown": md})


@dataclass
class YouTubeAdapter(DefaultAdapter):
    """
    YouTube 适配器。

    YouTube 页面重度 SPA，直接抓几乎无内容。
    推荐替代方案：
    - yt-dlp 获取视频信息/字幕
    - YouTube Data API
    """
    name: str = "youtube"
    domains: list[str] = field(default_factory=lambda: ["youtube.com", "youtu.be"])
    needs_login: bool = False
    scroll: bool = True
    extra_wait: float = 3

    def transform(self, result: CrawlResult) -> CrawlResult:
        md = result.markdown
        if len(md) < 200:
            return result.model_copy(update={
                "status": "partial",
                "metadata": {**result.metadata, "hint": "YouTube SPA 抓取受限，建议用 yt-dlp 或 YouTube API"},
            })
        return result
