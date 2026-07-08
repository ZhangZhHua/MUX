#!/bin/bash
# =============================================================
# git-commit-work.sh - 智能 Git 提交助手（修复优化版）
# 功能：交互式生成 conventional commit 并安全推送
# =============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}    Git 提交助手 - MUX 物理实验室日志   ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# ✨ 修复点 1：动态、精准定位 Git 项目根目录
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo -e "${RED}❌ 错误：当前目录或上级目录不是一个 Git 仓库。${NC}"
    exit 1
fi
PROJECT_ROOT=$(git rev-parse --show-toplevel)
cd "$PROJECT_ROOT"

# 检查暂存区是否有文件
STAGED=$(git diff --cached --name-only)
if [ -z "$STAGED" ]; then
    echo -e "${YELLOW}⚠ 暂存区为空。请先运行 scripts/git-add-work.sh 暂存文件。${NC}"
    exit 1
fi

echo -e "${CYAN}暂存区中的文件：${NC}"
git --no-pager diff --cached --stat
echo ""

# 选择提交类型
echo -e "${YELLOW}选择提交类型：${NC}"
echo "1) feat     - 新功能"
echo "2) fix      - 修复 Bug"
echo "3) chore    - 杂项（构建、依赖等）"
echo "4) docs     - 文档变更"
echo "5) style    - 代码格式（不影响功能）"
echo "6) refactor - 代码重构"
echo "7) perf     - 性能优化"
echo "8) test     - 测试相关"
echo "9) ci       - CI/CD 配置变更"
echo "10) custom  - 自定义类型"
echo ""

read -p "输入选择 [1-10]: " type_choice

case $type_choice in
    1) TYPE="feat" ;;
    2) TYPE="fix" ;;
    3) TYPE="chore" ;;
    4) TYPE="docs" ;;
    5) TYPE="style" ;;
    6) TYPE="refactor" ;;
    7) TYPE="perf" ;;
    8) TYPE="test" ;;
    9) TYPE="ci" ;;
    10)
        read -p "输入自定义类型: " TYPE
        ;;
    *)
        echo -e "${RED}无效选择。${NC}"
        exit 1
        ;;
esac

echo ""

# 选择作用域（可选）
echo -e "${YELLOW}选择作用域（可选）：${NC}"
echo "1) client   - 前端"
echo "2) server   - 后端"
echo "3) config   - 配置文件"
echo "4) docs     - 文档"
echo "5) deps     - 依赖"
echo "6) scripts  - 脚本"
echo "7) none     - 无作用域"
echo "8) custom   - 自定义"
echo ""

read -p "输入选择 [1-8]: " scope_choice

case $scope_choice in
    1) SCOPE="client" ;;
    2) SCOPE="server" ;;
    3) SCOPE="config" ;;
    4) SCOPE="docs" ;;
    5) SCOPE="deps" ;;
    6) SCOPE="scripts" ;;
    7) SCOPE="" ;;
    8)
        read -p "输入自定义作用域: " SCOPE
        ;;
    *)
        echo -e "${RED}无效选择。${NC}"
        exit 1
        ;;
esac

echo ""

# 输入提交描述
read -p "输入提交描述（简短说明）: " SHORT_DESC
if [ -z "$SHORT_DESC" ]; then
    echo -e "${RED}错误：提交描述不能为空。${NC}"
    exit 1
fi

echo ""

# 输入详细描述（可选）
read -p "输入详细描述（可选，留空跳过）: " BODY

echo ""

# 构建提交消息头部
if [ -n "$SCOPE" ]; then
    COMMIT_HEADER="$TYPE($SCOPE): $SHORT_DESC"
else
    COMMIT_HEADER="$TYPE: $SHORT_DESC"
fi

echo -e "${CYAN}预期的提交消息：${NC}"
echo -e "${GREEN}$COMMIT_HEADER${NC}"
if [ -n "$BODY" ]; then
    echo -e "${GREEN}${BODY}${NC}"
fi
echo ""

# 确认提交
read -p "确认提交？（y/n）: " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo -e "${YELLOW}提交已取消。${NC}"
    exit 0
fi

echo ""
echo -e "${YELLOW}正在提交...${NC}"

# ✨ 修复点 2：使用多个 -m 传递参数，Git 会自动干净地用空行隔开标题和正文，避免跨平台转义Bug
if [ -n "$BODY" ]; then
    git commit -m "$COMMIT_HEADER" -m "$BODY"
else
    git commit -m "$COMMIT_HEADER"
fi

echo -e "${GREEN}✔ 提交成功！${NC}"
echo ""

# 推送选项
read -p "是否推送到远程仓库？（y/n）: " push_confirm
if [ "$push_confirm" = "y" ] || [ "$push_confirm" = "Y" ]; then
    BRANCH=$(git rev-parse --abbrev-ref HEAD)
    
    # ✨ 修复点 3：检测 Detached HEAD（游离头指针状态），防止误推送
    if [ "$BRANCH" = "HEAD" ]; then
        echo -e "${RED}❌ 推送终止：当前处于游离头指针（Detached HEAD）状态，无法自动推送。${NC}"
        echo -e "${YELLOW}请先切换到正常分支（如 git checkout main）后再手动推送。${NC}"
    else
        echo -e "${YELLOW}正在推送到 origin/$BRANCH ...${NC}"
        # ✨ 修复点 4：用 if 包裹推送，防止网络失败或需要 pull 时由于 set -e 直接导致整个脚本闪退
        if git push origin "$BRANCH"; then
            echo -e "${GREEN}✔ 推送成功！${NC}"
        else
            echo ""
            echo -e "${RED}❌ 推送失败！${NC}"
            echo -e "${YELLOW}原因可能是网络连接中断，或者远程仓库有更新。${NC}"
            echo -e "${YELLOW}请尝试手动运行 'git pull' 后再运行 'git push origin $BRANCH'。${NC}"
        fi
    fi
else
    echo -e "${YELLOW}跳过推送。使用 'git push origin $(git rev-parse --abbrev-ref HEAD)' 手动推送。${NC}"
fi

echo ""
echo -e "${BLUE}最新的 3 条提交：${NC}"
git log --oneline -3
echo ""
echo -e "${GREEN}✔ 完成。${NC}"