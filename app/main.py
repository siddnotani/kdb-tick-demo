from datetime import date, timedelta
from functools import lru_cache
from typing import Annotated, Any

import pykx as kx
from fastapi import Depends, FastAPI, HTTPException, Query

from app.kdb import KdbClient

app = FastAPI(title="kdb tick demo API", version="0.1.0")

# Endpoints are async on purpose: q IPC handles only work on the main thread ("nosocket"),
# and uvicorn runs the event loop there, whereas sync endpoints run in a thread pool.


@lru_cache
def get_client() -> KdbClient:
    return KdbClient.from_env()


Client = Annotated[KdbClient, Depends(get_client)]
Day = Annotated[date | None, Query(alias="date", description="Defaults to today (RDB)")]
Syms = Annotated[list[str] | None, Query(alias="sym", description="Repeatable; omit for all")]


def run(
    client: KdbClient, name: str, d: date | None, sym: list[str] | None, *args: Any
) -> list[dict[str, Any]]:
    try:
        return client.query(name, d or date.today(), sym or [], *args)
    except kx.QError as e:
        raise HTTPException(status_code=400, detail=f"q error: {e}") from e
    except (ConnectionError, OSError) as e:
        raise HTTPException(status_code=503, detail="kdb process unavailable") from e


@app.get("/health")
async def health(client: Client) -> dict[str, Any]:
    rdb, hdb = client.ping(client.rdb), client.ping(client.hdb)
    return {"status": "ok" if rdb and hdb else "degraded", "rdb": rdb, "hdb": hdb}


@app.get("/dates")
async def dates(client: Client) -> list[str]:
    try:
        return client.dates()
    except (ConnectionError, OSError) as e:
        raise HTTPException(status_code=503, detail="kdb process unavailable") from e


@app.get("/vwap")
async def vwap(client: Client, d: Day = None, sym: Syms = None) -> list[dict[str, Any]]:
    return run(client, "vwap", d, sym)


@app.get("/bars")
async def bars(
    client: Client,
    d: Day = None,
    sym: Syms = None,
    minutes: Annotated[int, Query(ge=1, le=390)] = 5,
) -> list[dict[str, Any]]:
    return run(client, "bars", d, sym, timedelta(minutes=minutes))


@app.get("/spread")
async def spread(client: Client, d: Day = None, sym: Syms = None) -> list[dict[str, Any]]:
    return run(client, "spread", d, sym)


@app.get("/tca")
async def tca(client: Client, d: Day = None, sym: Syms = None) -> list[dict[str, Any]]:
    return run(client, "tca", d, sym)


@app.get("/trades")
async def trades(
    client: Client,
    d: Day = None,
    sym: Syms = None,
    limit: Annotated[int, Query(ge=1, le=10_000)] = 100,
) -> list[dict[str, Any]]:
    return run(client, "trades", d, sym, limit)
