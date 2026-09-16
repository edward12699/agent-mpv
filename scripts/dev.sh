#!/usr/bin/env bash
# 同时启动 ts-agent 的 Next.js 客户端 和 py-agent 的 FastAPI 后端。
# 用法（仓库根目录）：
#   ./scripts/dev.sh
#
# 可选环境变量：
#   NEXT_PORT   Next.js 端口，默认 3002（与 py-agent CORS 一致）
#   PY_HOST     后端监听地址，默认 127.0.0.1
#   PY_PORT     后端端口，默认 8000

set -euo pipefail
set -m

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TS_DIR="$ROOT/ts-agent"
PY_DIR="$ROOT/py-agent"

NEXT_PORT="${NEXT_PORT:-3002}"
PY_HOST="${PY_HOST:-127.0.0.1}"
PY_PORT="${PY_PORT:-8000}"
API_URL="http://${PY_HOST}:${PY_PORT}"

if [[ ! -d "$TS_DIR" ]]; then
  echo "未找到 ts-agent 目录：$TS_DIR" >&2
  exit 1
fi

if [[ ! -d "$PY_DIR" ]]; then
  echo "未找到 py-agent 目录：$PY_DIR" >&2
  exit 1
fi

if [[ ! -d "$TS_DIR/node_modules" ]]; then
  echo "未找到 ts-agent/node_modules，请先执行：cd ts-agent && npm install" >&2
  exit 1
fi

if [[ -x "$PY_DIR/venv/bin/python" ]]; then
  PYTHON="$PY_DIR/venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON="$(command -v python3)"
else
  echo "未找到 Python。请先创建虚拟环境：cd py-agent && python3 -m venv venv" >&2
  exit 1
fi

if ! "$PYTHON" -c "import uvicorn" >/dev/null 2>&1; then
  echo "当前 Python 环境未安装 uvicorn。请先执行：" >&2
  echo "  source py-agent/venv/bin/activate && pip install -r py-agent/requirements.txt" >&2
  exit 1
fi

PIDS=()

prefix_logs() {
  local name="$1"
  local color="$2"
  local reset=$'\033[0m'
  while IFS= read -r line || [[ -n "$line" ]]; do
    printf '%b[%s]%b %s\n' "$color" "$name" "$reset" "$line"
  done
}

stop_pid() {
  local pid="$1"
  if ! kill -0 "$pid" 2>/dev/null; then
    return 0
  fi
  kill -- "-${pid}" 2>/dev/null || kill "$pid" 2>/dev/null || true
  wait "$pid" 2>/dev/null || true
}

cleanup() {
  trap - INT TERM EXIT
  echo
  echo "正在停止服务..."
  local pid
  for pid in "${PIDS[@]:-}"; do
    stop_pid "$pid"
  done
}

trap cleanup INT TERM EXIT

echo "启动 py-agent 后端 -> ${API_URL}"
(
  cd "$PY_DIR"
  exec "$PYTHON" -m uvicorn app.api.main:app \
    --reload \
    --host "$PY_HOST" \
    --port "$PY_PORT"
) > >(prefix_logs "py-agent" $'\033[0;32m') 2>&1 &
PIDS+=($!)

echo "启动 ts-agent Next.js -> http://localhost:${NEXT_PORT}"
(
  cd "$TS_DIR"
  export PORT="$NEXT_PORT"
  export NEXT_PUBLIC_AGENT_API_URL_PY="$API_URL"
  exec npm run dev -- --port "$NEXT_PORT"
) > >(prefix_logs "ts-agent" $'\033[0;36m') 2>&1 &
PIDS+=($!)

echo
echo "前端: http://localhost:${NEXT_PORT}"
echo "后端: ${API_URL}/health"
echo "按 Ctrl+C 同时停止两个服务"
echo

# 任一进程退出后结束另一个。macOS 自带 bash 3.2 不支持 wait -n，因此轮询。
while true; do
  for pid in "${PIDS[@]}"; do
    if ! kill -0 "$pid" 2>/dev/null; then
      echo "有服务已退出，正在关闭其余进程..."
      exit 1
    fi
  done
  sleep 1
done
