# kdb-tick-demo

A small kdb+/q market-data stack built for Devin demos at banks and trading firms. It runs the
classic kdb+tick setup on synthetic US bank equities (`JPM GS MS BAC C WFC`), with q analytics
and a PyKX/FastAPI service on top.

```
feed.q ──► tickerplant (tick.q :5010) ──► RDB (q/rdb.q :5011, today)
               │ log: data/symYYYY.MM.DD        │ end of day: write to HDB
               ▼                                ▼
                                 HDB (q/hdb.q :5012, data/sym/<date>/...)
FastAPI (app/) ── PyKX IPC ──► RDB for today, HDB for earlier dates
```

| Path | What it is |
| --- | --- |
| `tick.q`, `tick/u.q`, `tick/r.q` | Vanilla tickerplant, pub/sub and RDB from [KxSystems/kdb-tick](https://github.com/KxSystems/kdb-tick), copied unchanged |
| `tick/sym.q` | `trade` and `quote` schemas |
| `q/synth.q` | Deterministic random-walk quote/trade generator |
| `q/feed.q` | Feed handler publishing to the tickerplant on a timer |
| `q/gen_hdb.q` | Writes N weekdays of synthetic history with `.Q.dpft` |
| `q/analytics.q` | `.mkt.slice`, `.mkt.vwap`, `.mkt.bars`, `.mkt.withQuotes` (as-of join), `.mkt.spread`, `.mkt.tca` |
| `q/rdb.q`, `q/hdb.q` | RDB / HDB processes with the analytics loaded |
| `app/` | FastAPI service: `/health /dates /vwap /bars /spread /tca /trades` |
| `tests/q/` | q unit tests (`tests/q/run.q` is the runner) |
| `tests/` | pytest: API and client unit tests, plus an end-to-end test of the whole stack |

## Setup

Requires q (KDB-X Community Edition, free; register at
https://developer.kx.com/products/kdb-x/install to get a base64 `kc.lic`) and Python 3.11.

```bash
KDB_LICENSE_KEY=<base64 kc.lic> scripts/install_kdbx.sh   # installs q to ~/.kx, telemetry off
export PATH="$HOME/.kx/bin:$PATH"
python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
```

## Run

```bash
scripts/start.sh                       # generates data/sym history on first run, starts tp, hdb, rdb, feed
uvicorn app.main:app --port 8000       # Swagger at http://localhost:8000/docs
curl -s 'localhost:8000/vwap?sym=JPM&sym=GS'
curl -s 'localhost:8000/bars?date=2026-11-02&sym=JPM&minutes=30'
q                                      # then: h:hopen 5012; h".mkt.tca[.mkt.slice[`trade;last date;`JPM];.mkt.slice[`quote;last date;`JPM]]"
scripts/stop.sh
```

Ports and paths come from `TP_PORT RDB_PORT HDB_PORT DATA_DIR HDB_DAYS` (start script) and
`RDB_ADDR HDB_ADDR` (API). The API only needs IPC, so PyKX runs unlicensed.

## Lint and test

```bash
ruff check . && ruff format --check .
q tests/q/run.q -q                     # q unit tests
pytest -q                              # unit tests; the end-to-end test is skipped if q is not installed
```

## Demo prompts for Devin

- "Add a TWAP analytic to `q/analytics.q`, a `/twap` endpoint and tests in q and pytest."
- "Add a data-quality check for crossed quotes (bid >= ask) and out-of-order timestamps, exposed as `/dq`."
- "Add a `notional` column to `trade` end to end: schema, feed, HDB backfill of existing partitions, analytics."
- "Explain how end of day works in this stack and what happens to a subscriber that connects mid-day."
- "Port `.mkt.tca` to PyKX/pandas and prove both versions give the same numbers on the HDB."
