"""允许 python3 -m spider.mcp 启动 MCP Server。"""
from spider.mcp.server import main
import asyncio

asyncio.run(main())
