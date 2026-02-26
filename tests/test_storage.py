"""SQLite 存储层测试。"""

import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from spider.core.result import CrawlResult
from spider.storage.sqlite import SpiderStorage


@pytest.fixture
def storage(tmp_path):
    """每个测试用独立的临时存储。"""
    db_path = tmp_path / "test.db"
    pages_dir = tmp_path / "pages"
    s = SpiderStorage(db_path, pages_dir)
    yield s
    s.close()


def _make_result(url="https://example.com", markdown="# Test", **kwargs):
    return CrawlResult(url=url, markdown=markdown, engine="test", **kwargs)


class TestSave:
    def test_save_returns_id(self, storage):
        result = _make_result()
        row_id = storage.save(result)
        assert row_id > 0

    def test_save_creates_file(self, storage, tmp_path):
        result = _make_result(markdown="# Hello World")
        storage.save(result)
        # 检查 pages 目录有文件
        pages = list((tmp_path / "pages").rglob("*.md"))
        assert len(pages) == 1
        assert "Hello World" in pages[0].read_text()

    def test_duplicate_skipped(self, storage):
        """相同 URL + 相同 content_hash 不重复插入。"""
        r1 = _make_result(markdown="same")
        r2 = _make_result(markdown="same")
        id1 = storage.save(r1)
        id2 = storage.save(r2)
        assert id1 > 0
        assert id2 == 0  # 重复，跳过
        assert storage.count() == 1

    def test_different_content_saved(self, storage):
        """相同 URL 但不同内容会保存两条。"""
        r1 = _make_result(markdown="version 1")
        r2 = _make_result(markdown="version 2")
        storage.save(r1)
        storage.save(r2)
        assert storage.count() == 2


class TestQuery:
    def test_get_by_url(self, storage):
        storage.save(_make_result(url="https://a.com", markdown="aaa"))
        storage.save(_make_result(url="https://b.com", markdown="bbb"))
        results = storage.get_by_url("https://a.com")
        assert len(results) == 1
        assert results[0]["url"] == "https://a.com"

    def test_get_by_domain(self, storage):
        storage.save(_make_result(url="https://zhihu.com/q/1", markdown="q1"))
        storage.save(_make_result(url="https://zhihu.com/q/2", markdown="q2"))
        storage.save(_make_result(url="https://reddit.com/r/1", markdown="r1"))
        results = storage.get_by_domain("zhihu.com")
        assert len(results) == 2

    def test_recent(self, storage):
        for i in range(5):
            storage.save(_make_result(
                url=f"https://example.com/{i}",
                markdown=f"content {i}",
            ))
        results = storage.recent(limit=3)
        assert len(results) == 3

    def test_search_by_title(self, storage):
        storage.save(_make_result(
            url="https://a.com",
            markdown="x",
            title="Python 教程",
        ))
        storage.save(_make_result(
            url="https://b.com",
            markdown="y",
            title="Java 入门",
        ))
        results = storage.search("Python")
        assert len(results) == 1

    def test_search_by_url(self, storage):
        storage.save(_make_result(url="https://github.com/test", markdown="gh"))
        results = storage.search("github")
        assert len(results) == 1


class TestCache:
    def test_cache_hit(self, storage):
        storage.save(_make_result(markdown="cached content"))
        cached = storage.get_cached("https://example.com", max_age_seconds=3600)
        assert cached is not None
        assert cached["url"] == "https://example.com"

    def test_cache_miss_different_url(self, storage):
        storage.save(_make_result(url="https://a.com", markdown="a"))
        cached = storage.get_cached("https://b.com")
        assert cached is None

    def test_cache_miss_expired(self, storage):
        """过期缓存返回 None。"""
        result = _make_result(markdown="old")
        # 手动设一个过去的时间
        result.crawled_at = datetime.now(timezone.utc) - timedelta(hours=2)
        storage.save(result)
        cached = storage.get_cached("https://example.com", max_age_seconds=3600)
        assert cached is None

    def test_cache_ignores_failed(self, storage):
        """失败的结果不作为缓存。"""
        storage.save(_make_result(status="failed", error="timeout"))
        cached = storage.get_cached("https://example.com")
        assert cached is None


class TestCount:
    def test_empty(self, storage):
        assert storage.count() == 0

    def test_after_saves(self, storage):
        storage.save(_make_result(url="https://a.com", markdown="a"))
        storage.save(_make_result(url="https://b.com", markdown="b"))
        assert storage.count() == 2
