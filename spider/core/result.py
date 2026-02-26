"""
爬取结果数据模型。

所有引擎的输出统一为 CrawlResult，供上层消费。
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, computed_field


class CrawlResult(BaseModel):
    """单次爬取的统一结果。"""

    url: str
    title: str = ""
    markdown: str = ""
    fit_markdown: str = ""
    html: str = ""
    screenshot: bytes | None = None
    links: list[str] = Field(default_factory=list)

    # 元信息
    engine: str = ""  # crawl4ai / http
    status: str = "success"  # success / partial / failed
    error: str = ""
    crawled_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def domain(self) -> str:
        """从 URL 提取域名。"""
        from urllib.parse import urlparse

        return urlparse(self.url).netloc

    @computed_field  # type: ignore[prop-decorator]
    @property
    def content_hash(self) -> str:
        """内容指纹，用于去重和变更检测。基于 fit_markdown 或 markdown。"""
        text = self.fit_markdown or self.markdown
        if not text:
            return ""
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def char_count(self) -> int:
        """主要内容的字符数。"""
        return len(self.fit_markdown or self.markdown)
