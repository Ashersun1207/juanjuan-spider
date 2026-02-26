"""
juanjuan-spider MCP Server 🕷️

通过 MCP 协议暴露爬虫能力给 AI Agent。

启动方式:
  python3 -m spider.mcp.server          # stdio 模式（Claude Desktop / OpenClaw）
  python3 -m spider.mcp.server --sse    # SSE 模式（HTTP 远程调用）

Tools:
  spider_scrape      — 抓取单个 URL，返回 markdown/html/text
  spider_batch       — 批量抓取多个 URL
  spider_query       — 查询历史爬取记录（按 URL/域名/关键词）
  spider_screenshot  — 网页截图
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from spider.core.engine import FetchConfig
from spider.core.result import CrawlResult
from spider.engines.crawl4ai_engine import Crawl4AIEngine
from spider.engines.http_engine import HttpEngine
from spider.core.router import Router
from spider.infra.config import SpiderConfig
from spider.storage.sqlite import SpiderStorage

# 全局实例（MCP server 生命周期内复用）
_config = SpiderConfig()
_crawl4ai: Crawl4AIEngine | None = None
_http: HttpEngine | None = None
_storage: SpiderStorage | None = None


def _get_storage() -> SpiderStorage:
    global _storage
    if _storage is None:
        _storage = SpiderStorage(_config.db_path, _config.pages_dir)
    return _storage


async def _get_engines() -> tuple[Crawl4AIEngine, HttpEngine]:
    global _crawl4ai, _http
    if _crawl4ai is None:
        _crawl4ai = Crawl4AIEngine()
    if _http is None:
        _http = HttpEngine()
    return _crawl4ai, _http


async def _do_scrape(
    url: str,
    format: str = "markdown",
    selector: str | None = None,
    wait: float = 0,
    scroll: bool = False,
    max_chars: int = 0,
    save: bool = True,
    no_cache: bool = False,
) -> dict[str, Any]:
    """核心抓取逻辑，供各 tool 复用。"""
    storage = _get_storage()

    # 缓存检查
    if save and not no_cache:
        cached = storage.get_cached(url)
        if cached and cached.get("file_path"):
            file_path = _config.storage_dir / cached["file_path"]
            if file_path.exists():
                content = file_path.read_text(encoding="utf-8")
                if max_chars > 0 and len(content) > max_chars:
                    content = content[:max_chars] + f"\n\n... (截断于 {max_chars} 字符)"
                return {
                    "url": cached["url"],
                    "title": cached.get("title", ""),
                    "content": content,
                    "engine": cached.get("engine", ""),
                    "status": "cached",
                    "char_count": len(content),
                }

    # 构建配置
    fc = FetchConfig(
        proxy=_config.proxy if _config.use_proxy else None,
        timeout=_config.timeout,
        stealth=_config.stealth,
        headless=_config.headless,
        wait=wait,
        scroll=scroll,
        selector=selector,
    )

    # 路由 + 抓取
    crawl4ai, http = await _get_engines()
    router = Router(default_engine=crawl4ai, http_engine=http)
    engine, adapter = router.route(url)
    fc = adapter.customize_config(fc)

    result = await engine.fetch(url, fc)
    result = adapter.transform(result)

    # 存储
    if save:
        storage.save(result)

    # 选择输出格式
    if format == "html":
        content = result.html
    elif format == "fit":
        content = result.fit_markdown or result.markdown
    elif format == "text":
        import re
        content = re.sub(r'!?\[([^\]]*)\]\([^)]+\)', r'\1', result.markdown)
        content = re.sub(r'[#*_`~]', '', content)
    else:
        content = result.markdown

    if max_chars > 0 and len(content) > max_chars:
        content = content[:max_chars] + f"\n\n... (截断于 {max_chars} 字符)"

    return {
        "url": result.url,
        "title": result.title,
        "content": content,
        "engine": result.engine,
        "status": result.status,
        "char_count": len(content),
        "duration_ms": result.duration_ms,
    }


def create_server() -> Server:
    """创建 MCP Server 实例。"""
    server = Server("juanjuan-spider")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="spider_scrape",
                description=(
                    "抓取单个网页，返回 markdown/html/text。"
                    "支持 JS 渲染（动态页面）、反检测、CSS 选择器、自动滚动。"
                    "结果自动缓存到本地 SQLite。"
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "目标 URL",
                        },
                        "format": {
                            "type": "string",
                            "enum": ["markdown", "html", "text", "fit"],
                            "default": "markdown",
                            "description": "输出格式（fit=智能去噪 markdown）",
                        },
                        "selector": {
                            "type": "string",
                            "description": "CSS 选择器，只抓匹配内容",
                        },
                        "wait": {
                            "type": "number",
                            "default": 0,
                            "description": "额外等待秒数（等 JS 渲染）",
                        },
                        "scroll": {
                            "type": "boolean",
                            "default": False,
                            "description": "自动滚动加载懒加载内容",
                        },
                        "max_chars": {
                            "type": "integer",
                            "default": 0,
                            "description": "输出最大字符数（0=不限）",
                        },
                        "no_cache": {
                            "type": "boolean",
                            "default": False,
                            "description": "忽略缓存，强制重抓",
                        },
                    },
                    "required": ["url"],
                },
            ),
            Tool(
                name="spider_batch",
                description="批量抓取多个 URL，返回每个 URL 的结果摘要。",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "urls": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "URL 列表",
                        },
                        "format": {
                            "type": "string",
                            "enum": ["markdown", "html", "text", "fit"],
                            "default": "markdown",
                        },
                        "max_chars": {
                            "type": "integer",
                            "default": 5000,
                            "description": "每个 URL 的最大字符数",
                        },
                    },
                    "required": ["urls"],
                },
            ),
            Tool(
                name="spider_query",
                description=(
                    "查询历史爬取记录。支持按 URL、域名、关键词搜索，"
                    "或列出最近的爬取记录。"
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "精确 URL 查询",
                        },
                        "domain": {
                            "type": "string",
                            "description": "按域名查询（如 zhihu.com）",
                        },
                        "keyword": {
                            "type": "string",
                            "description": "按标题或 URL 模糊搜索",
                        },
                        "limit": {
                            "type": "integer",
                            "default": 10,
                            "description": "返回条数上限",
                        },
                    },
                },
            ),
            Tool(
                name="spider_screenshot",
                description="对网页截图，返回 base64 编码的 PNG 图片。",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "目标 URL",
                        },
                        "wait": {
                            "type": "number",
                            "default": 1,
                            "description": "截图前等待秒数",
                        },
                    },
                    "required": ["url"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        try:
            if name == "spider_scrape":
                result = await _do_scrape(**arguments)
                return [TextContent(
                    type="text",
                    text=json.dumps(result, ensure_ascii=False, indent=2),
                )]

            elif name == "spider_batch":
                urls = arguments.get("urls", [])
                fmt = arguments.get("format", "markdown")
                max_chars = arguments.get("max_chars", 5000)
                results = []
                for url in urls:
                    try:
                        r = await _do_scrape(
                            url=url, format=fmt, max_chars=max_chars
                        )
                        results.append(r)
                    except Exception as e:
                        results.append({
                            "url": url,
                            "status": "failed",
                            "error": str(e),
                        })
                return [TextContent(
                    type="text",
                    text=json.dumps(results, ensure_ascii=False, indent=2),
                )]

            elif name == "spider_query":
                storage = _get_storage()
                if url := arguments.get("url"):
                    rows = storage.get_by_url(url)
                elif domain := arguments.get("domain"):
                    rows = storage.get_by_domain(
                        domain, limit=arguments.get("limit", 10)
                    )
                elif keyword := arguments.get("keyword"):
                    rows = storage.search(
                        keyword, limit=arguments.get("limit", 10)
                    )
                else:
                    rows = storage.recent(limit=arguments.get("limit", 10))

                # 精简输出（不返回完整内容）
                summary = []
                for r in rows:
                    summary.append({
                        "url": r["url"],
                        "title": r.get("title", ""),
                        "domain": r.get("domain", ""),
                        "engine": r.get("engine", ""),
                        "status": r.get("status", ""),
                        "char_count": r.get("char_count", 0),
                        "crawled_at": r.get("crawled_at", ""),
                    })
                return [TextContent(
                    type="text",
                    text=json.dumps(summary, ensure_ascii=False, indent=2),
                )]

            elif name == "spider_screenshot":
                url = arguments["url"]
                wait = arguments.get("wait", 1)
                result = await _do_scrape(
                    url=url, format="markdown", wait=wait, save=False,
                )
                # 截图需要单独处理
                fc = FetchConfig(
                    proxy=_config.proxy if _config.use_proxy else None,
                    timeout=_config.timeout,
                    stealth=_config.stealth,
                    headless=True,
                    wait=wait,
                )
                crawl4ai, _ = await _get_engines()
                r = await crawl4ai.fetch(url, fc)
                if r.screenshot:
                    import base64
                    b64 = base64.b64encode(r.screenshot).decode()
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "url": url,
                            "screenshot_base64": b64,
                            "size_bytes": len(r.screenshot),
                        }),
                    )]
                return [TextContent(
                    type="text",
                    text=json.dumps({"url": url, "error": "截图失败"}),
                )]

            else:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": f"未知 tool: {name}"}),
                )]

        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, ensure_ascii=False),
            )]

    return server


async def main():
    """MCP Server 主入口（stdio 模式）。"""
    server = create_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


# 支持 python3 -m spider.mcp.server 启动
if __name__ == "__main__":
    asyncio.run(main())
