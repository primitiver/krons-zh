#!/usr/bin/env bash
# Kronos 一键安装脚本
# 功能：创建虚拟环境 → 安装依赖 → 下载模型 → 启动 WebUI

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/kronos_env"
LOG_FILE="$SCRIPT_DIR/install.log"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Kronos 股票预测工具 - 一键安装${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检查 Python 版本
echo -e "${YELLOW}[1/5] 检查 Python 环境...${NC}"
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}错误：未找到 python3，请先安装 Python 3.10+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo -e "${RED}错误：需要 Python 3.10+，当前版本 $PYTHON_VERSION${NC}"
    exit 1
fi
echo -e "${GREEN}  Python $PYTHON_VERSION ✓${NC}"

# 创建虚拟环境
echo -e "${YELLOW}[2/5] 创建虚拟环境...${NC}"
if [ -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}  虚拟环境已存在，跳过创建${NC}"
else
    python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}  虚拟环境创建成功 ✓${NC}"
fi

# 激活虚拟环境
source "$VENV_DIR/bin/activate"

# 升级 pip
echo -e "${YELLOW}[3/5] 安装项目依赖...${NC}"
pip install --upgrade pip -q

# 安装核心依赖
pip install -r "$SCRIPT_DIR/requirements.txt" -q
echo -e "${GREEN}  核心依赖安装完成 ✓${NC}"

# 安装 WebUI 依赖
if [ -f "$SCRIPT_DIR/webui/requirements.txt" ]; then
    pip install -r "$SCRIPT_DIR/webui/requirements.txt" -q
    echo -e "${GREEN}  WebUI 依赖安装完成 ✓${NC}"
fi

# 安装 opencli（可选，用于实时数据获取）
echo -e "${YELLOW}[4/5] 检查实时数据工具...${NC}"
if command -v opencli &>/dev/null; then
    echo -e "${GREEN}  opencli 已安装 ✓${NC}"
else
    echo -e "${YELLOW}  opencli 未安装（可选，用于获取实时股票数据）${NC}"
    echo -e "${YELLOW}  如需使用，请运行：npm install -g opencli${NC}"
fi

# 下载模型
echo -e "${YELLOW}[5/5] 下载 Kronos 模型和分词器...${NC}"
if [ -d "$HOME/.cache/huggingface/hub" ]; then
    # 检查是否已经下载过
    if ls "$HOME/.cache/huggingface/hub"/*/models--NeoQuasar 2>/dev/null | head -1 &>/dev/null; then
        echo -e "${GREEN}  模型已在缓存中，跳过下载${NC}"
    else
        python3 -c "
from huggingface_hub import snapshot_download
print('  下载分词器...')
snapshot_download(repo_id='NeoQuasar/Kronos-Tokenizer-base', resume_download=True)
print('  下载模型...')
snapshot_download(repo_id='NeoQuasar/Kronos-small', resume_download=True)
print('  模型下载完成！')
"
    fi
else
    python3 -c "
from huggingface_hub import snapshot_download
print('  下载分词器...')
snapshot_download(repo_id='NeoQuasar/Kronos-Tokenizer-base', resume_download=True)
print('  下载模型...')
snapshot_download(repo_id='NeoQuasar/Kronos-small', resume_download=True)
print('  模型下载完成！')
"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  安装完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "启动 WebUI 预测工具："
echo -e "  ${YELLOW}source $VENV_DIR/bin/activate${NC}"
echo -e "  ${YELLOW}python $SCRIPT_DIR/webui/app.py${NC}"
echo ""
echo "然后在浏览器中访问："
echo -e "  ${GREEN}http://localhost:8899${NC}"
echo ""
echo "或者直接使用一键启动脚本（如果存在）："
echo -e "  ${YELLOW}bash $SCRIPT_DIR/webui/start.sh${NC}"
echo ""

# 保存安装信息
echo "$(date): 安装成功 (Python $PYTHON_VERSION)" >> "$LOG_FILE"
