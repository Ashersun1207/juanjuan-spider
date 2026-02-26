"""配置加载测试。"""

import os
from pathlib import Path

from spider.infra.config import SpiderConfig


def test_defaults():
    cfg = SpiderConfig()
    assert cfg.proxy == "http://127.0.0.1:7897"
    assert cfg.use_proxy is True
    assert cfg.timeout == 30
    assert cfg.stealth is True
    assert cfg.headless is True
    assert cfg.max_concurrency == 5


def test_db_path():
    cfg = SpiderConfig(storage_dir=Path("/tmp/test-spider"))
    assert cfg.db_path == Path("/tmp/test-spider/spider.db")


def test_pages_dir():
    cfg = SpiderConfig(storage_dir=Path("/tmp/test-spider"))
    assert cfg.pages_dir == Path("/tmp/test-spider/pages")


def test_env_override(monkeypatch):
    """环境变量覆盖配置。"""
    monkeypatch.setenv("SPIDER_PROXY", "http://proxy:9999")
    monkeypatch.setenv("SPIDER_TIMEOUT", "60")
    monkeypatch.setenv("SPIDER_VERBOSE", "true")

    cfg = SpiderConfig()
    assert cfg.proxy == "http://proxy:9999"
    assert cfg.timeout == 60
    assert cfg.verbose is True


def test_custom_db_name():
    cfg = SpiderConfig(db_name="custom.db")
    assert cfg.db_path.name == "custom.db"
