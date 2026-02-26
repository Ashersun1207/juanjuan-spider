"""CrawlResult 数据模型测试。"""

from spider.core.result import CrawlResult


def test_basic_creation():
    r = CrawlResult(url="https://example.com", markdown="# Hello")
    assert r.url == "https://example.com"
    assert r.markdown == "# Hello"
    assert r.status == "success"


def test_domain_extraction():
    r = CrawlResult(url="https://www.zhihu.com/question/123")
    assert r.domain == "www.zhihu.com"


def test_domain_with_port():
    r = CrawlResult(url="http://localhost:8080/page")
    assert r.domain == "localhost:8080"


def test_content_hash_consistency():
    """相同内容应该产生相同 hash。"""
    r1 = CrawlResult(url="https://a.com", markdown="same content")
    r2 = CrawlResult(url="https://b.com", markdown="same content")
    assert r1.content_hash == r2.content_hash


def test_content_hash_difference():
    """不同内容应该产生不同 hash。"""
    r1 = CrawlResult(url="https://a.com", markdown="content A")
    r2 = CrawlResult(url="https://a.com", markdown="content B")
    assert r1.content_hash != r2.content_hash


def test_content_hash_prefers_fit():
    """有 fit_markdown 时 hash 基于 fit_markdown。"""
    r = CrawlResult(url="https://a.com", markdown="raw", fit_markdown="fit")
    r2 = CrawlResult(url="https://a.com", markdown="fit")  # 和 fit_markdown 相同
    assert r.content_hash == r2.content_hash


def test_empty_content_hash():
    r = CrawlResult(url="https://a.com")
    assert r.content_hash == ""


def test_char_count():
    r = CrawlResult(url="https://a.com", markdown="12345", fit_markdown="123")
    assert r.char_count == 3  # fit_markdown 优先


def test_char_count_fallback():
    r = CrawlResult(url="https://a.com", markdown="12345")
    assert r.char_count == 5  # 无 fit → 用 markdown


def test_failed_result():
    r = CrawlResult(url="https://a.com", status="failed", error="timeout")
    assert r.status == "failed"
    assert r.char_count == 0
    assert r.content_hash == ""
