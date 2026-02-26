"""
HTTP 轻量引擎 — 用于不需要 JS 渲染的静态页面。

基于 httpx + markdownify，无需浏览器，速度快、资源省。
"""

from __future__ import annotations

import re
import time

import httpx
from markdownify import markdownify

from spider.core.engine import BaseEngine, FetchConfig
from spider.core.result import CrawlResult


class HttpEngine(BaseEngine):
    """httpx 轻量引擎，适合纯静态页面。"""

    name = "http"

    def __init__(self):
        self._client: httpx.AsyncClient | None = None

    async def _ensure_client(self, config: FetchConfig) -> httpx.AsyncClient:
        """惰性初始化 httpx client。"""
        if self._client is None:
            proxy = config.proxy if config.proxy else None
            self._client = httpx.AsyncClient(
                timeout=config.timeout,
                follow_redirects=True,
                proxy=proxy,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/131.0.0.0 Safari/537.36"
                    ),
                    "Accept": "text/html,application/xhtml+xml,*/*",
                    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8",
                },
            )
        return self._client

    async def fetch(self, url: str, config: FetchConfig | None = None) -> CrawlResult:
        """HTTP GET 抓取 + HTML→Markdown 转换。"""
        cfg = config or FetchConfig()
        client = await self._ensure_client(cfg)

        t0 = time.monotonic()
        try:
            resp = await client.get(url)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            return CrawlResult(
                url=url,
                engine=self.name,
                status="failed",
                error=str(e),
                duration_ms=int((time.monotonic() - t0) * 1000),
            )

        duration_ms = int((time.monotonic() - t0) * 1000)
        html = resp.text

        # HTML → Markdown
        raw_md = markdownify(html, heading_style="ATX", strip=["script", "style", "nav", "footer", "noscript", "svg"])
        # 简单清理：合并连续空行
        raw_md = re.sub(r"\n{3,}", "\n\n", raw_md).strip()

        # 提取 title
        title = ""
        title_match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()

        # 提取链接
        links = re.findall(r'href="(https?://[^"]+)"', html)

        return CrawlResult(
            url=url,
            title=title,
            markdown=raw_md,
            fit_markdown="",  # HTTP 引擎不做智能去噪
            html=html,
            links=list(set(links)),
            engine=self.name,
            status="success" if raw_md else "partial",
            duration_ms=duration_ms,
        )

    async def close(self) -> None:
        """关闭 httpx client。"""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
