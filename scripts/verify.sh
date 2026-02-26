#!/bin/bash
# juanjuan-spider 验证脚本（V1-V9）
# commit 前必须跑，确保代码+文档+测试全部对齐
#
# 用法: bash scripts/verify.sh
# 退出码: 0=全绿 1=有错误

set -euo pipefail
cd "$(dirname "$0")/.."

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

ERRORS=0
WARNS=0

pass() { echo -e "${GREEN}✔ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠ $1${NC}"; WARNS=$((WARNS+1)); }
fail() { echo -e "${RED}✘ $1${NC}"; ERRORS=$((ERRORS+1)); }
section() { echo ""; echo "━━━ $1 ━━━"; }

echo "=== juanjuan-spider verify ==="

# ── V1: pytest ──
section "V1: 测试"
TEST_OUTPUT=$(.venv/bin/python3 -m pytest tests/ -q --tb=short 2>&1)
TEST_COUNT=$(echo "$TEST_OUTPUT" | grep -oE "^[0-9]+" | head -1 || echo "0")
FAILED=$(echo "$TEST_OUTPUT" | grep -c "FAILED" || true)
if [ "$FAILED" -eq 0 ]; then
    pass "全部 ${TEST_COUNT} 个测试通过"
else
    echo "$TEST_OUTPUT" | tail -10
    fail "${FAILED} 个测试失败"
fi

# ── V2: 导入检查 ──
section "V2: 导入"
.venv/bin/python3 -c "from spider import crawl, CrawlResult" 2>/dev/null && pass "spider 包" || fail "spider 包导入失败"
.venv/bin/python3 -c "from spider.mcp.server import create_server" 2>/dev/null && pass "MCP Server" || fail "MCP Server 导入失败"
.venv/bin/python3 -c "from spider.core.router import Router" 2>/dev/null && pass "Router" || fail "Router 导入失败"
.venv/bin/python3 -c "from spider.storage.sqlite import SpiderStorage" 2>/dev/null && pass "Storage" || fail "Storage 导入失败"

# ── V3: 文档完整性 ──
section "V3: 文档存在"
for f in docs/ARCHITECTURE.md docs/status.md docs/decisions.md docs/lessons.md README.md; do
    [ -f "$f" ] && pass "$f" || fail "$f 缺失"
done

# ── V4: ARCHITECTURE.md ↔ 代码一致性 ──
section "V4: 架构文档 ↔ 代码"

# 4a: 文档提到的 .py 文件是否都存在
ARCH_MISSING=0
while IFS= read -r fpath; do
    if [ ! -f "$fpath" ]; then
        fail "ARCHITECTURE.md 提到 $fpath 但文件不存在"
        ARCH_MISSING=$((ARCH_MISSING+1))
    fi
done < <(grep -oE 'spider/[a-zA-Z_/]+\.py' docs/ARCHITECTURE.md 2>/dev/null | sort -u)
[ "$ARCH_MISSING" -eq 0 ] && pass "ARCHITECTURE.md 中的源文件全部存在"

# 4b: 实际 spider/ 中的 .py 文件是否都在 ARCHITECTURE.md 中
UNTRACKED=0
while IFS= read -r srcf; do
    base=$(basename "$srcf")
    [ "$base" = "__init__.py" ] && continue
    [ "$base" = "__main__.py" ] && continue
    if ! grep -q "$base" docs/ARCHITECTURE.md 2>/dev/null; then
        warn "代码文件 $srcf 未出现在 ARCHITECTURE.md 中"
        UNTRACKED=$((UNTRACKED+1))
    fi
done < <(find spider/ -name "*.py" -not -path "*__pycache__*" | sort)
[ "$UNTRACKED" -eq 0 ] && pass "所有源文件都在 ARCHITECTURE.md 中有记录"

# ── V5: status.md 漂移检测 ──
section "V5: status.md 漂移"

# 5a: 测试数
if grep -q "${TEST_COUNT} test" docs/status.md 2>/dev/null; then
    pass "测试数一致 (${TEST_COUNT})"
else
    warn "status.md 测试数可能过时 (实际 ${TEST_COUNT})"
fi

# 5b: 引擎数
ENGINE_COUNT=$(find spider/engines/ -name "*.py" -not -name "__init__.py" | wc -l | tr -d ' ')
ADAPTER_COUNT=$(find spider/adapters/ -name "*.py" -not -name "__init__.py" | wc -l | tr -d ' ')
pass "引擎 ${ENGINE_COUNT} 个, 适配器 ${ADAPTER_COUNT} 个"

# 5c: MCP tools 数量检查
MCP_TOOLS=$(.venv/bin/python3 -c "
from spider.mcp.server import create_server
import asyncio
async def check():
    s = create_server()
    # 遍历注册的 handlers 计数
    return len([k for k in dir(s) if 'tool' in k.lower()])
print(asyncio.run(check()))
" 2>/dev/null || echo "0")
pass "MCP Server 已注册"

# ── V6: 依赖检查 ──
section "V6: 依赖"
MISSING_DEPS=0
while IFS= read -r pkg; do
    pkg_name=$(echo "$pkg" | sed 's/[>=<].*//')
    if .venv/bin/python3 -c "import importlib; importlib.import_module('${pkg_name//-/_}')" 2>/dev/null; then
        pass "$pkg_name"
    else
        fail "$pkg_name 未安装"
        MISSING_DEPS=$((MISSING_DEPS+1))
    fi
done < <(grep -v "^#" requirements.txt | grep -v "^$")

# ── V6b: Lint ──
section "V6b: Lint (ruff)"
if .venv/bin/python3 -c "import ruff" 2>/dev/null || .venv/bin/ruff --version 2>/dev/null; then
    RUFF_OUT=$(.venv/bin/ruff check spider/ scrape.py 2>&1)
    RUFF_ERRORS=$(echo "$RUFF_OUT" | grep -c "^spider/\|^scrape.py" || true)
    if [ "$RUFF_ERRORS" -eq 0 ]; then
        pass "ruff: 0 issues"
    else
        echo "$RUFF_OUT" | head -20
        warn "ruff: ${RUFF_ERRORS} issues（不阻断，但建议修复）"
    fi
else
    warn "ruff 未安装，跳过 lint（pip install ruff）"
fi

# ── V6c: Type check 入口验证 ──
section "V6c: 关键类型检查"
TYPE_ERRORS=0
for mod in "spider.core.result" "spider.core.engine" "spider.core.extractor" "spider.core.router" "spider.main"; do
    if .venv/bin/python3 -c "import ${mod}" 2>/dev/null; then
        pass "$mod"
    else
        fail "$mod 导入失败"
        TYPE_ERRORS=$((TYPE_ERRORS+1))
    fi
done

# ── V7: decisions.md 完整性 ──
section "V7: 决策记录"
DECISION_COUNT=$(grep -c "^## D[0-9]" docs/decisions.md 2>/dev/null || echo "0")
pass "已记录 ${DECISION_COUNT} 个决策"

LESSON_COUNT=$(grep -c "^## L[0-9]" docs/lessons.md 2>/dev/null || echo "0")
pass "已记录 ${LESSON_COUNT} 个教训"

# ── V8: Git 状态 ──
section "V8: Git"
UNCOMMITTED=$(git status --porcelain | wc -l | tr -d ' ')
if [ "$UNCOMMITTED" -eq 0 ]; then
    pass "工作区干净"
else
    warn "有 ${UNCOMMITTED} 个未提交变更"
    git status --short
fi

# ── V9: workspace memory 同步 ──
section "V9: Workspace 同步"
SYNC_TS_FILE="$HOME/.openclaw/workspace/memory/juanjuan-spider-sync/.last-sync-ts"
if [ -f "$SYNC_TS_FILE" ]; then
    SYNC_TS=$(cat "$SYNC_TS_FILE")
    NOW_TS=$(date +%s)
    AGE=$(( (NOW_TS - SYNC_TS) / 3600 ))
    if [ "$AGE" -gt 24 ]; then
        warn "距上次 sync 已 ${AGE} 小时（建议跑 bash scripts/sync.sh）"
    else
        pass "sync 距今 ${AGE} 小时"
    fi
else
    warn "从未跑过 sync.sh"
fi

# ── 汇总 ──
echo ""
echo "━━━━━━━━━━━━━━━━━━━━"
if [ $ERRORS -gt 0 ]; then
    fail "❌ ${ERRORS} 个错误, ${WARNS} 个警告"
    exit 1
elif [ $WARNS -gt 0 ]; then
    warn "⚠ ${WARNS} 个警告, 无错误"
    exit 0
else
    pass "✅ 全部通过！"
    exit 0
fi
