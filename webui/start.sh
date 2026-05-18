#!/bin/bash

# Kronos WebUI 启动脚本

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_DIR/kronos_env"

echo "================================"
echo "  Kronos 股票预测 WebUI"
echo "================================"
echo ""

# 检查虚拟环境
if [ ! -d "$VENV_DIR" ]; then
    echo "未找到虚拟环境，请先运行一键安装脚本："
    echo "  bash $PROJECT_DIR/install.sh"
    exit 1
fi

# 激活虚拟环境
source "$VENV_DIR/bin/activate"

# 检查依赖
echo "检查依赖..."
if ! python3 -c "import fastapi, uvicorn, pandas, matplotlib" &>/dev/null; then
    echo "依赖不完整，正在安装..."
    pip install -r "$SCRIPT_DIR/requirements.txt" -q
fi

# 启动服务
echo ""
echo "WebUI 启动中..."
echo "浏览器访问: http://localhost:8899"
echo "按 Ctrl+C 停止服务"
echo ""

cd "$SCRIPT_DIR"
python3 app.py
