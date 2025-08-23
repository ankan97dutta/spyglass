"""Async-safe trace/span context using ContextVar.


Provides minimal helpers + a context manager for ergonomic usage without locks.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Optional

__all__ = [
    "get_trace_id",
    "get_span_id",
    "set_trace_id",
    "set_span_id",
    "reset_trace_id",
    "reset_span_id",
    "use_span",
]

# None means "unset". Keep defaults at module import for speed; ContextVar is async-safe.
_TRACE_ID: ContextVar[Optional[str]] = ContextVar("spyglass_trace_id", default=None)
_SPAN_ID: ContextVar[Optional[str]] = ContextVar("spyglass_span_id", default=None)


# --- Getters ---
def get_trace_id() -> Optional[str]:
    return _TRACE_ID.get()


def get_span_id() -> Optional[str]:
    return _SPAN_ID.get()


# --- Setters returning tokens for manual reset ---
def set_trace_id(value: Optional[str]) -> Token[Optional[str]]:
    return _TRACE_ID.set(value)


def set_span_id(value: Optional[str]) -> Token[Optional[str]]:
    return _SPAN_ID.set(value)


# --- Reset helpers ---


def reset_trace_id(token: Token[Optional[str]]) -> None:
    _TRACE_ID.reset(token)


def reset_span_id(token: Token[Optional[str]]) -> None:
    _SPAN_ID.reset(token)


# --- Ergonomic context manager ---
@contextmanager
def use_span(trace_id: Optional[str] = None, span_id: Optional[str] = None) -> Iterator[None]:
    """Temporarily set trace/span IDs (async-safe). Resets on exit.


    Parameters may be None to leave a value unchanged.
    """
    ttoken = stoken = None
    try:
        if trace_id is not None:
            ttoken = set_trace_id(trace_id)
        if span_id is not None:
            stoken = set_span_id(span_id)
        yield
    finally:
        # Reset only what we set
        if stoken is not None:
            reset_span_id(stoken)
        if ttoken is not None:
            reset_trace_id(ttoken)
