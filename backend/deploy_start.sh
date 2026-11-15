#!/usr/bin/env bash
# 基智后端一键启动：装依赖 -> 停旧进程 -> 起 uvicorn -> 起 worker -> 自检
# 用法：bash deploy_start.sh
set -u

APP_DIR="/www/wwwroot/jizhi-backend-2026-11-15"
cd "$APP_DIR" || { echo "目录不存在: $APP_DIR"; exit 1; }

export PYTHONIOENCODING=utf-8

echo "[1/5] 检查 .env"
if [ ! -f .env ]; then
  echo "缺少 .env：请先把生产 .env 上传到 $APP_DIR/.env"
  exit 1
fi

echo "[2/5] 安装依赖（已装过会很快）"
python3.11 -m pip install -q -r requirements.txt || {
  echo "依赖安装失败，先看上面的报错"
  exit 1
}

echo "[3/5] 停止旧的 uvicorn / worker"
pkill -f "uvicorn main:app" 2>/dev/null || true
pkill -f "python3.11 worker.py" 2>/dev/null || true
sleep 1

echo "[4/5] 启动 uvicorn"
nohup python3.11 -m uvicorn main:app --host 127.0.0.1 --port 8000 > server.log 2>&1 &
API_PID=$!
echo "  uvicorn PID=$API_PID"

echo "[5/5] 启动 worker（需要 Redis）"
if command -v redis-cli >/dev/null 2>&1; then
  redis-cli ping >/dev/null 2>&1 || redis-server --daemonize yes 2>/dev/null || true
fi
if command -v redis-cli >/dev/null 2>&1 && redis-cli ping >/dev/null 2>&1; then
  nohup python3.11 worker.py > worker.log 2>&1 &
  WORKER_PID=$!
  echo "  worker PID=$WORKER_PID"
else
  echo "  未检测到 Redis，跳过 worker；上传解析/视频生成会排队不动"
fi

sleep 3
echo
echo "===== server.log ====="
tail -8 server.log
echo
echo "===== worker.log ====="
tail -8 worker.log 2>/dev/null || true
echo
echo "===== health ====="
curl -s http://127.0.0.1:8000/health || echo "health 请求失败"
echo
echo
echo "启动完成。查看日志：tail -f $APP_DIR/server.log"
