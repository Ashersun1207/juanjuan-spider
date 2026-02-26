#!/usr/bin/env python3
"""
通用网页抓取工具 — Playwright + Stealth
用法:
  python3 scrape.py <URL> [选项]

选项:
  --proxy URL        代理地址（默认 http://127.0.0.1:7897）
  --no-proxy         不使用代理
  --wait SEC         页面加载后额外等待秒数（默认 3）
  --selector CSS     只抓取匹配的 CSS 选择器内容
  --output FILE      输出到文件（默认 stdout）
  --format FMT       输出格式: markdown(默认) / html / text / screenshot
  --scroll           自动滚动到底部（加载懒加载内容）
  --headless         无头模式（默认，不显示浏览器）
  --headed           有头模式（调试用，显示浏览器）
  --cookie FILE      加载 cookie JSON 文件
  --js CODE          页面加载后执行的 JS 代码
"""

import argparse
import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from markdownify import markdownify as md

# stealth 实例
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
    p.add_argument("--scroll", action="store_true", help="自动滚动加载")
    p.add_argument("--headed", action="store_true", help="有头模式（显示浏览器）")
    p.add_argument("--cookie", help="Cookie JSON 文件路径")
    p.add_argument("--js", help="页面加载后执行的 JS")
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


def main():
    args = parse_args()

    with sync_playwright() as p:
        # 浏览器启动参数
        launch_opts = {
            "headless": not args.headed,
        }
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

        # 加载 cookie
        if args.cookie:
            cookie_path = Path(args.cookie)
            if cookie_path.exists():
                cookies = json.loads(cookie_path.read_text())
                context.add_cookies(cookies)

        page = context.new_page()
        _stealth.apply_stealth_sync(page)  # 注入反检测

        # 导航
        try:
            page.goto(args.url, timeout=args.timeout * 1000,
                      wait_until="networkidle")
        except Exception as e:
            # networkidle 超时时降级尝试
            try:
                page.goto(args.url, timeout=args.timeout * 1000,
                          wait_until="domcontentloaded")
            except Exception as e2:
                print(f"❌ 页面加载失败: {e2}", file=sys.stderr)
                browser.close()
                sys.exit(1)

        # 额外等待
        if args.wait > 0:
            time.sleep(args.wait)

        # 执行自定义 JS
        if args.js:
            page.evaluate(args.js)
            time.sleep(1)

        # 自动滚动
        if args.scroll:
            auto_scroll(page)
            time.sleep(2)

        # 截图模式
        if args.format == "screenshot":
            out_path = args.output or "screenshot.png"
            page.screenshot(path=out_path, full_page=True)
            print(f"✅ 截图已保存: {out_path}", file=sys.stderr)
            browser.close()
            return

        # 获取内容
        if args.selector:
            elements = page.query_selector_all(args.selector)
            html_parts = [el.inner_html() for el in elements]
            html = "\n".join(html_parts)
        else:
            # 尝试智能提取主内容区域，去掉导航/广告/脚本
            main_selectors = [
                "main", "article", "#content", ".content",
                "#main-content", ".main-content", "[role='main']"
            ]
            html = None
            for sel in main_selectors:
                el = page.query_selector(sel)
                if el:
                    html = el.inner_html()
                    break
            if not html:
                # fallback: 抓 body 但去掉 script/style/nav/header/footer
                html = page.evaluate("""() => {
                    const clone = document.body.cloneNode(true);
                    clone.querySelectorAll(
                        'script, style, noscript, nav, header, footer, ' +
                        '.nav, .navbar, .sidebar, .ad, .ads, .advertisement, ' +
                        '[role="navigation"], [role="banner"]'
                    ).forEach(el => el.remove());
                    return clone.innerHTML;
                }""")

        browser.close()

        # 格式化输出
        if args.format == "html":
            result = html
        elif args.format == "text":
            # 简单去标签
            from markdownify import markdownify
            result = markdownify(html, strip=["img", "script", "style"])
            # 去除多余空行
            lines = [l.strip() for l in result.split("\n")]
            result = "\n".join(l for l in lines if l)
        else:  # markdown
            result = md(html, strip=["script", "style"])
            # 清理多余空行
            lines = result.split("\n")
            cleaned = []
            blank_count = 0
            for line in lines:
                if line.strip() == "":
                    blank_count += 1
                    if blank_count <= 2:
                        cleaned.append("")
                else:
                    blank_count = 0
                    cleaned.append(line)
            result = "\n".join(cleaned)

        # 输出
        if args.output:
            Path(args.output).write_text(result, encoding="utf-8")
            print(f"✅ 已保存: {args.output}", file=sys.stderr)
        else:
            print(result)


if __name__ == "__main__":
    main()
