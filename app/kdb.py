"""PyKX IPC client that sends today's queries to the RDB and earlier dates to the HDB."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

# The q processes do the work; Python only needs IPC, which PyKX supports without a license.
os.environ.setdefault("PYKX_UNLICENSED", "true")

import pandas as pd  # noqa: E402
import pykx as kx  # noqa: E402

# q functions called over IPC. Arguments are sent as typed q values, never spliced into strings.
QUERIES: dict[str, str] = {
    "vwap": "{[d;s] .mkt.vwap .mkt.slice[`trade;d;s]}",
    "bars": "{[d;s;w] .mkt.bars[.mkt.slice[`trade;d;s];w]}",
    "spread": "{[d;s] .mkt.spread .mkt.slice[`quote;d;s]}",
    "tca": "{[d;s] .mkt.tca[.mkt.slice[`trade;d;s];.mkt.slice[`quote;d;s]]}",
    "trades": "{[d;s;n] neg[n] sublist .mkt.slice[`trade;d;s]}",
}


@dataclass(frozen=True)
class Endpoint:
    host: str
    port: int

    @classmethod
    def parse(cls, addr: str) -> Endpoint:
        host, _, port = addr.rpartition(":")
        return cls(host or "localhost", int(port))


def to_q(value: Any) -> kx.K:
    if isinstance(value, date):
        return kx.DateAtom(value)
    if isinstance(value, timedelta):
        return kx.TimespanAtom(value)
    if isinstance(value, list):
        return kx.SymbolVector(value)
    if isinstance(value, int):
        return kx.LongAtom(value)
    raise TypeError(f"unsupported argument type: {type(value).__name__}")


def format_timespan(td: pd.Timedelta) -> str | None:
    if pd.isna(td):
        return None
    total_ms = int(td / pd.Timedelta(milliseconds=1))
    seconds, ms = divmod(total_ms, 1000)
    minutes, s = divmod(seconds, 60)
    h, m = divmod(minutes, 60)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Flatten a (possibly keyed) q table into JSON-safe rows."""
    if any(name is not None for name in df.index.names):
        df = df.reset_index()
    df = df.copy()
    for col in df.columns:
        if pd.api.types.is_timedelta64_dtype(df[col]):
            df[col] = df[col].map(format_timespan)
    return json.loads(df.to_json(orient="records"))


@dataclass
class KdbClient:
    rdb: Endpoint
    hdb: Endpoint
    timeout: float = 10.0
    today: Any = field(default=date.today)

    @classmethod
    def from_env(cls) -> KdbClient:
        return cls(
            rdb=Endpoint.parse(os.environ.get("RDB_ADDR", "localhost:5011")),
            hdb=Endpoint.parse(os.environ.get("HDB_ADDR", "localhost:5012")),
        )

    def endpoint_for(self, d: date) -> Endpoint:
        return self.rdb if d == self.today() else self.hdb

    def _eval(self, endpoint: Endpoint, expr: str, *args: Any) -> kx.K:
        with kx.SyncQConnection(endpoint.host, endpoint.port, timeout=self.timeout) as conn:
            return conn(expr, *(to_q(a) for a in args))

    def query(self, name: str, d: date, *args: Any) -> list[dict[str, Any]]:
        result = self._eval(self.endpoint_for(d), QUERIES[name], d, *args)
        return to_records(result.pd())

    def dates(self) -> list[str]:
        return [d.isoformat() for d in self._eval(self.hdb, "date").py()]

    def ping(self, endpoint: Endpoint) -> bool:
        try:
            return bool(self._eval(endpoint, "1b").py())
        except Exception:
            return False
