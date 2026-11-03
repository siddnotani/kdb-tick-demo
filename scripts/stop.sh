#!/usr/bin/env bash
# Stops the processes started by scripts/start.sh.
set -euo pipefail
cd "$(dirname "$0")/.."
DATA_DIR="${DATA_DIR:-$PWD/data}"
for name in feed rdb hdb tp; do
  pidfile="$DATA_DIR/$name.pid"
  [ -f "$pidfile" ] || continue
  kill "$(cat "$pidfile")" 2>/dev/null || true
  rm -f "$pidfile"
done
