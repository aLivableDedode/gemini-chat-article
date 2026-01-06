#!/bin/bash

# 服务启动脚本
# 自动从 .env 文件加载环境变量并启动 Flask 应用

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 .env 文件是否存在
if [ -f ".env" ]; then
    print_info "发现 .env 文件，正在加载环境变量..."
    
    # 从 .env 文件读取并设置环境变量
    # 忽略注释和空行
    while IFS= read -r line || [ -n "$line" ]; do
        # 跳过注释和空行
        if [[ "$line" =~ ^[[:space:]]*# ]] || [[ -z "${line// }" ]]; then
            continue
        fi
        
        # 提取 key=value 格式的配置
        if [[ "$line" =~ ^[[:space:]]*([^=]+)=(.*)$ ]]; then
            key="${BASH_REMATCH[1]// /}"
            value="${BASH_REMATCH[2]}"
            
            # 移除值两端的引号（如果存在）
            value="${value#\"}"
            value="${value%\"}"
            value="${value#\'}"
            value="${value%\'}"
            
            # 设置环境变量
            export "$key=$value"
            print_info "已设置: $key"
        fi
    done < .env
    
    print_info "环境变量加载完成"
else
    print_warn ".env 文件不存在，将使用系统环境变量或默认值"
fi

# 检查必需的环境变量
if [ -z "$GEMINI_API_KEY" ]; then
    print_error "GEMINI_API_KEY 未设置！请设置环境变量或创建 .env 文件"
    exit 1
fi

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    print_error "未找到 python3，请先安装 Python"
    exit 1
fi

# 检查依赖是否安装
if ! python3 -c "import flask" 2>/dev/null; then
    print_warn "Flask 未安装，正在安装依赖..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        print_error "依赖安装失败"
        exit 1
    fi
fi

# 创建必要的目录
mkdir -p data
mkdir -p logs

print_info "正在启动 Flask 应用..."
print_info "服务地址: http://0.0.0.0:5001"
print_info "按 Ctrl+C 停止服务"
echo ""

# 启动 Flask 应用
python3 app.py

