#!/bin/bash

# 停止服务脚本

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.app.pid"

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

# 检查 PID 文件是否存在
if [ ! -f "$PID_FILE" ]; then
    print_warn "未找到 PID 文件，尝试查找运行中的进程..."
    
    # 尝试通过端口查找进程
    PID=$(lsof -ti:5001 2>/dev/null)
    if [ -z "$PID" ]; then
        print_warn "未找到运行中的应用"
        exit 0
    else
        print_info "找到运行中的进程 (PID: $PID)"
        kill "$PID"
        print_info "应用已停止"
        exit 0
    fi
fi

# 读取 PID
APP_PID=$(cat "$PID_FILE")

# 检查进程是否存在
if ps -p "$APP_PID" > /dev/null 2>&1; then
    print_info "正在停止应用 (PID: $APP_PID)..."
    kill "$APP_PID"
    
    # 等待进程结束
    for i in {1..10}; do
        if ! ps -p "$APP_PID" > /dev/null 2>&1; then
            break
        fi
        sleep 1
    done
    
    # 如果进程仍在运行，强制杀死
    if ps -p "$APP_PID" > /dev/null 2>&1; then
        print_warn "进程未正常退出，强制终止..."
        kill -9 "$APP_PID"
    fi
    
    print_info "应用已停止"
else
    print_warn "进程不存在 (PID: $APP_PID)"
fi

# 删除 PID 文件
rm -f "$PID_FILE"
print_info "清理完成"

