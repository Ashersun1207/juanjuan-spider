#!/usr/bin/env python3
"""
通用网页抓取工具 — 基于 Crawl4AI
用法:
  python3 scrape.py <URL> [选项]

选项:
  --proxy URL        代理地址（默认 http://127.0.0.1:7897）
  --no-proxy         不使用代理
  --wait SEC         页面加载后额外等待秒数（默认 0）
  --selector CSS     只抓取匹配的 CSS 选择器内容
  --output FILE      输出到文件（默认 stdout）
  --format FMT       输出格式: markdown(默认) / html / text / screenshot / fit
  --scroll           自动滚动到底部（加载懒加载内容）
  --headed           有头模式（调试用，显示浏览器）
  --cookie FILE      加载 cookie JSON 文件
  --js CODE          页面加载后执行的 JS 代码
  --max-chars N      输出最大字符数（截断）
  --timeout SEC      页面加载超时秒数（默认 30）
  --stealth          启用反检测模式（默认开启）
  --no-stealth       关闭反检测模式
  --verbose          显示 Crawl4AI 日志
"""

import argparse
import asyncio
import json
import os
import sys
import warnings
from pathlib import Path

# 抑制无关警告
warnings.filterwarnings("ignore", category=UserWarning)
os.environ.setdefault("CRAWL4AI_LOG_LEVEL", "ERROR")


def parse_args():
    p = argparse.ArgumentParser(description="通用网页抓取工具（Crawl4AI）")
    p.add_argument("url", help="目标 URL")
    p.add_argument("--proxy", default="http://127.0.0.1:7897", help="代理地址")
    p.add_argument("--no-proxy", action="store_true", help="不使用代理")
    p.add_argument("--wait", type=float, default=0, help="额外等待秒数")
    p.add_argument("--selector", help="CSS 选择器，只抓匹配内容")
    p.add_argument("--output", "-o", help="输出文件路径")
    p.add_argument("--format", "-f", default="markdown",
                   choices=["markdown", "html", "text", "screenshot", "fit"],
                   help="输出格式（fit=Crawl4AI 智能去噪 markdown）")
    p.add_argument("--scroll", action="store_true", help="自动滚动加载")
    p.add_argument("--headed", action="store_true", help="有头模式")
    p.add_argument("--cookie", help="Cookie JSON 文件路径")
    p.add_argument("--js", help="页面加载后执行的 JS")
    p.add_argument("--max-chars", type=int, default=0,
                   help="输出最大字符数（0=不限）")
    p.add_argument("--timeout", type=int, default=30, help="页面加载超时秒数")
    p.add_argument("--stealth", action="store_true", default=True,
                   help="启用反检测（默认）")
    p.add_argument("--no-stealth", dest="stealth", action="store_false",
                   help="关闭反检测")
    p.add_argument("--verbose", action="store_true", help="显示详细日志")
    return p.parse_args()


async def run(args):
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

    # 浏览器配置
    browser_kwargs = {
        "headless": not args.headed,
        "enable_stealth": args.stealth,
        "verbose": args.verbose,
    }
    if not args.no_proxy:
        browser_kwargs["proxy"] = args.proxy

    bc = BrowserConfig(**browser_kwargs)

    # 爬取配置
    run_kwargs = {
        "page_timeout": args.timeout * 1000,
        "verbose": args.verbose,
    }
    if args.selector:
        run_kwargs["css_selector"] = args.selector
    if args.wait > 0:
        run_kwargs["delay_before_return_html"] = args.wait
    if args.scroll:
        run_kwargs["scan_full_page"] = True
    if args.js:
        run_kwargs["js_code"] = args.js

    rc = CrawlerRunConfig(**run_kwargs)

    async with AsyncWebCrawler(config=bc) as crawler:
        # Cookie 注入
        if args.cookie:
            cookie_path = Path(args.cookie)
            if cookie_path.exists():
                cookies = json.loads(cookie_path.read_text())
                # Crawl4AI 支持通过 browser context 注入 cookies
                if hasattr(crawler, 'crawler_strategy') and crawler.crawler_strategy:
                    ctx = getattr(crawler.crawler_strategy, 'browser_context', None)
                    if ctx:
                        await ctx.add_cookies(cookies)

        result = await crawler.arun(url=args.url, config=rc)

        if not result.success:
            print(f"❌ 抓取失败: {result.error_message}", file=sys.stderr)
            sys.exit(1)

        # 截图
        if args.format == "screenshot":
            if result.screenshot:
                import base64
                out_path = args.output or "screenshot.png"
                img_data = base64.b64decode(result.screenshot)
                Path(out_path).write_bytes(img_data)
                print(f"✅ 截图已保存: {out_path}", file=sys.stderr)
            else:
                print("❌ 截图失败", file=sys.stderr)
                sys.exit(1)
            return

        # 选择输出格式
        if args.format == "html":
            output = result.html or ""
        elif args.format == "fit":
            output = ""
            if result.markdown:
                output = result.markdown.fit_markdown or result.markdown.raw_markdown or ""
        elif args.format == "text":
            md = ""
            if result.markdown:
                md = result.markdown.raw_markdown or ""
            # 简单去除 markdown 标记
            import re
            output = re.sub(r'!?\[([^\]]*)\]\([^)]+\)', r'\1', md)
            output = re.sub(r'[#*_`~]', '', output)
        else:  # markdown（默认）
            output = ""
            if result.markdown:
                output = result.markdown.raw_markdown or ""

        # 截断
        if args.max_chars > 0 and len(output) > args.max_chars:
            output = output[:args.max_chars] + f"\n\n... (截断于 {args.max_chars} 字符)"

        # 输出
        if args.output:
            Path(args.output).write_text(output, encoding="utf-8")
            print(f"✅ 已保存: {args.output} ({len(output)} 字符)",
                  file=sys.stderr)
        else:
            print(output)


def main():
    args = parse_args()
    if not args.verbose:
        os.environ["CRAWL4AI_LOG_LEVEL"] = "ERROR"
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
