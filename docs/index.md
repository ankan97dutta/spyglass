# Spyglass

A high‑performance, non‑blocking profiler for Python web apps.

- **Frameworks**: Flask, FastAPI, Sanic
- **Databases**: SQLAlchemy, pyodbc, MongoDB, Neo4j
- **UI**: Built‑in, minified dashboard
- **Exporters**: JSONL (rotating), Prometheus, OTLP (future)

## Quick start (Flask)
```bash
pip install spyglass[flask,sqlalchemy]
```
```python
from flask import Flask
from spyglass.integrations.flask_ext import SpyglassFlask
app = Flask(__name__)
sg = SpyglassFlask(app, ui_enabled=True, ui_prefix="/_spyglass")
@app.get('/health')
def ok(): return {'ok': True}
# Visit /_spyglass for the dashboard
```
