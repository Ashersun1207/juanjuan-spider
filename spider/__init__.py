"""
juanjuan-spider 🕷️ — 通用网页爬取工具。

快速使用:
    from spider import crawl
    result = await crawl("https://example.com")
"""

from spider.core.result import CrawlResult
from spider.main import crawl

__all__ = ["crawl", "CrawlResult"]
__version__ = "0.4.0"
