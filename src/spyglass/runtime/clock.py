"""High-resolution, monotonic clock.


- now_ns(): nanoseconds from an arbitrary, monotonic reference (perf_counter_ns)
"""

from __future__ import annotations

import time

__all__ = ["now_ns"]


def now_ns() -> int:
    """Return a monotonically increasing timestamp in nanoseconds.


    Uses time.perf_counter_ns() for high-resolution timing unaffected by
    system clock adjustments. Suitable for interval measurement.
    """
    return time.perf_counter_ns()
