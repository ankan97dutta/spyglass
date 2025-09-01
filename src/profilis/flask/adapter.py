"""Flask adapter: request hooks, exceptions, sampling, and bytes in/out.

Usage:
    from profilis.flask.adapter import ProfilisFlask
    app = Flask(__name__)
    ProfilisFlask(app, collector=my_collector, exclude_routes=["/health", "/metrics"], sample=1.0)

Guarantees:
- One REQ metric per request (success or error) with route template if available
- Exceptions recorded with `exception_type`
- Bytes in/out captured best-effort
"""

from __future__ import annotations

import contextlib
import random
import typing as _t
from dataclasses import dataclass

from flask import Flask, g, request

from profilis.core.async_collector import AsyncCollector
from profilis.core.emitter import Emitter
from profilis.runtime import now_ns, span_id, use_span

# HTTP status code constants
HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_INTERNAL_SERVER_ERROR = 500


@dataclass
class _ReqState:
    start_ns: int
    bytes_in: int
    route: str
    span: str
    trace: str
    sampled: bool
    exception_type: str | None = None


class ProfilisFlask:
    def __init__(
        self,
        app: Flask,
        *,
        collector: AsyncCollector[dict[str, _t.Any]],
        exclude_routes: list[str] | None = None,
        sample: float = 1.0,
    ) -> None:
        self.app = app
        self.collector = collector
        self.emitter = Emitter(collector)
        self.exclude_routes = tuple(exclude_routes or ())
        self.sample = float(sample)

        self._register_hooks()

    # ----------------- Flask hook wiring -----------------
    def _register_hooks(self) -> None:
        app = self.app

        @app.before_request
        def _sg_before_request() -> None:  # type: ignore[unused-ignore]
            self._handle_before_request()

        @app.after_request
        def _sg_after_request(response: _t.Any) -> _t.Any:  # type: ignore[unused-ignore]
            return self._handle_after_request(response)

        @app.teardown_request
        def _sg_teardown_request(exc: _t.Any) -> None:  # type: ignore[unused-ignore,type-var,arg-type]
            self._handle_teardown_request(exc)

    def _handle_before_request(self) -> None:
        path = request.path or "/"
        # Exclusions by prefix
        for exc in self.exclude_routes:
            if path.startswith(exc):
                g._profilis_state = None
                return None

        # Sampling
        sampled = random.random() < self.sample
        if not sampled:
            g._profilis_state = None
            return None

        # Route template detection
        route_tpl = self._get_route_template(path)

        # Bytes in
        bytes_in = self._get_bytes_in()

        # Assign new trace/span and stash timing
        trace = span_id()
        span = span_id()
        g._profilis_ctx = use_span(trace_id=trace, span_id=span)
        # Enter the span context now; __enter__ called explicitly
        g._profilis_ctx.__enter__()

        g._profilis_state = _ReqState(
            start_ns=now_ns(),
            bytes_in=bytes_in,
            route=route_tpl,
            span=span,
            trace=trace,
            sampled=True,
        )
        return None

    def _get_route_template(self, path: str) -> str:
        """Get the route template from the request."""
        route_tpl = path
        try:
            if request.url_rule is not None and request.url_rule.rule:
                route_tpl = request.url_rule.rule  # type: ignore[attr-defined]
        except Exception:
            pass
        return route_tpl

    def _get_bytes_in(self) -> int:
        """Get the number of bytes in the request."""
        bytes_in = int(request.content_length or 0)
        if bytes_in == 0:
            try:
                data = request.get_data(cache=False, as_text=False, parse_form_data=False)  # type: ignore[arg-type]
                bytes_in = len(data or b"")
            except Exception:
                bytes_in = 0
        return bytes_in

    def _handle_after_request(self, response: _t.Any) -> _t.Any:
        st: _ReqState | None = getattr(g, "_profilis_state", None)
        if st is None:
            return response

        # Bytes out best-effort
        bytes_out = self._get_bytes_out(response)

        dur_ns = now_ns() - st.start_ns
        status = getattr(response, "status_code", HTTP_OK)
        error = bool(st.exception_type) or (status >= HTTP_INTERNAL_SERVER_ERROR)

        self.emitter.emit_req(
            route=st.route,
            status=status,
            dur_ns=dur_ns,
        )
        # Also emit a function-level metric with error marker for dashboards
        if error:
            self.emitter.emit_fn("flask.request", dur_ns=dur_ns, error=True)
        else:
            self.emitter.emit_fn("flask.request", dur_ns=dur_ns, error=False)

        # Attach bytes and context as a lightweight DB event (so they get stored)
        self.collector.enqueue(
            {
                "kind": "REQ_META",
                "route": st.route,
                "bytes_in": st.bytes_in,
                "bytes_out": int(bytes_out),
                "exception_type": st.exception_type,
                "ts_ns": now_ns(),
                "trace_id": st.trace,
                "span_id": st.span,
            }
        )
        return response

    def _get_bytes_out(self, response: _t.Any) -> int:
        """Get the number of bytes out in the response."""
        try:
            bytes_out = response.calculate_content_length() or 0
            if bytes_out == 0:
                data = response.get_data(as_text=False)
                bytes_out = len(data or b"")
        except Exception:
            bytes_out = 0
        return bytes_out

    def _handle_teardown_request(self, exc: _t.Any) -> None:
        st: _ReqState | None = getattr(g, "_profilis_state", None)
        if st is not None and exc is not None:
            # Remember exception type for after_request emission
            st.exception_type = getattr(exc, "__class__", type(exc)).__name__
        # Exit span context if we entered it
        ctx = getattr(g, "_profilis_ctx", None)
        if ctx is not None:
            with contextlib.suppress(Exception):
                ctx.__exit__(None, None, None)
