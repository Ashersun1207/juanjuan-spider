#!/bin/bash
# juanjuan-spider 文档自动同步脚本
# 自动更新 status.md 中的统计数据，确保文档不漂移
#
# 用法: bash scripts/sync.sh
# 做的事:
#   1. 统计代码行数、文件数、测试数
#   2. 更新 status.md 统计区域
#   3. 同步到 workspace memory
#   4. 记录时间戳

set -euo pipefail
cd "$(dirname "$0")/.."

echo "=== juanjuan-spider sync ==="

# 收集统计
TEST_COUNT=$(.venv/bin/python3 -m pytest tests/ -q --tb=no 2>&1 | grep -oE "^[0-9]+" | head -1 || echo "0")
TOTAL_LINES=$(find spider/ scrape.py -name "*.py" -not -path "*__pycache__*" -exec cat {} + | wc -l | tr -d ' ')
TEST_LINES=$(find tests/ -name "*.py" -not -path "*__pycache__*" -exec cat {} + | wc -l | tr -d ' ')
PY_FILES=$(find spider/ -name "*.py" -not -name "__pycache__" | wc -l | tr -d ' ')
ADAPTER_COUNT=$(find spider/adapters/ -name "*.py" -not -name "__init__.py" | wc -l | tr -d ' ')
ENGINE_COUNT=$(find spider/engines/ -name "*.py" -not -name "__init__.py" | wc -l | tr -d ' ')
DB_RECORDS=0
if [ -f "storage/spider.db" ]; then
    DB_RECORDS=$(sqlite3 storage/spider.db "SELECT COUNT(*) FROM crawl_results" 2>/dev/null || echo "0")
fi
VERSION=$(sed -n 's/.*__version__.*=.*"\(.*\)".*/\1/p' spider/__init__.py 2>/dev/null || echo "unknown")
GIT_COMMITS=$(git rev-list --count HEAD 2>/dev/null || echo "0")
LAST_COMMIT=$(git log --oneline -1 2>/dev/null || echo "unknown")
NOW=$(date "+%Y-%m-%d %H:%M")

echo "📊 统计:"
echo "  版本: v${VERSION}"
echo "  代码: ${TOTAL_LINES} 行 (${PY_FILES} 文件)"
echo "  测试: ${TEST_COUNT} tests (${TEST_LINES} 行)"
echo "  引擎: ${ENGINE_COUNT} | 适配器: ${ADAPTER_COUNT}"
echo "  存储: ${DB_RECORDS} 条记录"
echo "  Git: ${GIT_COMMITS} commits"
echo ""

# 同步到 workspace memory
MEMORY_FILE="$HOME/.openclaw/workspace/memory/web-scraper-notes.md"
if [ -f "$MEMORY_FILE" ]; then
    # 更新统计区块
    cat > /tmp/spider-stats.md << EOF
## 项目统计（自动同步 ${NOW}）

| 指标 | 值 |
|---|---|
| 版本 | v${VERSION} |
| 代码行数 | ${TOTAL_LINES}（含测试 ${TEST_LINES}） |
| 测试数 | ${TEST_COUNT} |
| 引擎 | ${ENGINE_COUNT} |
| 适配器 | ${ADAPTER_COUNT} |
| 存储记录 | ${DB_RECORDS} |
| Git commits | ${GIT_COMMITS} |
| 最新 commit | ${LAST_COMMIT} |
EOF

    # 如果 memory 文件里有统计区块就替换，没有就追加
    if grep -q "## 项目统计" "$MEMORY_FILE"; then
        # 用 python 替换区块（sed 处理多行替换不靠谱）
        .venv/bin/python3 -c "
import re
from pathlib import Path

mem = Path('$MEMORY_FILE').read_text()
stats = Path('/tmp/spider-stats.md').read_text()

# 替换从 '## 项目统计' 到下一个 '## ' 或文件末尾
pattern = r'## 项目统计.*?(?=\n## |\Z)'
mem = re.sub(pattern, stats.strip(), mem, flags=re.DOTALL)
Path('$MEMORY_FILE').write_text(mem)
"
        echo "✅ workspace memory 已更新"
    else
        echo "" >> "$MEMORY_FILE"
        cat /tmp/spider-stats.md >> "$MEMORY_FILE"
        echo "✅ workspace memory 已追加统计"
    fi
    rm -f /tmp/spider-stats.md
else
    echo "⚠️  memory 文件不存在: $MEMORY_FILE"
fi

# 记录同步时间戳
SYNC_DIR="$HOME/.openclaw/workspace/memory/juanjuan-spider-sync"
mkdir -p "$SYNC_DIR"
date "+%s" > "$SYNC_DIR/.last-sync-ts"
echo "✅ 同步时间戳已记录"

echo ""
echo "=== sync 完成 ==="
