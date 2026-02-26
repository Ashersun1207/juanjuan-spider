"""Router 路由逻辑测试。"""

from unittest.mock import AsyncMock

from spider.adapters.default import DefaultAdapter
from spider.core.router import Router


def _make_engine(name: str):
    """造一个假引擎。"""
    engine = AsyncMock()
    engine.name = name
    return engine


def test_default_route():
    """无适配器时返回默认引擎 + 默认适配器。"""
    crawl4ai = _make_engine("crawl4ai")
    router = Router(default_engine=crawl4ai)

    engine, adapter = router.route("https://unknown-site.com/page")
    assert engine.name == "crawl4ai"
    assert adapter.name == "default"


def test_static_site_uses_http():
    """arxiv 是纯静态，应该走 HTTP 引擎。"""
    crawl4ai = _make_engine("crawl4ai")
    http = _make_engine("http")
    router = Router(default_engine=crawl4ai, http_engine=http)

    engine, _ = router.route("https://arxiv.org/abs/2301.07041")
    assert engine.name == "http"


def test_hn_uses_crawl4ai():
    """HN 是 table 布局，markdownify 无法处理，应走 Crawl4AI。"""
    crawl4ai = _make_engine("crawl4ai")
    http = _make_engine("http")
    router = Router(default_engine=crawl4ai, http_engine=http)

    engine, _ = router.route("https://news.ycombinator.com/")
    assert engine.name == "crawl4ai"


def test_arxiv_uses_http():
    crawl4ai = _make_engine("crawl4ai")
    http = _make_engine("http")
    router = Router(default_engine=crawl4ai, http_engine=http)

    engine, _ = router.route("https://arxiv.org/abs/2301.07041")
    assert engine.name == "http"


def test_github_uses_default():
    """GitHub 是 SPA，需要浏览器。"""
    crawl4ai = _make_engine("crawl4ai")
    http = _make_engine("http")
    router = Router(default_engine=crawl4ai, http_engine=http)

    engine, _ = router.route("https://github.com/apify/crawlee")
    assert engine.name == "crawl4ai"


def test_dynamic_site_uses_default():
    """动态站点用默认引擎（Crawl4AI）。"""
    crawl4ai = _make_engine("crawl4ai")
    http = _make_engine("http")
    router = Router(default_engine=crawl4ai, http_engine=http)

    engine, _ = router.route("https://zhihu.com/question/123")
    assert engine.name == "crawl4ai"


def test_custom_adapter():
    """注册自定义适配器后能匹配。"""
    crawl4ai = _make_engine("crawl4ai")
    zhihu_adapter = DefaultAdapter(name="zhihu", domains=["zhihu.com"])

    router = Router(
        default_engine=crawl4ai,
        adapters={"zhihu.com": zhihu_adapter},
    )

    _, adapter = router.route("https://zhihu.com/question/123")
    assert adapter.name == "zhihu"


def test_subdomain_adapter_match():
    """子域名也能匹配到主域名适配器。"""
    crawl4ai = _make_engine("crawl4ai")
    zhihu_adapter = DefaultAdapter(name="zhihu", domains=["zhihu.com"])

    router = Router(
        default_engine=crawl4ai,
        adapters={"zhihu.com": zhihu_adapter},
    )

    _, adapter = router.route("https://zhuanlan.zhihu.com/p/123456")
    assert adapter.name == "zhihu"


def test_www_stripped():
    """www. 前缀被自动去掉。"""
    crawl4ai = _make_engine("crawl4ai")
    adapter = DefaultAdapter(name="example")
    router = Router(
        default_engine=crawl4ai,
        adapters={"example.com": adapter},
    )

    _, matched = router.route("https://www.example.com/page")
    assert matched.name == "example"


def test_register_adapter():
    """动态注册适配器。"""
    crawl4ai = _make_engine("crawl4ai")
    router = Router(default_engine=crawl4ai)

    new_adapter = DefaultAdapter(name="reddit")
    router.register_adapter("reddit.com", new_adapter)

    _, adapter = router.route("https://reddit.com/r/python")
    assert adapter.name == "reddit"


def test_no_http_engine_fallback():
    """没有 HTTP 引擎时，静态站也用默认引擎。"""
    crawl4ai = _make_engine("crawl4ai")
    router = Router(default_engine=crawl4ai)

    engine, _ = router.route("https://news.ycombinator.com/")
    assert engine.name == "crawl4ai"
