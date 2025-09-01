import json
import time
from typing import Union

from flask import Flask

from profilis.core.stats import StatsStore
from profilis.flask.ui import ErrorItem, make_ui_blueprint, record_error

# HTTP status codes
HTTP_OK = 200
HTTP_UNAUTHORIZED = 401


def _mk_app(token: Union[str, None] = None) -> tuple[Flask, StatsStore]:
    app = Flask(__name__)
    stats = StatsStore()
    bp = make_ui_blueprint(stats, bearer_token=token, ui_prefix="/profilis")
    app.register_blueprint(bp)
    return app, stats


def test_metrics_json_schema_and_snapshot() -> None:
    app, stats = _mk_app()
    client = app.test_client()
    # record some events
    for i in range(10):
        stats.record(1000 * i, error=(i % 2 == 0))
    r = client.get("/profilis/metrics.json")
    assert r.status_code == HTTP_OK
    data = json.loads(r.data)
    assert "rps" in data and "p50" in data and "spark" in data


def test_dashboard_rendering_smoke() -> None:
    app, _ = _mk_app()
    client = app.test_client()
    r = client.get("/profilis/")
    assert r.status_code == HTTP_OK
    assert b"Profilis" in r.data


def test_auth_check_forbidden() -> None:
    app, _ = _mk_app(token="secret")
    client = app.test_client()
    r = client.get("/profilis/metrics.json")
    assert r.status_code == HTTP_UNAUTHORIZED
    r2 = client.get("/profilis/metrics.json", headers={"Authorization": "Bearer secret"})
    assert r2.status_code == HTTP_OK


def test_errors_ring_endpoint() -> None:
    app, _ = _mk_app()
    record_error(
        ErrorItem(
            ts_ns=time.time_ns(),
            route="/boom",
            status=500,
            exception_type="RuntimeError",
            exception_value="Test error",
            traceback="Test traceback",
        )
    )
    client = app.test_client()
    r = client.get("/profilis/errors.json")
    assert r.status_code == HTTP_OK
    data = json.loads(r.data)
    assert "errors" in data and any(e["route"] == "/boom" for e in data["errors"])
