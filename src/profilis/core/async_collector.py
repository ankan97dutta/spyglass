"""AsyncCollector: bounded, drop-oldest queue with background batch writer.

- Non-blocking enqueue (drops oldest when full)
- Background writer thread batches and flushes to a provided sink
- atexit handler drains remaining items

Configuration:
- queue_size (int): max buffer size (default 2048)
- flush_interval (float): seconds between periodic flush attempts (default 0.5s)
- batch_max (int): maximum batch size per sink call (default 256)
"""

from __future__ import annotations

import atexit
import contextlib
import threading
import time
from collections import deque
from typing import Callable, Generic, TypeVar

T = TypeVar("T")

__all__ = ["AsyncCollector"]


class AsyncCollector(Generic[T]):
    def __init__(
        self,
        sink: Callable[[list[T]], None],
        *,
        queue_size: int = 2048,
        flush_interval: float = 0.5,
        batch_max: int = 256,
        name: str = "profilis-collector",
    ) -> None:
        if queue_size <= 0:
            raise ValueError("queue_size must be > 0")
        if batch_max <= 0:
            raise ValueError("batch_max must be > 0")
        if flush_interval <= 0:
            raise ValueError("flush_interval must be > 0")

        self._sink = sink
        self._buf: deque[T] = deque()
        self._max = int(queue_size)
        self._batch_max = int(batch_max)
        self._interval = float(flush_interval)

        self._lock = threading.Lock()
        self._wakeup = threading.Event()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name=name, daemon=True)

        # Stats (best-effort; not locked on read)
        self.enqueued = 0
        self.processed = 0
        self.dropped_oldest = 0
        self.flush_errors = 0

        # Start worker and register atexit
        self._thread.start()
        atexit.register(self._atexit)

    # -------------------------- Public API --------------------------
    def enqueue(self, item: T) -> None:
        """Non-blocking enqueue.

        If the buffer is full, drop the oldest item and append the new one.
        This method never blocks on back-pressure.
        """
        with self._lock:
            if len(self._buf) >= self._max:
                # Drop-oldest
                try:
                    self._buf.popleft()
                    self.dropped_oldest += 1
                except IndexError:
                    # Very unlikely race if another thread drained; ignore
                    pass
            self._buf.append(item)
            self.enqueued += 1
        # Nudge the writer to flush sooner
        self._wakeup.set()

    def close(self, *, timeout: float = 2.0) -> None:
        """Stop the background thread and flush any remaining items."""
        if not self._stop.is_set():
            self._stop.set()
            self._wakeup.set()
            self._thread.join(timeout=timeout)
            # Final drain regardless of join result
            self._drain_all()
            # Close the sink if it has a close method
            if hasattr(self._sink, "close"):
                with contextlib.suppress(Exception):
                    self._sink.close()
            # Also try to call finalize if the sink has that method (for JSONL exporter)
            if hasattr(self._sink, "finalize"):
                with contextlib.suppress(Exception):
                    self._sink.finalize()

    # ------------------------- Internal ----------------------------
    def _atexit(self) -> None:
        # atexit safety: try to stop and drain without raising
        with contextlib.suppress(Exception):
            self.close()

    def _run(self) -> None:
        interval = self._interval
        while not self._stop.is_set():
            # Wait for either a wakeup or the periodic interval
            self._wakeup.wait(timeout=interval)
            self._wakeup.clear()
            try:
                self._flush_batches()
            except Exception:
                # Never kill the thread on sink errors
                self.flush_errors += 1
                # Back off briefly to avoid tight error loops
                time.sleep(min(0.05, interval))

    def _pop_many(self, n: int) -> list[T]:
        items: list[T] = []
        with self._lock:
            for _ in range(min(n, len(self._buf))):
                try:
                    items.append(self._buf.popleft())
                except IndexError:
                    break
        return items

    def _flush_batches(self) -> None:
        batch_max = self._batch_max
        while True:
            batch = self._pop_many(batch_max)
            if not batch:
                return
            self._sink(batch)
            self.processed += len(batch)
            # Loop to continue draining until empty to keep latency low

    def _drain_all(self) -> None:
        # Drain everything regardless of batch size
        while True:
            batch = self._pop_many(self._batch_max * 4)
            if not batch:
                break
            try:
                self._sink(batch)
                self.processed += len(batch)
            except Exception:
                self.flush_errors += 1
