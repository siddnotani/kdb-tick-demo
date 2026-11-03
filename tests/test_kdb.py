from datetime import date, timedelta

import pandas as pd
import pykx as kx
import pytest

from app.kdb import QUERIES, Endpoint, KdbClient, format_timespan, to_q, to_records


def test_endpoint_parse():
    assert Endpoint.parse("kdb-host:5011") == Endpoint("kdb-host", 5011)
    assert Endpoint.parse(":5012") == Endpoint("localhost", 5012)


def test_to_q_types():
    assert isinstance(to_q(date(2026, 1, 2)), kx.DateAtom)
    assert isinstance(to_q(timedelta(minutes=5)), kx.TimespanAtom)
    assert isinstance(to_q(["JPM", "GS"]), kx.SymbolVector)
    assert isinstance(to_q([]), kx.SymbolVector)
    assert isinstance(to_q(10), kx.LongAtom)


def test_to_q_rejects_strings():
    with pytest.raises(TypeError):
        to_q("JPM")


def test_format_timespan():
    assert format_timespan(pd.Timedelta(hours=9, minutes=30, milliseconds=5)) == "09:30:00.005"
    assert format_timespan(pd.NaT) is None


def test_to_records_flattens_keyed_tables():
    df = pd.DataFrame(
        {"vwap": [101.0], "time": [pd.Timedelta(hours=10)]},
        index=pd.Index(["JPM"], name="sym"),
    )
    assert to_records(df) == [{"sym": "JPM", "vwap": 101.0, "time": "10:00:00.000"}]


def test_to_records_maps_nan_to_null():
    assert to_records(pd.DataFrame({"x": [float("nan")]})) == [{"x": None}]


def test_endpoint_for_routes_today_to_rdb():
    client = KdbClient(Endpoint("r", 1), Endpoint("h", 2), today=lambda: date(2026, 1, 2))
    assert client.endpoint_for(date(2026, 1, 2)) == client.rdb
    assert client.endpoint_for(date(2026, 1, 1)) == client.hdb


def test_from_env(monkeypatch):
    monkeypatch.setenv("RDB_ADDR", "a:1")
    monkeypatch.setenv("HDB_ADDR", "b:2")
    client = KdbClient.from_env()
    assert (client.rdb, client.hdb) == (Endpoint("a", 1), Endpoint("b", 2))


def test_ping_false_when_nothing_listening():
    client = KdbClient(Endpoint("localhost", 1), Endpoint("localhost", 1), timeout=1)
    assert client.ping(client.rdb) is False


def test_queries_never_interpolate_arguments():
    assert all(q.startswith("{[") for q in QUERIES.values())
