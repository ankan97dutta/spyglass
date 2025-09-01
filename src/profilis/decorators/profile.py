"""@profile_function decorator (sync/async) with nesting support.

- Inherits current trace; creates a new span per invocation
- Attaches parent_span_id when nesting is detected
- Records exceptions (exception_type on FN_META) and re-raises

Usage:
    from profilis.decorators.profile import profile_function

    collector = AsyncCollector(JSONLExporter(...))
    emitter = Emitter(collector)

    @profile_function(emitter)
    def work(x):
        return x * 2

    @profile_function(emitter)
    async def a_work(x):
        await asyncio.sleep(0)
        return x
"""

from __future__ import annotations

import asyncio
import functools
from typing import Callable, TypeVar

from typing_extensions import ParamSpec

from profilis.core.emitter import Emitter
from profilis.runtime import get_span_id, get_trace_id, now_ns, span_id, use_span

P = ParamSpec("P")
T = TypeVar("T")

__all__ = ["profile_function"]


def profile_function(emitter: Emitter) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator factory that profiles sync/async callables.

    Emits:
      - FN (name, dur_ns, error flag)
      - FN_META (trace/span IDs + parent_span_id + exception_type when set)
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        is_async = asyncio.iscoroutinefunction(func)
        name = getattr(func, "__qualname__", getattr(func, "__name__", "<fn>"))

        if not is_async:

            @functools.wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                parent_span = get_span_id()
                trace = get_trace_id() or span_id()
                child = span_id()
                start = now_ns()
                exc_type: str | None = None
                with use_span(trace_id=trace, span_id=child):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:  # record and re-raise
                        exc_type = type(e).__name__
                        raise
                    finally:
                        dur = now_ns() - start
                        emitter.emit_fn(name, dur_ns=dur, error=exc_type is not None)
                        # FN_META carries linkage + exception_type
                        emitter._collector.enqueue(
                            {
                                "kind": "FN_META",
                                "fn": name,
                                "ts_ns": now_ns(),
                                "trace_id": trace,
                                "span_id": child,
                                "parent_span_id": parent_span,
                                "exception_type": exc_type,
                            }
                        )

            return wrapper

        else:
            # For async functions, we need to handle the fact that the return type
            # is actually Awaitable[T] when called, but the decorator signature
            # expects Callable[P, T]. This is a limitation of the current typing system.
            # We'll use a type ignore comment for this specific case.

            @functools.wraps(func)
            async def awrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                parent_span = get_span_id()
                trace = get_trace_id() or span_id()
                child = span_id()
                start = now_ns()
                exc_type: str | None = None
                with use_span(trace_id=trace, span_id=child):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        exc_type = type(e).__name__
                        raise
                    finally:
                        dur = now_ns() - start
                        emitter.emit_fn(name, dur_ns=dur, error=exc_type is not None)
                        emitter._collector.enqueue(
                            {
                                "kind": "FN_META",
                                "fn": name,
                                "ts_ns": now_ns(),
                                "trace_id": trace,
                                "span_id": child,
                                "parent_span_id": parent_span,
                                "exception_type": exc_type,
                            }
                        )

            return awrapper  # type: ignore[return-value]

    return decorator
