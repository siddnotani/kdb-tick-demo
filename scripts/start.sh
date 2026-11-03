#!/usr/bin/env bash
# Starts the tick stack: tickerplant, HDB, RDB and synthetic feed.
# Generates synthetic history first if the HDB does not exist yet.
# Env: DATA_DIR (default ./data), TP_PORT 5010, RDB_PORT 5011, HDB_PORT 5012, HDB_DAYS 5
set -euo pipefail
cd "$(dirname "$0")/.."

DATA_DIR="${DATA_DIR:-$PWD/data}"
TP_PORT="${TP_PORT:-5010}"
RDB_PORT="${RDB_PORT:-5011}"
HDB_PORT="${HDB_PORT:-5012}"
HDB_DAYS="${HDB_DAYS:-5}"
mkdir -p "$DATA_DIR/logs"

command -v q >/dev/null || { echo "q not on PATH; run scripts/install_kdbx.sh first" >&2; exit 1; }

wait_port() {
  for _ in $(seq 1 50); do
    (exec 3<>"/dev/tcp/127.0.0.1/$1") 2>/dev/null && return 0
    sleep 0.2
  done
  echo "nothing listening on port $1; see $DATA_DIR/logs" >&2
  exit 1
}

launch() {
  local name=$1; shift
  q "$@" </dev/null >"$DATA_DIR/logs/$name.log" 2>&1 &
  echo $! >"$DATA_DIR/$name.pid"
}

if [ ! -d "$DATA_DIR/sym" ]; then
  q q/gen_hdb.q -db "$DATA_DIR/sym" -days "$HDB_DAYS" -q
fi

launch tp tick.q sym "$DATA_DIR" -p "$TP_PORT"
wait_port "$TP_PORT"
launch hdb q/hdb.q "$DATA_DIR/sym" -p "$HDB_PORT"
wait_port "$HDB_PORT"
launch rdb q/rdb.q ":$TP_PORT" ":$HDB_PORT" -p "$RDB_PORT"
wait_port "$RDB_PORT"
launch feed q/feed.q -tp "localhost:$TP_PORT"

echo "tickerplant :$TP_PORT  rdb :$RDB_PORT  hdb :$HDB_PORT  (logs in $DATA_DIR/logs)"
