"""StatsStore: rolling 15-minute window with RPS, error%, percentiles, sparkline."""

from __future__ import annotations

import math
import time
from collections import deque
from typing import Any

__all__ = ["StatsStore"]

# Constants for magic numbers
SPARKLINE_BINS = 60  # Number of 1-second bins for sparkline
PERCENT_MAX = 100  # Maximum percentage value


class StatsStore:
    def __init__(self, window_sec: int = 900):
        self._window = window_sec
        self._events: deque[tuple[float, float, bool]] = deque()
        # each item: (ts, dur_ms, error)

    def record(self, dur_ns: int, error: bool = False) -> None:
        now = time.time()
        dur_ms = dur_ns / 1e6
        self._events.append((now, dur_ms, error))
        self._trim(now)

    def _trim(self, now: float) -> None:
        cutoff = now - self._window
        while self._events and self._events[0][0] < cutoff:
            self._events.popleft()

    def snapshot(self) -> dict[str, Any]:
        now = time.time()
        self._trim(now)
        evs = list(self._events)
        n = len(evs)
        if n == 0:
            return {"rps": 0, "error_pct": 0.0, "p50": None, "p95": None, "spark": []}
        # RPS = events/sec over last window
        span = max(evs[-1][0] - evs[0][0], 1e-6)
        rps = n / span
        errors = sum(1 for _, _, e in evs if e)
        error_pct = errors * PERCENT_MAX / n
        durs = sorted(d for _, d, _ in evs)

        def pct(p: float) -> float | None:
            if not durs:
                return None
            k = (len(durs) - 1) * p
            f = math.floor(k)
            c = math.ceil(k)
            if f == c:
                return durs[int(k)]
            return durs[f] * (c - k) + durs[c] * (k - f)

        p50 = pct(0.5)
        p95 = pct(0.95)
        # sparkline: last 60s, 1s bins
        bins = [0] * SPARKLINE_BINS
        for ts, _, _ in evs:
            ago = int(now - ts)
            if 0 <= ago < SPARKLINE_BINS:
                bins[SPARKLINE_BINS - 1 - ago] += 1
        return {"rps": rps, "error_pct": error_pct, "p50": p50, "p95": p95, "spark": bins}
