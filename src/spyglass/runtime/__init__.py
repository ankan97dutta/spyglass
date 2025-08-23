"""Minimal core runtime API for IDs, clocks, and async-safe context.


Acceptance:
- No locks on the hot path
- Async-safe via ContextVar


Public API surface exported here for convenience.
"""
from .ids import span_id
from .clock import now_ns
from .context import (
get_trace_id,
get_span_id,
set_trace_id,
set_span_id,
reset_trace_id,
reset_span_id,
use_span,
)


__all__ = [
"span_id",
"now_ns",
"get_trace_id",
"get_span_id",
"set_trace_id",
"set_span_id",
"reset_trace_id",
"reset_span_id",
"use_span",
]