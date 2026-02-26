"""
主入口函数 — spider.crawl()

一行调用完成抓取，串联 Router → Engine → Extractor → Adapter → Storage。
"""

from __future__ import annotations

import logging
from dataclasses import replace

from spider.core.engine import FetchConfig
from spider.core.extractor import ContentExtractor
from spider.core.result import CrawlResult
from spider.core.router import Router
from spider.engines.crawl4ai_engine import Crawl4AIEngine
from spider.engines.http_engine import HttpEngine
from spider.infra.config import SpiderConfig
from spider.storage.sqlite import SpiderStorage

logger = logging.getLogger("spider")

# 适配器注册表（模块级，不重复创建）
_adapter_registry: list | None = None


def _get_adapters():
    """惰性加载所有适配器（避免每次 crawl() 重新 import + 实例化）。"""
    global _adapter_registry
    if _adapter_registry is not None:
        return _adapter_registry

    from spider.adapters.finance import (
        BloombergAdapter,
        FTAdapter,
        InvestingAdapter,
        MyfxbookAdapter,
        WSJAdapter,
        YahooFinanceAdapter,
    )
    from spider.adapters.news import BBCAdapter, CNBCAdapter, Jin10Adapter, ReutersAdapter
    from spider.adapters.social import MediumAdapter, RedditAdapter, TwitterAdapter, YouTubeAdapter
    from spider.adapters.tech import HackerNewsAdapter, TechCrunchAdapter, TheVergeAdapter, WikipediaAdapter

    _adapter_registry = [
        BBCAdapter(), CNBCAdapter(), ReutersAdapter(), Jin10Adapter(),
        RedditAdapter(), TwitterAdapter(), MediumAdapter(), YouTubeAdapter(),
        InvestingAdapter(), YahooFinanceAdapter(), MyfxbookAdapter(),
        BloombergAdapter(), WSJAdapter(), FTAdapter(),
        TechCrunchAdapter(), TheVergeAdapter(), WikipediaAdapter(), HackerNewsAdapter(),
    ]
    return _adapter_registry


async def crawl(
    url: str,
    *,
    save: bool = False,
    no_cache: bool = False,
    config: SpiderConfig | None = None,
    fetch_config: FetchConfig | None = None,
    screenshot: bool = False,
) -> CrawlResult:
    """
    抓取单个 URL，返回统一结果。

    参数:
        url: 目标 URL
        save: 是否保存到 SQLite 存储
        no_cache: 忽略缓存，强制重抓
        config: 全局配置（默认自动加载）
        fetch_config: 运行时抓取配置（覆盖默认）
        screenshot: 是否截图

    返回:
        CrawlResult 统一结果对象
    """
    cfg = config or SpiderConfig()
    storage = SpiderStorage(cfg.db_path, cfg.pages_dir) if save else None

    try:
        # 检查缓存
        if save and not no_cache and storage:
            cached = storage.get_cached(url)
            if cached and cached.get("file_path"):
                file_path = cfg.storage_dir / cached["file_path"]
                md_content = ""
                if file_path.exists():
                    md_content = file_path.read_text(encoding="utf-8")
                return CrawlResult(
                    url=cached["url"],
                    title=cached.get("title", ""),
                    markdown=md_content,
                    fit_markdown=md_content,  # 文件里存的是 fit，两个都赋值
                    engine=cached.get("engine", ""),
                    status="cached",
                    metadata={"from_cache": True, "cached_at": cached["crawled_at"]},
                )

        # 构建 FetchConfig（不 mutate 用户传入的对象）
        fc = fetch_config or FetchConfig(
            proxy=cfg.proxy if cfg.use_proxy else None,
            timeout=cfg.timeout,
            stealth=cfg.stealth,
            headless=cfg.headless,
            verbose=cfg.verbose,
        )

        # 路由
        crawl4ai = Crawl4AIEngine()
        http = HttpEngine()
        router = Router(default_engine=crawl4ai, http_engine=http)

        for a in _get_adapters():
            for domain in a.domains:
                router.register_adapter(domain, a)

        engine, adapter = router.route(url)

        # 直连判断
        if router.needs_direct(url):
            fc = replace(fc, proxy=None)

        # 适配器定制配置（不 mutate 原对象，先复制再传入）
        fc = adapter.customize_config(fc)

        # 截图配置
        if screenshot:
            fc = replace(fc, extra={**fc.extra, "screenshot": True})

        # 抓取
        try:
            result = await engine.fetch(url, fc)
        finally:
            await crawl4ai.close()
            await http.close()

        # 内容提取（trafilatura 正文提取 + 质量择优）
        extractor = ContentExtractor()
        result = extractor.extract(result)

        # 适配器后处理（站点特有精调）
        result = adapter.transform(result)

        # 存储
        if save and storage:
            storage.save(result)

        return result

    finally:
        if storage:
            storage.close()
