---
name: kdb-q
description: Write, debug, test and review q/kdb+ code in this repo (tickerplant, RDB, HDB, analytics in q/analytics.q, PyKX API). Use for any change to *.q files, HDB schema changes, end-of-day logic, or PyKX calls into q.
---

# Working with q / kdb+ in kdb-tick-demo

## Before you change anything
- q lives at `~/.kx/bin/q` (KDB-X Community). If missing: `KDB_LICENSE_KEY=... scripts/install_kdbx.sh`. Never echo the license.
- Run every q process **from the repo root**. `tick.q` loads `tick/sym.q` relatively and `r.q` / `\l <db>` change the working directory.
- Start the stack with `scripts/start.sh` and stop it with `scripts/stop.sh`. Query a process with `q` then `h:hopen 5011; h"..."` (5010 tp, 5011 rdb, 5012 hdb).

## Verify every change
```bash
q tests/q/run.q -q          # q unit tests: add a tests/q/test_<area>.q using .t.eq / .t.ok / .t.throws
ruff check . && ruff format --check .
pytest -q                   # includes tests/test_integration.py: real stack on spare ports + API + end of day
```
A new q function gets a q test. A new endpoint gets a pytest in `tests/test_api.py` (fake client) and, if it hits q, a case in `tests/test_integration.py`.

## Architecture rules
- `tick.q`, `tick/u.q`, `tick/r.q` are vendored from KxSystems/kdb-tick. Don't edit them; wrap them (see `q/rdb.q`).
- Schemas live only in `tick/sym.q`. `time` (timespan, stamped by the TP) and `sym` must be the first two columns. The feed sends every column **except** `time`.
- Analytics in `q/analytics.q` (namespace `.mkt`) take in-memory tables. Get data with `.mkt.slice[`trade;date;syms]` so the same function works on the RDB (today) and the HDB (partitioned by `date`).
- Keep globals out of the root namespace in the RDB. `.u.end` saves **every** root table with `g#sym` to the HDB at end of day.
- Adding a column means changing the schema, feed, synth generator and analytics, **and** backfilling existing HDB partitions (every `data/sym/<date>/<table>/` and `.d` file). Otherwise old dates break queries.

## q gotchas seen in this repo
- q evaluates right to left with no operator precedence. `-1 -3!x` parses as `(-1 -3)!x`, so write `-1 .Q.s1 x`.
- Inner lambdas don't capture outer locals. Pass them in or project: `{x y}[f]`, not `{f y}`.
- Functional select needs a symbol list enlisted inside the parse tree: `(in;`sym;enlist syms)`.
- `aj` needs the right-hand table sorted by `sym`,`time` (or `g#sym` with time sorted). Use `` `sym`time xasc `` on subsets.
- `.z.D`/`.z.P` are local time and the TP uses them for the log date. Tests should use `.z.D`, not hard-coded dates.
- Don't `select from` a whole HDB table without a `date` constraint. Always filter `date` first, then `sym`.
- Never `delete` from or overwrite HDB partitions in place. Write a new partition or a scripted backfill and test it on a copy (`DATA_DIR=/tmp/x scripts/start.sh`).

## PyKX from Python
- The API only does IPC, so `app/kdb.py` sets `PYKX_UNLICENSED=true`. Send typed args (`kx.DateAtom`, `kx.SymbolVector`, `kx.TimespanAtom`) to a q lambda in `QUERIES`. Never format user input into q strings.
- q IPC handles must be used on the **main thread** (`nosocket` error otherwise). FastAPI endpoints are `async def` for this reason, and integration tests call the app with `httpx.ASGITransport` from the test thread, not `TestClient`.
- Importing pykx unlicensed unsets `QHOME`. Restore it from `PYKX_OLD_QHOME` before spawning `q` subprocesses from Python.
