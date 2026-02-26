"""
Crawl4AI 引擎 — 主力浏览器渲染引擎。

基于 Crawl4AI 0.8.x 的 AsyncWebCrawler，支持反检测、JS 渲染、Cookie 注入。
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from spider.core.engine import BaseEngine, FetchConfig
from spider.core.result import CrawlResult


class Crawl4AIEngine(BaseEngine):
    """Crawl4AI 浏览器渲染引擎。"""

    name = "crawl4ai"

    def __init__(self):
        self._crawler = None

    async def _ensure_crawler(self, config: FetchConfig):
        """惰性初始化 Crawler 实例。"""
        from crawl4ai import AsyncWebCrawler, BrowserConfig

        browser_kwargs: dict = {
            "headless": config.headless,
            "enable_stealth": config.stealth,
            "verbose": config.verbose,
        }
        if config.proxy:
            browser_kwargs["proxy"] = config.proxy

        bc = BrowserConfig(**browser_kwargs)

        if self._crawler is not None:
            await self._crawler.__aexit__(None, None, None)

        self._crawler = AsyncWebCrawler(config=bc)
        await self._crawler.__aenter__()

    async def fetch(self, url: str, config: FetchConfig | None = None) -> CrawlResult:
        """抓取单个 URL。"""
        from crawl4ai import CrawlerRunConfig

        cfg = config or FetchConfig()
        await self._ensure_crawler(cfg)
        assert self._crawler is not None

        # 构建运行配置
        run_kwargs: dict = {
            "page_timeout": cfg.timeout * 1000,
            "verbose": cfg.verbose,
            # 去噪：排除导航、页脚、侧边栏等非正文元素
            "excluded_tags": ["nav", "footer", "header", "aside", "noscript"],
            "excluded_selector": ",".join([
                # 导航 & 页头页脚
                "[role='navigation']", "[role='banner']", "[role='contentinfo']",
                ".navbar", ".menu-bar", ".site-footer", ".cookie-banner",
                # 广告 & Cookie
                ".advertisement", "#cookie-consent", "#cookie-banner",
                "[class*='cookie']", "[id*='cookie']",
                "[class*='advert']", "[class*='sponsor']",
                # 侧边栏
                ".sidebar", "[role='complementary']", "aside",
                # 社交 & 分享
                ".social-share", ".share-buttons", "[class*='share']",
                # 推荐 & 订阅
                ".related-articles", ".recommended", "[class*='related']",
                ".newsletter-signup", ".subscribe-form",
                # 弹窗
                "[class*='popup']", "[class*='modal']", "[class*='overlay']",
                # 跳转链接
                "[class*='skip-to']", ".skip-navigation",
            ]),
            "remove_overlay_elements": True,
            "exclude_external_images": True,
        }
        if cfg.selector:
            run_kwargs["css_selector"] = cfg.selector
        if cfg.wait > 0:
            run_kwargs["delay_before_return_html"] = cfg.wait
        if cfg.scroll:
            run_kwargs["scan_full_page"] = True
        if cfg.js_code:
            run_kwargs["js_code"] = cfg.js_code

        rc = CrawlerRunConfig(**run_kwargs)

        # Cookie 注入
        if cfg.cookie_file:
            cookie_path = Path(cfg.cookie_file)
            if cookie_path.exists():
                cookies = json.loads(cookie_path.read_text())
                if (
                    hasattr(self._crawler, "crawler_strategy")
                    and self._crawler.crawler_strategy
                ):
                    ctx = getattr(
                        self._crawler.crawler_strategy, "browser_context", None
                    )
                    if ctx:
                        await ctx.add_cookies(cookies)

        # 执行抓取
        t0 = time.monotonic()
        result = await self._crawler.arun(url=url, config=rc)
        duration_ms = int((time.monotonic() - t0) * 1000)

        if not result.success:
            return CrawlResult(
                url=url,
                engine=self.name,
                status="failed",
                error=result.error_message or "unknown error",
                duration_ms=duration_ms,
            )

        # 提取内容
        raw_md = ""
        fit_md = ""
        if result.markdown:
            raw_md = result.markdown.raw_markdown or ""
            fit_md = result.markdown.fit_markdown or ""

        # 提取链接
        links: list[str] = []
        if hasattr(result, "links") and result.links:
            for link_group in [result.links.get("internal", []),
                               result.links.get("external", [])]:
                for link in link_group:
                    if isinstance(link, dict) and "href" in link:
                        links.append(link["href"])
                    elif isinstance(link, str):
                        links.append(link)

        # 截图
        screenshot_bytes = None
        if result.screenshot:
            import base64
            screenshot_bytes = base64.b64decode(result.screenshot)

        return CrawlResult(
            url=url,
            title=(result.metadata.get("title") or "") if result.metadata else "",
            markdown=raw_md,
            fit_markdown=fit_md,
            html=result.html or "",
            screenshot=screenshot_bytes,
            links=links,
            engine=self.name,
            status="success" if (raw_md or fit_md) else "partial",
            duration_ms=duration_ms,
        )

    async def close(self) -> None:
        """关闭浏览器。"""
        if self._crawler is not None:
            await self._crawler.__aexit__(None, None, None)
            self._crawler = None
