"""
URL 路由器。

根据 URL 判断使用哪个引擎和适配器。
参考 Crawlee 的 Router 设计，但大幅简化。
"""

from __future__ import annotations

from urllib.parse import urlparse

from spider.adapters.default import DefaultAdapter
from spider.core.engine import BaseEngine


class Router:
    """
    URL → (Engine, Adapter) 路由。

    规则优先级：
    1. 精确域名匹配（注册的适配器）
    2. 引擎类型判断（需要 JS 渲染 → Crawl4AI，静态 → HTTP）
    3. 兜底使用默认引擎 + 默认适配器
    """

    # 已知需要浏览器渲染的域名（持续积累）
    BROWSER_REQUIRED: set[str] = {
        "zhihu.com",
        "xiaohongshu.com",
        "weibo.com",
        "reddit.com",
        "bloomberg.com",
        "investing.com",
        "jin10.com",
    }

    # 已知纯静态、不需要浏览器的域名
    STATIC_SAFE: set[str] = {
        "news.ycombinator.com",
        "raw.githubusercontent.com",
        "arxiv.org",
        "docs.python.org",
        "en.wikipedia.org",
    }

    def __init__(
        self,
        default_engine: BaseEngine,
        http_engine: BaseEngine | None = None,
        adapters: dict[str, DefaultAdapter] | None = None,
    ):
        self._default_engine = default_engine
        self._http_engine = http_engine
        self._adapters: dict[str, DefaultAdapter] = adapters or {}
        self._default_adapter = DefaultAdapter()

    def register_adapter(self, domain: str, adapter: DefaultAdapter) -> None:
        """注册域名专用适配器。"""
        self._adapters[domain] = adapter

    def route(self, url: str) -> tuple[BaseEngine, DefaultAdapter]:
        """
        路由 URL 到合适的引擎和适配器。

        返回: (engine, adapter) 元组
        """
        domain = self._extract_domain(url)

        # 1. 查适配器（适配器可能指定引擎偏好）
        adapter = self._find_adapter(domain)

        # 2. 选引擎
        engine = self._select_engine(domain)

        return engine, adapter

    def _extract_domain(self, url: str) -> str:
        """提取主域名（去掉 www. 前缀）。"""
        host = urlparse(url).netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        return host

    def _find_adapter(self, domain: str) -> DefaultAdapter:
        """按域名查找适配器，支持子域名匹配。"""
        # 精确匹配
        if domain in self._adapters:
            return self._adapters[domain]
        # 主域名匹配（sub.example.com → example.com）
        parts = domain.split(".")
        if len(parts) > 2:
            parent = ".".join(parts[-2:])
            if parent in self._adapters:
                return self._adapters[parent]
        return self._default_adapter

    def _select_engine(self, domain: str) -> BaseEngine:
        """根据域名选引擎。"""
        # 已知静态站 + 有 HTTP 引擎 → 用轻量引擎
        if self._http_engine and self._is_static(domain):
            return self._http_engine
        return self._default_engine

    def _is_static(self, domain: str) -> bool:
        """判断域名是否可以用纯 HTTP 抓取。"""
        for safe in self.STATIC_SAFE:
            if domain == safe or domain.endswith("." + safe):
                return True
        return False
