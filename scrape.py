#!/usr/bin/env python3
"""
通用网页抓取工具 — Playwright + Stealth + Readability
用法:
  python3 scrape.py <URL> [选项]

选项:
  --proxy URL        代理地址（默认 http://127.0.0.1:7897）
  --no-proxy         不使用代理
  --wait SEC         页面加载后额外等待秒数（默认 3）
  --selector CSS     只抓取匹配的 CSS 选择器内容
  --output FILE      输出到文件（默认 stdout）
  --format FMT       输出格式: markdown(默认) / html / text / screenshot
  --raw              跳过 readability 提取，输出原始页面内容
  --scroll           自动滚动到底部（加载懒加载内容）
  --headed           有头模式（调试用，显示浏览器）
  --cookie FILE      加载 cookie JSON 文件
  --js CODE          页面加载后执行的 JS 代码
  --max-chars N      输出最大字符数（截断）
  --timeout SEC      页面加载超时秒数（默认 30）
"""

import argparse
import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from markdownify import markdownify as md

# readability
try:
    from readability import Document as ReadabilityDocument
    HAS_READABILITY = True
except ImportError:
    HAS_READABILITY = False

_stealth = Stealth()


def parse_args():
    p = argparse.ArgumentParser(description="通用网页抓取工具")
    p.add_argument("url", help="目标 URL")
    p.add_argument("--proxy", default="http://127.0.0.1:7897", help="代理地址")
    p.add_argument("--no-proxy", action="store_true", help="不使用代理")
    p.add_argument("--wait", type=float, default=3, help="额外等待秒数")
    p.add_argument("--selector", help="CSS 选择器，只抓匹配内容")
    p.add_argument("--output", "-o", help="输出文件路径")
    p.add_argument("--format", "-f", default="markdown",
                   choices=["markdown", "html", "text", "screenshot"],
                   help="输出格式")
    p.add_argument("--raw", action="store_true",
                   help="跳过 readability，输出原始内容")
    p.add_argument("--scroll", action="store_true", help="自动滚动加载")
    p.add_argument("--headed", action="store_true", help="有头模式")
    p.add_argument("--cookie", help="Cookie JSON 文件路径")
    p.add_argument("--js", help="页面加载后执行的 JS")
    p.add_argument("--max-chars", type=int, default=0,
                   help="输出最大字符数（0=不限）")
    p.add_argument("--timeout", type=int, default=30, help="页面加载超时秒数")
    return p.parse_args()


def auto_scroll(page):
    """模拟人类滚动，触发懒加载"""
    page.evaluate("""
        async () => {
            await new Promise((resolve) => {
                let totalHeight = 0;
                const distance = 300;
                const timer = setInterval(() => {
                    window.scrollBy(0, distance);
                    totalHeight += distance;
                    if (totalHeight >= document.body.scrollHeight) {
                        clearInterval(timer);
                        resolve();
                    }
                }, 200);
            });
        }
    """)


def extract_with_readability(html, url=""):
    """用 readability 提取正文，去掉导航/广告/脚本"""
    if not HAS_READABILITY:
        return html
    try:
        doc = ReadabilityDocument(html, url=url)
        return doc.summary()
    except Exception:
        return html


def clean_markdown(text):
    """清理 markdown 输出：去多余空行、去残留 CSS/JS 片段"""
    lines = text.split("\n")
    cleaned = []
    blank_count = 0
    for line in lines:
        stripped = line.strip()
        # 跳过明显的 CSS/JS 残留
        if any(kw in stripped for kw in [
            "googletag", "function()", "window.", "var ", "const ",
            "let ", ".push(", "border:", "margin:", "padding:",
            "font-", "background:", "display:", "position:",
            "overflow:", "rgba(", "progid:", "webkit", "-ms-",
            "-moz-", "sentinel{", "jqstooltip", ".css",
        ]):
            continue
        if stripped == "":
            blank_count += 1
            if blank_count <= 1:
                cleaned.append("")
        else:
            blank_count = 0
            cleaned.append(line)
    return "\n".join(cleaned).strip()


def main():
    args = parse_args()

    with sync_playwright() as p:
        launch_opts = {"headless": not args.headed}
        if not args.no_proxy:
            launch_opts["proxy"] = {"server": args.proxy}

        browser = p.chromium.launch(**launch_opts)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
        )

        if args.cookie:
            cookie_path = Path(args.cookie)
            if cookie_path.exists():
                cookies = json.loads(cookie_path.read_text())
                context.add_cookies(cookies)

        page = context.new_page()
        _stealth.apply_stealth_sync(page)

        # 导航（networkidle 优先，超时降级 domcontentloaded）
        try:
            page.goto(args.url, timeout=args.timeout * 1000,
                      wait_until="networkidle")
        except Exception:
            try:
                page.goto(args.url, timeout=args.timeout * 1000,
                          wait_until="domcontentloaded")
            except Exception as e2:
                print(f"❌ 页面加载失败: {e2}", file=sys.stderr)
                browser.close()
                sys.exit(1)

        if args.wait > 0:
            time.sleep(args.wait)

        if args.js:
            page.evaluate(args.js)
            time.sleep(1)

        if args.scroll:
            auto_scroll(page)
            time.sleep(2)

        # 截图
        if args.format == "screenshot":
            out_path = args.output or "screenshot.png"
            page.screenshot(path=out_path, full_page=True)
            print(f"✅ 截图已保存: {out_path}", file=sys.stderr)
            browser.close()
            return

        # 获取 HTML
        if args.selector:
            elements = page.query_selector_all(args.selector)
            html = "\n".join(el.inner_html() for el in elements)
        else:
            html = page.content()

        browser.close()

        # readability 正文提取（除非 --raw 或 --selector）
        if not args.raw and not args.selector and HAS_READABILITY:
            html = extract_with_readability(html, url=args.url)

        # 格式化
        if args.format == "html":
            result = html
        elif args.format == "text":
            result = md(html, strip=["img", "script", "style"])
            result = clean_markdown(result)
        else:  # markdown
            result = md(html, strip=["script", "style"])
            result = clean_markdown(result)

        # 截断
        if args.max_chars > 0 and len(result) > args.max_chars:
            result = result[:args.max_chars] + "\n\n... (截断于 %d 字符)" % args.max_chars

        # 输出
        if args.output:
            Path(args.output).write_text(result, encoding="utf-8")
            print(f"✅ 已保存: {args.output} ({len(result)} 字符)",
                  file=sys.stderr)
        else:
            print(result)


if __name__ == "__main__":
    main()
