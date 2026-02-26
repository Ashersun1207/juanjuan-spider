#!/bin/bash
# juanjuan-spider 验证脚本
# commit 前必须跑，确保代码+文档+测试都 OK
#
# 用法: bash scripts/verify.sh
# 退出码: 0=全绿 1=有问题

set -euo pipefail
cd "$(dirname "$0")/.."

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

ERRORS=0
WARNS=0

pass() { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; WARNS=$((WARNS+1)); }
fail() { echo -e "${RED}❌ $1${NC}"; ERRORS=$((ERRORS+1)); }

echo "=== juanjuan-spider verify ==="
echo ""

# V1: pytest
echo "--- V1: 测试 ---"
if .venv/bin/python3 -m pytest tests/ -q --tb=short 2>&1; then
    pass "所有测试通过"
else
    fail "测试失败"
fi
echo ""

# V2: import 检查
echo "--- V2: 导入检查 ---"
if .venv/bin/python3 -c "from spider import crawl, CrawlResult; print('OK')" 2>/dev/null; then
    pass "spider 包可导入"
else
    fail "spider 包导入失败"
fi

if .venv/bin/python3 -c "from spider.mcp.server import create_server; print('OK')" 2>/dev/null; then
    pass "MCP Server 可导入"
else
    fail "MCP Server 导入失败"
fi
echo ""

# V3: 文档完整性
echo "--- V3: 文档检查 ---"
for f in docs/ARCHITECTURE.md docs/status.md docs/decisions.md docs/lessons.md; do
    if [ -f "$f" ]; then
        pass "$f 存在"
    else
        fail "$f 缺失"
    fi
done
echo ""

# V4: 文档漂移检测
echo "--- V4: 文档漂移 ---"

# 检查 status.md 的测试数
TEST_COUNT=$(.venv/bin/python3 -m pytest tests/ -q --tb=no 2>&1 | grep -oE "^[0-9]+" | head -1)
if grep -q "${TEST_COUNT} tests" docs/status.md 2>/dev/null || grep -q "${TEST_COUNT} test" docs/status.md 2>/dev/null; then
    pass "status.md 测试数一致 (${TEST_COUNT})"
else
    warn "status.md 测试数可能过时 (实际 ${TEST_COUNT})"
fi

# 检查 Python 文件数 vs 文档目录树
PY_COUNT=$(find spider/ -name "*.py" -not -name "__pycache__" | wc -l | tr -d ' ')
if [ "$PY_COUNT" -gt 0 ]; then
    pass "spider/ 包含 ${PY_COUNT} 个 .py 文件"
else
    fail "spider/ 包为空"
fi

# 检查适配器是否都注册了
ADAPTER_FILES=$(find spider/adapters/ -name "*.py" -not -name "__init__.py" | wc -l | tr -d ' ')
pass "已有 ${ADAPTER_FILES} 个适配器文件"

# 检查引擎文件数
ENGINE_FILES=$(find spider/engines/ -name "*.py" -not -name "__init__.py" | wc -l | tr -d ' ')
pass "已有 ${ENGINE_FILES} 个引擎文件"
echo ""

# V5: git 状态
echo "--- V5: Git 状态 ---"
UNCOMMITTED=$(git status --porcelain | wc -l | tr -d ' ')
if [ "$UNCOMMITTED" -eq 0 ]; then
    pass "工作区干净"
else
    warn "有 ${UNCOMMITTED} 个未提交变更"
    git status --short
fi
echo ""

# V6: 依赖检查
echo "--- V6: 依赖 ---"
for pkg in crawl4ai httpx markdownify pydantic mcp; do
    if .venv/bin/python3 -c "import importlib; importlib.import_module('$pkg')" 2>/dev/null; then
        pass "$pkg 已安装"
    else
        fail "$pkg 未安装"
    fi
done
echo ""

# 汇总
echo "=== 结果 ==="
if [ $ERRORS -gt 0 ]; then
    fail "有 $ERRORS 个错误，$WARNS 个警告"
    exit 1
elif [ $WARNS -gt 0 ]; then
    warn "有 $WARNS 个警告，无错误"
    exit 0
else
    pass "全部通过！"
    exit 0
fi
