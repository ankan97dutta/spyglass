import asyncio
import time
from typing import Any

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine

from profilis.core.async_collector import AsyncCollector
from profilis.core.emitter import Emitter
from profilis.sqlalchemy.instrumentation import (
    instrument_async_engine,
    instrument_engine,
    redact_statement,
)

# Constants for test values
TEST_BATCH_SIZE = 64
TEST_QUEUE_SIZE = 128
TEST_FLUSH_INTERVAL = 0.01
TEST_SLEEP_TIME = 0.05
MIN_REDACTED_PLACEHOLDERS = 2


class _Sink(list[Any]):
    def __call__(self, batch: list[Any]) -> None:
        self.extend(batch)


def test_redaction() -> None:
    s = "INSERT INTO t (name, age) VALUES ('Alice', 42)"
    r = redact_statement(s)
    assert "'Alice'" not in r and "42" not in r
    assert r.count("?") >= MIN_REDACTED_PLACEHOLDERS


def test_sync_sqlite_engine_metrics(tmp_path: Any) -> None:
    sink = _Sink()
    col = AsyncCollector(
        sink,
        queue_size=TEST_QUEUE_SIZE,
        flush_interval=TEST_FLUSH_INTERVAL,
        batch_max=TEST_BATCH_SIZE,
    )
    em = Emitter(col)

    eng = sa.create_engine("sqlite:///:memory:")
    instrument_engine(eng, em)

    with eng.begin() as conn:
        conn.execute(sa.text("CREATE TABLE x (id INTEGER PRIMARY KEY, name TEXT)"))
        conn.execute(sa.text("INSERT INTO x (name) VALUES ('Bob')"))
        res = conn.execute(sa.text("SELECT * FROM x WHERE id = 1"))
        _ = res.fetchall()

    time.sleep(TEST_SLEEP_TIME)
    col.close()

    db_events = [e for e in sink if isinstance(e, dict) and e.get("kind") == "DB"]
    assert db_events, "no DB events captured"
    assert all("'Bob'" not in e.get("query", "") for e in db_events)


async def _run_async_sqlite(col: AsyncCollector[Any], em: Emitter) -> None:
    eng = create_async_engine("sqlite+aiosqlite:///:memory:")
    instrument_async_engine(eng, em)

    async with eng.begin() as conn:
        await conn.execute(sa.text("CREATE TABLE y (id INTEGER PRIMARY KEY, v INTEGER)"))
        await conn.execute(sa.text("INSERT INTO y (v) VALUES (123)"))
        result = await conn.execute(sa.text("SELECT * FROM y WHERE v = 123"))
        result.fetchall()

    await eng.dispose()


def test_async_sqlite_engine_metrics() -> None:
    sink = _Sink()
    col = AsyncCollector(
        sink,
        queue_size=TEST_QUEUE_SIZE,
        flush_interval=TEST_FLUSH_INTERVAL,
        batch_max=TEST_BATCH_SIZE,
    )
    em = Emitter(col)

    asyncio.run(_run_async_sqlite(col, em))

    time.sleep(TEST_SLEEP_TIME)
    col.close()

    db_events = [e for e in sink if isinstance(e, dict) and e.get("kind") == "DB"]
    assert db_events, "no async DB events captured"
    assert all("123" not in e.get("query", "") for e in db_events)
