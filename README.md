# web-scraper 🕷️

GainLab 生态的网页抓取工具 — Playwright + Stealth + Readability。

专注金融场景：抓取 FMP/EODHD API 覆盖不到的数据（财经新闻、EA 实盘、研报正文）。

## 安装

```bash
pip3 install playwright playwright-stealth markdownify readability-lxml
python3 -m playwright install chromium
```

## 用法

```bash
# 基本用法（走代理，输出 markdown）
python3 scrape.py "https://example.com"

# 不走代理（国内站点）
python3 scrape.py "https://example.com" --no-proxy

# 指定选择器只抓表格
python3 scrape.py "https://myfxbook.com/..." --selector "table"

# 截图
python3 scrape.py "https://example.com" -f screenshot -o page.png

# 跳过 Readability，输出原始内容
python3 scrape.py "https://example.com" --raw

# 自动滚动（懒加载页面）+ 限制输出长度
python3 scrape.py "https://example.com" --scroll --max-chars 5000

# 有头模式调试
python3 scrape.py "https://example.com" --headed

# 输出到文件
python3 scrape.py "https://example.com" -o result.md

# 页面加载后执行 JS
python3 scrape.py "https://example.com" --js "document.querySelector('.btn').click()"

# 加载 Cookie
python3 scrape.py "https://example.com" --cookie cookies.json
```

## 参数

| 参数 | 默认值 | 说明 |
|---|---|---|
| `--proxy URL` | `http://127.0.0.1:7897` | 代理地址 |
| `--no-proxy` | - | 不使用代理 |
| `--wait SEC` | 3 | 页面加载后额外等待 |
| `--selector CSS` | - | 只抓匹配的元素 |
| `--format FMT` | markdown | markdown / html / text / screenshot |
| `--raw` | - | 跳过 Readability 提取 |
| `--scroll` | - | 自动滚动到底部 |
| `--headed` | - | 显示浏览器（调试） |
| `--cookie FILE` | - | Cookie JSON 文件 |
| `--js CODE` | - | 加载后执行的 JS |
| `--max-chars N` | 0（不限） | 输出截断 |
| `--timeout SEC` | 30 | 页面加载超时 |
| `-o FILE` | stdout | 输出文件 |

## 反检测

内置 `playwright-stealth`：
- 隐藏 `navigator.webdriver`
- 伪装 Chrome 运行时
- 模拟真实 UA / viewport / timezone

## 正文提取

默认使用 Mozilla Readability 算法（Firefox 阅读模式同款），自动去除导航、广告、侧边栏，只保留正文。用 `--raw` 跳过。

## 文档

- [架构](docs/ARCHITECTURE.md)
- [状态](docs/status.md)
- [决策记录](docs/decisions.md)
- [经验教训](docs/lessons.md)

## 项目认知恢复

```bash
bash scripts/project-boot.sh
```

---

_GainLab 生态 · 非独立产品_
