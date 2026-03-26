#!/bin/bash
# System Designer OpenCode 安装脚本

set -e

echo "=========================================="
echo "System Designer - OpenCode 安装脚本"
echo "=========================================="

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo ""
echo "Step 1: 检查依赖..."

# 检查 Python
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo -e "${RED}错误: 未找到 Python，请先安装 Python 3.10+${NC}"
    exit 1
fi

PYTHON_CMD=$(command -v python3 || command -v python)
echo -e "${GREEN}✓${NC} Python: $($PYTHON_CMD --version)"

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}警告: 未找到 Node.js，如需使用 OpenCode CLI 请先安装${NC}"
else
    echo -e "${GREEN}✓${NC} Node.js: $(node --version)"
fi

echo ""
echo "Step 2: 安装 Python 依赖..."

# 创建虚拟环境（如果不存在）
VENV_DIR="$SCRIPT_DIR/src/subagent/system_designer_beta/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "创建虚拟环境..."
    $PYTHON_CMD -m venv "$VENV_DIR"
fi

# 激活虚拟环境并安装依赖
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source "$VENV_DIR/Scripts/activate"
else
    # Linux/macOS
    source "$VENV_DIR/bin/activate"
fi

pip install -r "$SCRIPT_DIR/src/subagent/system_designer_beta/requirements.txt"

echo -e "${GREEN}✓${NC} Python 依赖安装完成"

echo ""
echo "Step 3: 配置环境变量..."

ENV_FILE="$SCRIPT_DIR/src/subagent/system_designer_beta/.env"
ENV_EXAMPLE="$SCRIPT_DIR/src/subagent/system_designer_beta/.env.example"

if [ ! -f "$ENV_FILE" ]; then
    echo "创建 .env 文件..."
    cp "$ENV_EXAMPLE" "$ENV_FILE"
    echo -e "${YELLOW}请编辑 $ENV_FILE 并填入你的 ANTHROPIC_API_KEY${NC}"
else
    echo -e "${GREEN}✓${NC} .env 文件已存在"
fi

echo ""
echo "Step 4: 创建必要的目录..."

mkdir -p "$SCRIPT_DIR/docs/reference"
mkdir -p "$SCRIPT_DIR/data/images"
mkdir -p "$SCRIPT_DIR/data/sessions"
mkdir -p "$SCRIPT_DIR/data/test"

echo -e "${GREEN}✓${NC} 目录创建完成"

echo ""
echo "Step 5: 配置 OpenCode..."

# 检查是否已安装 OpenCode
if command -v opencode &> /dev/null; then
    echo -e "${GREEN}✓${NC} OpenCode 已安装: $(opencode --version 2>/dev/null || echo 'unknown')"
    
    # 创建 OpenCode 配置目录
    OPENCODE_CONFIG_DIR="$HOME/.opencode"
    mkdir -p "$OPENCODE_CONFIG_DIR/skills"
    
    # 复制 Skill 文件
    echo "安装 Skill 到 OpenCode..."
    cp "$SCRIPT_DIR/SKILL.md" "$OPENCODE_CONFIG_DIR/skills/system-designer.md"
    cp "$SCRIPT_DIR/OPENCODE.md" "$OPENCODE_CONFIG_DIR/skills/system-designer-opencode.md"
    
    echo -e "${GREEN}✓${NC} Skill 已安装到 OpenCode"
else
    echo -e "${YELLOW}警告: 未找到 OpenCode CLI${NC}"
    echo "请运行: npm install -g opencode"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}安装完成！${NC}"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 编辑 $ENV_FILE，填入你的 ANTHROPIC_API_KEY"
echo "2. 启动 OpenCode: opencode"
echo "3. 说「帮我设计一个XX系统」开始使用"
echo ""
echo "详细使用说明请参考 README.md"