#!/usr/bin/env python3
"""
juanjuan-spider CLI 🕷️

用法:
  python3 scrape.py <URL> [选项]

选项:
  --proxy URL        代理地址（默认 http://127.0.0.1:7897）
  --no-proxy         不使用代理
  --wait SEC         页面加载后额外等待秒数
  --selector CSS     只抓取匹配的 CSS 选择器内容
  --output FILE      输出到文件（默认 stdout）
  --format FMT       输出格式: markdown / html / text / screenshot / fit
  --scroll           自动滚动到底部
  --headed           有头模式（调试用）
  --cookie FILE      加载 cookie JSON 文件
  --js CODE          页面加载后执行的 JS 代码
  --max-chars N      输出最大字符数
  --timeout SEC      页面加载超时秒数（默认 30）
  --stealth          启用反检测（默认）
  --no-stealth       关闭反检测
  --save             保存到本地存储（SQLite + markdown 文件）
  --no-cache         忽略缓存，强制重抓
  --verbose          显示详细日志
"""

import argparse
import asyncio
import os
import re
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=UserWarning)
os.environ.setdefault("CRAWL4AI_LOG_LEVEL", "ERROR")


def parse_args():
    p = argparse.ArgumentParser(description="juanjuan-spider 🕷️ 通用网页抓取")
    p.add_argument("url", help="目标 URL")
    p.add_argument("--proxy", default="http://127.0.0.1:7897")
    p.add_argument("--no-proxy", action="store_true")
    p.add_argument("--wait", type=float, default=0)
    p.add_argument("--selector")
    p.add_argument("--output", "-o")
    p.add_argument("--format", "-f", default="markdown",
                   choices=["markdown", "html", "text", "screenshot", "fit"])
    p.add_argument("--scroll", action="store_true")
    p.add_argument("--headed", action="store_true")
    p.add_argument("--cookie")
    p.add_argument("--js")
    p.add_argument("--max-chars", type=int, default=0)
    p.add_argument("--timeout", type=int, default=30)
    p.add_argument("--stealth", action="store_true", default=True)
    p.add_argument("--no-stealth", dest="stealth", action="store_false")
    p.add_argument("--save", action="store_true", help="保存到本地存储")
    p.add_argument("--no-cache", action="store_true", help="忽略缓存强制重抓")
    p.add_argument("--verbose", action="store_true")
    return p.parse_args()


async def run(args):
    from spider.core.engine import FetchConfig
    from spider.main import crawl

    fc = FetchConfig(
        proxy=args.proxy if not args.no_proxy else None,
        timeout=args.timeout,
        stealth=args.stealth,
        headless=not args.headed,
        wait=args.wait,
        scroll=args.scroll,
        selector=args.selector,
        js_code=args.js,
        cookie_file=args.cookie,
        verbose=args.verbose,
    )

    result = await crawl(
        args.url,
        save=args.save,
        no_cache=args.no_cache,
        fetch_config=fc,
    )

    if result.status == "failed":
        print(f"❌ 抓取失败: {result.error}", file=sys.stderr)
        sys.exit(1)

    if result.status == "cached":
        print("📦 命中缓存", file=sys.stderr)

    # 截图
    if args.format == "screenshot":
        if result.screenshot:
            out_path = args.output or "screenshot.png"
            Path(out_path).write_bytes(result.screenshot)
            print(f"✅ 截图已保存: {out_path}", file=sys.stderr)
        else:
            print("❌ 截图失败", file=sys.stderr)
            sys.exit(1)
        return

    # 选择输出内容
    if args.format == "html":
        output = result.html
    elif args.format == "fit":
        output = result.fit_markdown or result.markdown
    elif args.format == "text":
        output = re.sub(r'!?\[([^\]]*)\]\([^)]+\)', r'\1', result.markdown)
        output = re.sub(r'[#*_`~]', '', output)
    else:
        output = result.markdown

    # 截断
    if args.max_chars > 0 and len(output) > args.max_chars:
        output = output[:args.max_chars] + f"\n\n... (截断于 {args.max_chars} 字符)"

    # 输出
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"✅ 已保存: {args.output} ({len(output)} 字符)", file=sys.stderr)
    else:
        print(output)

    # 打印元信息
    if args.verbose:
        print(f"\n--- 元信息 ---", file=sys.stderr)
        print(f"引擎: {result.engine}", file=sys.stderr)
        print(f"状态: {result.status}", file=sys.stderr)
        print(f"耗时: {result.duration_ms}ms", file=sys.stderr)
        print(f"字符数: {result.char_count}", file=sys.stderr)
        print(f"域名: {result.domain}", file=sys.stderr)
        print(f"内容哈希: {result.content_hash}", file=sys.stderr)


def main():
    args = parse_args()
    if not args.verbose:
        os.environ["CRAWL4AI_LOG_LEVEL"] = "ERROR"
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
