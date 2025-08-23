<img width="64" height="64" alt="image" src="https://github.com/user-attachments/assets/663b4497-d023-49a6-9ce9-60c50c86df02" />

# Spyglass

> A high performance, non blocking profiler for Python web apps.

[![Docs](https://github.com/ankan97dutta/spyglass/actions/workflows/docs.yml/badge.svg)](https://ankan97dutta.github.io/spyglass/)

---

## Overview
Spyglass provides drop‑in observability across APIs, functions, and database queries, with:
- **Frameworks**: Flask, FastAPI, Sanic
- **Databases**: SQLAlchemy, pyodbc, MongoDB, Neo4j
- **UI**: Built‑in minified dashboard
- **Exporters**: JSONL (rotating), Prometheus, OTLP (future)

## Installation

```bash
pip install spyglass[flask,sqlalchemy]
```

## Quick start

```python
from flask import Flask
from spyglass.integrations.flask_ext import SpyglassFlask

app = Flask(__name__)
sg = SpyglassFlask(app, ui_enabled=True, ui_prefix="/_spyglass")

@app.get('/health')
def ok():
    return {"ok": True}
# Visit http://localhost:5000/_spyglass for the dashboard
```

## Documentation

Full documentation is available at: [Spyglass Docs](https://ankan97dutta.github.io/spyglass/)

Docs are written in Markdown under [`docs/`](./docs) and built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/).

To preview locally:
```bash
pip install mkdocs mkdocs-material mkdocs-mermaid2-plugin
mkdocs serve
```

## Development

- See [Contributing](./docs/meta/contributing.md) and [Development Guidelines](./docs/meta/development-guidelines.md).
- Branch strategy: trunk‑based (`feat/*`, `fix/*`, `perf/*`, `chore/*`).
- Commits follow [Conventional Commits](https://www.conventionalcommits.org/).

## Roadmap

See [Spyglass – v0 Roadmap Project](https://github.com/ankan97dutta/spyglass/projects) and [`docs/overview/roadmap.md`](./docs/overview/roadmap.md).

## License

[MIT](./LICENSE)
