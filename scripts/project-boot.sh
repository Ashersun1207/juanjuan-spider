#!/bin/bash
# juanjuan-spider 项目认知恢复 + 状态验证
# 新会话开工前跑一次
#
# 用法: bash ~/Desktop/卷卷/juanjuan-spider/scripts/project-boot.sh

set -euo pipefail
cd "$(dirname "$0")/.."

echo "=== 🕷️ juanjuan-spider 项目启动 ==="
echo ""

# 基本信息
echo "📁 项目: $(pwd)"
VERSION=$(sed -n 's/.*__version__.*=.*"\(.*\)".*/\1/p' spider/__init__.py 2>/dev/null || echo "?")
echo "📦 版本: v${VERSION}"
echo ""

# Git
echo "📝 最近 commits:"
git log --oneline -5
echo ""
UNCOMMITTED=$(git status --porcelain | wc -l | tr -d ' ')
if [ "$UNCOMMITTED" -gt 0 ]; then
    echo "⚠️  ${UNCOMMITTED} 个未提交变更:"
    git status --short
    echo ""
fi

# 快速验证
echo "🧪 测试:"
.venv/bin/python3 -m pytest tests/ -q --tb=line 2>&1 | tail -3
echo ""

# 统计
TOTAL_LINES=$(find spider/ scrape.py -name "*.py" -not -path "*__pycache__*" -exec cat {} + | wc -l | tr -d ' ')
echo "📊 代码: ${TOTAL_LINES} 行"

if [ -f "storage/spider.db" ]; then
    DB_RECORDS=$(sqlite3 storage/spider.db "SELECT COUNT(*) FROM crawl_results" 2>/dev/null || echo "0")
    echo "💾 存储: ${DB_RECORDS} 条记录"
fi

echo ""
echo "📄 文档:"
for f in docs/status.md docs/decisions.md docs/lessons.md docs/ARCHITECTURE.md; do
    [ -f "$f" ] && echo "  ✅ $f" || echo "  ❌ $f"
done

echo ""
echo "🔗 关键路径:"
echo "  CLI:  python3 scrape.py <URL> [--save] [--format fit]"
echo "  API:  from spider import crawl"
echo "  MCP:  python3 -m spider.mcp.server"
echo "  验证: bash scripts/verify.sh"
echo "  同步: bash scripts/sync.sh"

echo ""
echo "=== 启动完成 ==="
