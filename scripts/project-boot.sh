#!/bin/bash
# web-scraper 项目认知恢复脚本
# 新会话开工前跑一次，快速了解项目状态

set -euo pipefail
cd "$(dirname "$0")/.."

echo "=== juanjuan-spider 项目状态 ==="
echo ""

echo "📁 项目位置: $(pwd)"
echo "📦 Git 状态:"
git log --oneline -5
echo ""
git status --short
echo ""

echo "🔧 依赖版本:"
pip3 show playwright playwright-stealth readability-lxml markdownify 2>/dev/null | grep -E "^(Name|Version):" || echo "  ⚠️ 部分依赖未安装"
echo ""

echo "📄 文档:"
for f in docs/ARCHITECTURE.md docs/status.md docs/decisions.md docs/lessons.md; do
  if [ -f "$f" ]; then
    echo "  ✅ $f"
  else
    echo "  ❌ $f (缺失)"
  fi
done
echo ""

echo "🧪 快速验证（抓 example.com）:"
python3 scrape.py "https://example.com" --no-proxy --max-chars 200 --timeout 15 >/dev/null 2>&1 && echo "  ✅ 抓取正常" || echo "  ❌ 抓取异常"

echo ""
echo "=== 完成 ==="
