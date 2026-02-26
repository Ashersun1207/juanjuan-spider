"""
主入口函数 — spider.crawl()

一行调用完成抓取，串联 Router → Engine → Adapter → Storage。
"""

from __future__ import annotations

from spider.core.engine import FetchConfig
from spider.core.result import CrawlResult
from spider.core.router import Router
from spider.engines.crawl4ai_engine import Crawl4AIEngine
from spider.engines.http_engine import HttpEngine
from spider.infra.config import SpiderConfig
from spider.storage.sqlite import SpiderStorage


async def crawl(
    url: str,
    *,
    save: bool = False,
    no_cache: bool = False,
    config: SpiderConfig | None = None,
    fetch_config: FetchConfig | None = None,
) -> CrawlResult:
    """
    抓取单个 URL，返回统一结果。

    参数:
        url: 目标 URL
        save: 是否保存到 SQLite 存储
        no_cache: 忽略缓存，强制重抓
        config: 全局配置（默认自动加载）
        fetch_config: 运行时抓取配置（覆盖默认）

    返回:
        CrawlResult 统一结果对象
    """
    cfg = config or SpiderConfig()
    storage = SpiderStorage(cfg.db_path, cfg.pages_dir) if save else None

    # 检查缓存
    if save and not no_cache and storage:
        cached = storage.get_cached(url)
        if cached and cached.get("file_path"):
            # 从文件读取内容
            file_path = cfg.storage_dir / cached["file_path"]
            md_content = ""
            if file_path.exists():
                md_content = file_path.read_text(encoding="utf-8")
            return CrawlResult(
                url=cached["url"],
                title=cached.get("title", ""),
                markdown=md_content,
                engine=cached.get("engine", ""),
                status="cached",
                metadata={"from_cache": True, "cached_at": cached["crawled_at"]},
            )

    # 构建 FetchConfig
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

    # 注册站点适配器
    from spider.adapters.news import BBCAdapter, CNBCAdapter, ReutersAdapter, Jin10Adapter
    for adapter_cls in [BBCAdapter, CNBCAdapter, ReutersAdapter, Jin10Adapter]:
        a = adapter_cls()
        for domain in a.domains:
            router.register_adapter(domain, a)

    engine, adapter = router.route(url)

    # 适配器定制配置
    fc = adapter.customize_config(fc)

    # 抓取
    try:
        result = await engine.fetch(url, fc)
    finally:
        await crawl4ai.close()
        await http.close()

    # 适配器后处理
    result = adapter.transform(result)

    # 存储
    if save and storage:
        storage.save(result)
        storage.close()

    return result
