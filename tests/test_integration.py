"""End-to-end: start the real tick stack on spare ports and query it through the API."""

import asyncio
import os
import shutil
import socket
import subprocess
import time
from datetime import date
from pathlib import Path

import httpx
import pytest

from app.kdb import Endpoint, KdbClient
from app.main import app, get_client

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(shutil.which("q") is None, reason="q (KDB-X) not installed")


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def stack(tmp_path_factory):
    ports = {"TP_PORT": free_port(), "RDB_PORT": free_port(), "HDB_PORT": free_port()}
    env = {
        **os.environ,
        **{k: str(v) for k, v in ports.items()},
        "DATA_DIR": str(tmp_path_factory.mktemp("kdb")),
        "HDB_DAYS": "2",
    }
    # importing pykx in unlicensed mode unsets QHOME; give the q subprocesses theirs back
    for var in ("QHOME", "QPATH"):
        if f"PYKX_OLD_{var}" in os.environ:
            env[var] = os.environ[f"PYKX_OLD_{var}"]
    subprocess.run([ROOT / "scripts/start.sh"], env=env, check=True)
    client = KdbClient(
        Endpoint("localhost", ports["RDB_PORT"]), Endpoint("localhost", ports["HDB_PORT"])
    )
    app.dependency_overrides[get_client] = lambda: client
    try:
        yield client, ports
    finally:
        app.dependency_overrides.clear()
        subprocess.run([ROOT / "scripts/stop.sh"], env=env, check=False)


def get(path: str, **params) -> httpx.Response:
    """Call the API on this (main) thread; TestClient would run it on a worker thread."""

    async def call() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as api:
            return await api.get(path, params=params)

    return asyncio.run(call())


def wait_for(fn, timeout=10.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if result := fn():
            return result
        time.sleep(0.2)
    raise AssertionError("condition not met in time")


def test_health(stack):
    assert get("/health").json() == {"status": "ok", "rdb": True, "hdb": True}


def test_hdb_history(stack):
    dates = get("/dates").json()
    assert len(dates) == 2
    vwap = get("/vwap", date=dates[-1]).json()
    assert {row["sym"] for row in vwap} == {"JPM", "GS", "MS", "BAC", "C", "WFC"}
    bars = get("/bars", date=dates[-1], sym="JPM", minutes=60).json()
    assert bars[0]["time"] == "09:00:00.000"
    assert all(b["low"] <= b["open"] <= b["high"] for b in bars)


def test_rdb_today_fills_from_feed(stack):
    trades = wait_for(lambda: get("/trades", sym="JPM", limit=3).json())
    assert all(t["sym"] == "JPM" for t in trades)
    tca = get("/tca", sym="GS").json()
    assert tca[0]["sym"] == "GS"


def test_missing_hdb_date_is_empty(stack):
    r = get("/vwap", date="2020-01-01")
    assert r.status_code == 200 and r.json() == []


def test_end_of_day_writes_today_to_hdb(stack):
    client, ports = stack
    wait_for(lambda: client.query("trades", date.today(), [], 1))
    tp = Endpoint("localhost", ports["TP_PORT"])
    client._eval(tp, ".u.endofday[]")
    wait_for(lambda: date.today().isoformat() in client.dates())
    assert client._eval(client.hdb, "count select from trade where date=.z.D").py() > 0
