"""
引擎抽象基类。

所有爬取引擎（Crawl4AI、HTTP 等）实现此接口。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from spider.core.result import CrawlResult


@dataclass
class FetchConfig:
    """单次抓取的运行时配置。"""

    proxy: str | None = None
    timeout: int = 30
    stealth: bool = True
    headless: bool = True
    wait: float = 0
    scroll: bool = False
    selector: str | None = None
    js_code: str | None = None
    cookie_file: str | None = None
    verbose: bool = False
    extra: dict[str, Any] = field(default_factory=dict)


class BaseEngine(ABC):
    """爬取引擎抽象基类。"""

    name: str = "base"

    @abstractmethod
    async def fetch(self, url: str, config: FetchConfig | None = None) -> CrawlResult:
        """抓取单个 URL，返回统一结果。"""
        ...

    async def close(self) -> None:
        """释放资源（浏览器实例等）。子类按需覆盖。"""
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self.close()
