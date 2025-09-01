import asyncio
import time
from contextlib import suppress
from typing import Any

from profilis.core.async_collector import AsyncCollector
from profilis.core.emitter import Emitter
from profilis.decorators.profile import profile_function
from profilis.runtime import span_id, use_span

# Constants for test values
EXPECTED_RESULT = 42
MIN_METADATA_EVENTS = 2


class _Sink(list[Any]):
    def __call__(self, batch: list[Any]) -> None:
        self.extend(batch)


def test_nested_sync_calls_and_parent_child_links() -> None:
    sink = _Sink()
    col = AsyncCollector(sink, queue_size=128, flush_interval=0.01, batch_max=32)
    em = Emitter(col)

    @profile_function(em)
    def leaf() -> int:
        return EXPECTED_RESULT

    @profile_function(em)
    def root() -> int:
        return leaf()

    with use_span(trace_id=span_id(), span_id=span_id()):
        out = root()
        assert out == EXPECTED_RESULT

    time.sleep(0.05)
    col.close()

    # Collect metadata events
    metas = [e for e in sink if isinstance(e, dict) and e.get("kind") == "FN_META"]
    assert len(metas) >= MIN_METADATA_EVENTS

    # Find leaf and root meta
    leaf_meta = next(m for m in metas if m.get("fn", "").endswith("leaf"))
    root_meta = next(m for m in metas if m.get("fn", "").endswith("root"))

    # Both share the same trace
    assert leaf_meta["trace_id"] == root_meta["trace_id"]

    # Leaf's parent is root's span
    assert leaf_meta.get("parent_span_id") == root_meta.get("span_id")


def test_async_function_and_exception_path() -> None:
    sink = _Sink()
    col = AsyncCollector(sink, queue_size=128, flush_interval=0.01, batch_max=32)
    em = Emitter(col)

    @profile_function(em)
    async def will_fail() -> None:
        await asyncio.sleep(0)
        raise RuntimeError("nope")

    async def run() -> None:
        with suppress(RuntimeError):
            await will_fail()

    asyncio.run(run())

    time.sleep(0.05)
    col.close()

    metas = [e for e in sink if isinstance(e, dict) and e.get("kind") == "FN_META"]
    assert any(m.get("exception_type") == "RuntimeError" for m in metas)
    # Ensure at least one FN event exists for the failure path (emitted by decorator)
    assert any(e.get("kind") == "FN" or e.get("kind") is None for e in sink if isinstance(e, dict))
