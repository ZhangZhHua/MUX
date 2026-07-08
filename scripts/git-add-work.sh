#!/bin/bash
# =============================================================
# git-add-work.sh - 智能 Git 暂存助手（修复优化版）
# 功能：交互式选择要暂存的文件，支持分类暂存
# =============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}    Git 暂存助手 - MUX 物理实验室日志   ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# ✨ 修复点 1：优先精准定位并切换到 Git 项目根目录
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo -e "${RED}❌ 错误：当前目录或上级目录不是一个 Git 仓库。${NC}"
    exit 1
fi
PROJECT_ROOT=$(git rev-parse --show-toplevel)
cd "$PROJECT_ROOT"

# ✨ 修复点 2：在根目录下安全获取文件列表
UNTRACKED=$(git ls-files --others --exclude-standard)
MODIFIED=$(git diff --name-only)
STAGED=$(git diff --cached --name-only)

if [ -z "$UNTRACKED" ] && [ -z "$MODIFIED" ] && [ -z "$STAGED" ]; then
    echo -e "${GREEN}✔ 工作区干净，没有需要暂存的文件。${NC}"
    exit 0
fi

echo -e "${YELLOW}请选择操作：${NC}"
echo "1) 暂存所有更改（跟踪文件 + 新文件）"
echo "2) 只暂存已跟踪文件的更改（不包含新文件）"
echo "3) 手动选择要暂存的类别"
echo "4) 查看当前状态后退出"
echo ""

read -p "输入选择 [1-4]: " choice

case $choice in
    1)
        echo -e "\n${YELLOW}正在暂存所有更改...${NC}"
        git add -A
        echo -e "${GREEN}✔ 所有更改已暂存。${NC}"
        ;;
    2)
        echo -e "\n${YELLOW}正在暂存已跟踪文件的更改...${NC}"
        git add -u
        echo -e "${GREEN}✔ 已跟踪文件的更改已暂存。${NC}"
        ;;
    3)
        echo ""
        echo -e "${YELLOW}暂存新文件：${NC}"
        if [ -n "$UNTRACKED" ]; then
            echo "未跟踪的文件："
            echo "$UNTRACKED" | nl -w2 -s') '
            read -p "输入要暂存的文件编号（空格分隔，或输入 'all' 暂存全部，留空跳过）: " file_nums
            
            # 转为小写比较
            file_nums_lower=$(echo "$file_nums" | tr '[:upper:]' '[:lower:]')
            
            if [ "$file_nums_lower" = "all" ]; then
                echo "$UNTRACKED" | while IFS= read -r f; do
                    git add "$f"
                    echo -e "  ${GREEN}+${NC} $f"
                done
            elif [ -n "$file_nums" ]; then
                for num in $file_nums; do
                    # ✨ 修复点 3：增加数字合法性校验，防止 sed 报错导致 set -e 闪退
                    if [[ "$num" =~ ^[0-9]+$ ]]; then
                        file=$(echo "$UNTRACKED" | sed -n "${num}p")
                        if [ -n "$file" ]; then
                            git add "$file"
                            echo -e "  ${GREEN}+${NC} $file"
                        fi
                    else
                        echo -e "  ${RED}⚠ 跳过无效编号:${NC} $num"
                    fi
                done
            fi
        else
            echo "  (无)"
        fi

        echo -e "\n${YELLOW}暂存已修改的文件：${NC}"
        if [ -n "$MODIFIED" ]; then
            echo "已修改的文件："
            echo "$MODIFIED" | nl -w2 -s') '
            read -p "输入要暂存的文件编号（空格分隔，或输入 'all' 暂存全部，留空跳过）: " mod_nums
            
            # 转为小写比较
            mod_nums_lower=$(echo "$mod_nums" | tr '[:upper:]' '[:lower:]')
            
            if [ "$mod_nums_lower" = "all" ]; then
                echo "$MODIFIED" | while IFS= read -r f; do
                    git add "$f"
                    echo -e "  ${GREEN}+${NC} $f"
                done
            elif [ -n "$mod_nums" ]; then
                for num in $mod_nums; do
                    # ✨ 修复点 3：同样增加数字合法性校验
                    if [[ "$num" =~ ^[0-9]+$ ]]; then
                        file=$(echo "$MODIFIED" | sed -n "${num}p")
                        if [ -n "$file" ]; then
                            git add "$file"
                            echo -e "  ${GREEN}+${NC} $file"
                        fi
                    else
                        echo -e "  ${RED}⚠ 跳过无效编号:${NC} $num"
                    fi
                done
            fi
        else
            echo "  (无)"
        fi
        ;;
    4)
        echo -e "\n${BLUE}当前 Git 状态：${NC}"
        git status
        exit 0
        ;;
    *)
        echo -e "${RED}无效选择，退出。${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}当前暂存区状态：${NC}"
git --no-pager diff --cached --stat
echo ""
echo -e "${GREEN}✔ 完成。运行 scripts/git-commit-work.sh 继续提交。${NC}"