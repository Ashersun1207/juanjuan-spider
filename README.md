# web-scraper 🕷️

卷卷的通用网页抓取工具，基于 Playwright + Stealth，能绕大部分反爬。

## 安装

```bash
pip3 install playwright playwright-stealth markdownify
python3 -m playwright install chromium
```

## 用法

```bash
# 基本用法（走代理，输出 markdown）
python3 scrape.py "https://example.com"

# 指定选择器只抓表格
python3 scrape.py "https://example.com" --selector "table"

# 截图
python3 scrape.py "https://example.com" -f screenshot -o page.png

# 不走代理
python3 scrape.py "https://example.com" --no-proxy

# 有头模式调试
python3 scrape.py "https://example.com" --headed

# 自动滚动（懒加载页面）
python3 scrape.py "https://example.com" --scroll

# 输出到文件
python3 scrape.py "https://example.com" -o result.md

# 页面加载后执行 JS（比如点击按钮）
python3 scrape.py "https://example.com" --js "document.querySelector('.btn').click()"
```

## 代理

默认走 `http://127.0.0.1:7897`（Clash），用 `--no-proxy` 关闭。

## 反检测

内置 `playwright-stealth`，自动注入指纹伪装：
- 隐藏 navigator.webdriver
- 伪装 Chrome 运行时
- 模拟真实 UA / viewport / timezone
