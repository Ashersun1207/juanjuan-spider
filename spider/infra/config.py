"""
全局配置，基于 pydantic-settings。

支持环境变量覆盖（SPIDER_ 前缀）和代码直接传参。
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class SpiderConfig(BaseSettings):
    """juanjuan-spider 全局配置。"""

    model_config = SettingsConfigDict(
        env_prefix="SPIDER_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # 代理
    proxy: str = "http://127.0.0.1:7897"
    use_proxy: bool = True

    # 引擎默认参数
    timeout: int = 30  # 页面加载超时（秒）
    stealth: bool = True
    headless: bool = True

    # 存储
    storage_dir: Path = Path("storage")
    db_name: str = "spider.db"

    # 并发
    max_concurrency: int = 5

    # 日志
    verbose: bool = False

    @property
    def db_path(self) -> Path:
        return self.storage_dir / self.db_name

    @property
    def pages_dir(self) -> Path:
        return self.storage_dir / "pages"
