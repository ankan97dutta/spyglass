import threading
import time

from profilis.core.async_collector import AsyncCollector


def test_non_blocking_and_drop_oldest_under_burst() -> None:
    received = []
    lock = threading.Lock()

    def sink(batch: list[int]) -> None:
        # Simulate lightweight sink
        with lock:
            received.extend(batch)

    qsize = 100
    col = AsyncCollector(sink, queue_size=qsize, flush_interval=0.05, batch_max=32)

    total = qsize * 10  # burst 10x queue size
    for i in range(total):
        col.enqueue(i)

    # Allow some flush cycles
    time.sleep(0.3)
    col.close()

    # Accounting: processed + dropped == enqueued
    assert col.enqueued == total
    assert col.processed + col.dropped_oldest == total

    # Sanity: we should have received at most the newest ~qsize items
    assert len(received) == col.processed
    assert col.flush_errors == 0


def test_close_drains_remaining_items() -> None:
    received = []

    def sink(batch: list[int]) -> None:
        received.extend(batch)

    col = AsyncCollector(sink, queue_size=16, flush_interval=1.0, batch_max=8)

    for i in range(25):
        col.enqueue(i)

    # Without waiting for the periodic flush, close should drain all
    col.close()

    assert col.processed + col.dropped_oldest == col.enqueued
    assert len(received) == col.processed


def test_atexit_handler_is_safe_to_call() -> None:
    # This exercises the atexit path without relying on interpreter shutdown
    received = []

    def sink(batch: list[int]) -> None:
        received.extend(batch)

    col = AsyncCollector(sink, queue_size=8, flush_interval=10.0, batch_max=8)
    for i in range(20):
        col.enqueue(i)

    # Call the atexit hook directly
    col._atexit()

    # Everything should be drained or accounted as dropped
    assert col.processed + col.dropped_oldest == col.enqueued
    assert len(received) == col.processed
