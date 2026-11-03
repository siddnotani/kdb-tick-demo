from datetime import date, timedelta

import pykx as kx
import pytest
from fastapi.testclient import TestClient

from app.kdb import Endpoint
from app.main import app, get_client


class FakeClient:
    rdb = Endpoint("rdb", 5011)
    hdb = Endpoint("hdb", 5012)

    def __init__(self, error: Exception | None = None):
        self.calls: list[tuple] = []
        self.error = error

    def query(self, name, d, *args):
        self.calls.append((name, d, *args))
        if self.error:
            raise self.error
        return [{"sym": "JPM", "value": 1.0}]

    def dates(self):
        return ["2026-01-01"]

    def ping(self, endpoint):
        return endpoint == self.rdb


@pytest.fixture
def fake():
    client = FakeClient()
    app.dependency_overrides[get_client] = lambda: client
    yield client
    app.dependency_overrides.clear()


api = TestClient(app)


def test_health_reports_each_process(fake):
    assert api.get("/health").json() == {"status": "degraded", "rdb": True, "hdb": False}


def test_dates(fake):
    assert api.get("/dates").json() == ["2026-01-01"]


@pytest.mark.parametrize("name", ["vwap", "spread", "tca"])
def test_analytics_pass_date_and_syms(fake, name):
    r = api.get(f"/{name}", params={"date": "2026-01-02", "sym": ["JPM", "GS"]})
    assert r.status_code == 200
    assert r.json() == [{"sym": "JPM", "value": 1.0}]
    assert fake.calls == [(name, date(2026, 1, 2), ["JPM", "GS"])]


def test_date_defaults_to_today(fake):
    api.get("/vwap")
    assert fake.calls == [("vwap", date.today(), [])]


def test_bars_sends_width_as_timedelta(fake):
    api.get("/bars", params={"date": "2026-01-02", "minutes": 15})
    assert fake.calls == [("bars", date(2026, 1, 2), [], timedelta(minutes=15))]


def test_bars_rejects_bad_width(fake):
    assert api.get("/bars", params={"minutes": 0}).status_code == 422


def test_trades_limit(fake):
    api.get("/trades", params={"sym": "JPM", "limit": 5})
    assert fake.calls == [("trades", date.today(), ["JPM"], 5)]
    assert api.get("/trades", params={"limit": 10_001}).status_code == 422


def test_q_error_is_400():
    app.dependency_overrides[get_client] = lambda: FakeClient(kx.QError("rdb only holds today"))
    try:
        r = api.get("/vwap", params={"date": "2026-01-01"})
    finally:
        app.dependency_overrides.clear()
    assert r.status_code == 400
    assert "rdb only holds today" in r.json()["detail"]


def test_connection_error_is_503():
    app.dependency_overrides[get_client] = lambda: FakeClient(ConnectionRefusedError())
    try:
        assert api.get("/vwap").status_code == 503
    finally:
        app.dependency_overrides.clear()
