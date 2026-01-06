#!/bin/bash

# 后台启动脚本
# 在后台运行 Flask 应用

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# PID 文件路径
PID_FILE="$SCRIPT_DIR/.app.pid"
LOG_FILE="$SCRIPT_DIR/logs/app_background.log"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否已经在运行
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        print_warn "应用已在运行中 (PID: $OLD_PID)"
        print_info "如需重启，请先运行: ./stop.sh"
        exit 1
    else
        # PID 文件存在但进程不存在，删除旧的 PID 文件
        rm -f "$PID_FILE"
    fi
fi

# 加载环境变量（复用 start.sh 的逻辑）
if [ -f ".env" ]; then
    print_info "加载 .env 文件中的环境变量..."
    while IFS= read -r line || [ -n "$line" ]; do
        if [[ "$line" =~ ^[[:space:]]*# ]] || [[ -z "${line// }" ]]; then
            continue
        fi
        if [[ "$line" =~ ^[[:space:]]*([^=]+)=(.*)$ ]]; then
            key="${BASH_REMATCH[1]// /}"
            value="${BASH_REMATCH[2]}"
            value="${value#\"}"
            value="${value%\"}"
            value="${value#\'}"
            value="${value%\'}"
            export "$key=$value"
        fi
    done < .env
fi

# 检查必需的环境变量
if [ -z "$GEMINI_API_KEY" ]; then
    print_error "GEMINI_API_KEY 未设置！"
    exit 1
fi

# 创建日志目录
mkdir -p "$(dirname "$LOG_FILE")"

# 后台启动应用
print_info "正在后台启动 Flask 应用..."
nohup python3 app.py > "$LOG_FILE" 2>&1 &
APP_PID=$!

# 保存 PID
echo $APP_PID > "$PID_FILE"

# 等待一下，检查进程是否成功启动
sleep 2
if ps -p "$APP_PID" > /dev/null 2>&1; then
    print_info "应用已成功启动！"
    print_info "PID: $APP_PID"
    print_info "日志文件: $LOG_FILE"
    print_info "服务地址: http://0.0.0.0:5001"
    print_info "查看日志: tail -f $LOG_FILE"
    print_info "停止服务: ./stop.sh"
else
    print_error "应用启动失败，请查看日志: $LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi

