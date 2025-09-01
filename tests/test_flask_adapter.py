import asyncio
import os
import tempfile
import time
from typing import Any

from flask import Flask, abort

from profilis.core.async_collector import AsyncCollector
from profilis.flask.adapter import ProfilisFlask

# HTTP status code constants
HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_INTERNAL_SERVER_ERROR = 500


class _Sink(list[dict[str, Any]]):
    def __call__(self, batch: list[dict[str, Any]]) -> None:
        self.extend(batch)


def _mk_app(tmpdir: str) -> Flask:
    app = Flask(__name__, static_folder=os.path.join(tmpdir, "static"))
    if app.static_folder is not None:
        os.makedirs(app.static_folder, exist_ok=True)
        with open(os.path.join(app.static_folder, "hello.txt"), "w", encoding="utf-8") as f:
            f.write("hi")

    return app


def test_flask_requests_200_400_500_and_static() -> None:
    tmp = tempfile.mkdtemp()
    app = _mk_app(tmp)

    sink = _Sink()
    col = AsyncCollector(sink, queue_size=256, flush_interval=0.01, batch_max=64)
    ProfilisFlask(app, collector=col, exclude_routes=["/health", "/metrics"], sample=1.0)

    @app.route("/ok")
    def ok() -> dict[str, bool]:
        return {"ok": True}

    @app.route("/bad")
    def bad() -> Any:
        abort(400)

    @app.route("/boom")
    def boom() -> Any:
        raise RuntimeError("boom")

    client = app.test_client()
    assert client.get("/ok").status_code == HTTP_OK
    assert client.get("/bad").status_code == HTTP_BAD_REQUEST

    # Don't catch the exception - let Flask handle it so Profilis can capture it
    response = client.get("/boom")
    assert (
        response.status_code == HTTP_INTERNAL_SERVER_ERROR
    )  # Flask should return 500 for unhandled exceptions

    # static file served
    r = client.get("/static/hello.txt")
    assert r.status_code == HTTP_OK

    # allow collector to flush
    time.sleep(0.05)
    col.close()

    kinds = [e.get("kind") for e in sink if isinstance(e, dict)]
    assert "REQ" in kinds
    assert "REQ_META" in kinds

    # Check for errors by looking at status codes in REQ events
    req_events = [e for e in sink if isinstance(e, dict) and e.get("kind") == "REQ"]
    has_error_by_status = any(e.get("status", HTTP_OK) >= HTTP_BAD_REQUEST for e in req_events)

    # Also check for exception_type as a fallback
    has_error_by_exception = any(
        e.get("exception_type") for e in sink if e.get("kind") == "REQ_META"
    )

    # Either method should detect the error
    assert has_error_by_status or has_error_by_exception, (
        f"No errors detected. Status-based: {has_error_by_status}, Exception-based: {has_error_by_exception}"
    )


def test_async_view() -> None:
    app = Flask(__name__)
    sink = _Sink()
    col = AsyncCollector(sink, queue_size=64, flush_interval=0.01, batch_max=16)
    ProfilisFlask(app, collector=col, sample=1.0)

    @app.route("/await")
    async def awaiter() -> dict[str, bool]:
        await asyncio.sleep(0)
        return {"ok": True}

    client = app.test_client()
    assert client.get("/await").status_code == HTTP_OK

    time.sleep(0.05)
    col.close()

    assert any(e.get("kind") == "REQ" for e in sink)
