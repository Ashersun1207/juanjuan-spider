# juanjuan-spider 🕷️

通用网页抓取工具 — 基于 **Crawl4AI** (58K+ ⭐)。

反检测 + 智能去噪 + 多格式输出，覆盖所有需要浏览器渲染的抓取场景。不造轮子，集成成熟项目。

## 安装

```bash
# 需要 Python 3.12+
python3.12 -m venv .venv
source .venv/bin/activate
pip install crawl4ai
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
| `--format fit` | - | Crawl4AI 智能去噪 markdown |
| `--stealth/--no-stealth` | stealth on | 反检测模式 |
| `--verbose` | - | 显示 Crawl4AI 日志 |
| `--scroll` | - | 自动滚动到底部 |
| `--headed` | - | 显示浏览器（调试） |
| `--cookie FILE` | - | Cookie JSON 文件 |
| `--js CODE` | - | 加载后执行的 JS |
| `--max-chars N` | 0（不限） | 输出截断 |
| `--timeout SEC` | 30 | 页面加载超时 |
| `-o FILE` | stdout | 输出文件 |

## 核心能力（来自 Crawl4AI）

- **反检测**：enable_stealth + patchright，指纹轮换，UA 随机化
- **智能去噪**：fit markdown 算法，自动去导航/广告/脚本
- **异步引擎**：底层异步，性能好
- **深度爬取**：支持递归发现子页面（CLI 暂未暴露，可通过 Python API 使用）
- **多格式**：markdown / fit / html / text / screenshot

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

_juanjuan-spider · 卷卷的万能爬虫_
