"""MCP Server 测试 — 验证 tool 定义和内部函数。"""

import json
import pytest

from spider.mcp.server import create_server, _do_scrape, _get_storage


def test_server_creates():
    """Server 实例化不报错。"""
    server = create_server()
    assert server is not None
    assert server.name == "juanjuan-spider"


def test_storage_query_empty():
    """查询空数据库不报错。"""
    storage = _get_storage()
    results = storage.recent(5)
    # 可能有之前测试留下的数据，不报错就行
    assert isinstance(results, list)


def test_storage_search_empty():
    """搜索空关键词不报错。"""
    storage = _get_storage()
    results = storage.search("不存在的关键词12345")
    assert isinstance(results, list)
    assert len(results) == 0


@pytest.mark.asyncio
async def test_do_scrape_bad_url():
    """抓取无效 URL 返回 failed 而不是崩溃。"""
    result = await _do_scrape(
        url="https://this-domain-does-not-exist-12345.com",
        save=False,
        max_chars=100,
    )
    # 应该返回 dict 而不是抛异常
    assert isinstance(result, dict)
    assert "status" in result
