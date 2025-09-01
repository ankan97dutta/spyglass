# Profilis

A high‑performance, non‑blocking profiler for Python web applications.

## Features

- **Frameworks**: Flask ✅, FastAPI (planned v0.3.0), Sanic (planned v0.3.0)
- **Databases**: SQLAlchemy ✅ (sync & async), pyodbc (planned v0.2.0), MongoDB (planned v0.2.0), Neo4j (planned v0.2.0)
- **UI**: Built‑in, real-time dashboard ✅
- **Exporters**: JSONL (rotating) ✅, Console ✅, Prometheus (planned v0.4.0), OTLP (planned v0.4.0)
- **Performance**: ≤15µs per event, 100K+ events/second

## Quick start (Flask)

```bash
pip install profilis[flask,sqlalchemy]
```

```python
from flask import Flask
from profilis.flask.adapter import ProfilisFlask
from profilis.exporters.jsonl import JSONLExporter
from profilis.core.async_collector import AsyncCollector

# Setup exporter and collector
exporter = JSONLExporter(dir="./logs", rotate_bytes=1024*1024, rotate_secs=3600)
collector = AsyncCollector(exporter, queue_size=2048, batch_max=128, flush_interval=0.1)

# Create Flask app and integrate Profilis
app = Flask(__name__)
profilis = ProfilisFlask(
    app,
    collector=collector,
    exclude_routes=["/health", "/metrics"],
    sample=1.0
)

@app.route('/health')
def ok():
    return {'ok': True}

# Visit /_profilis for the dashboard
```

## What's New in v0.1.0

- ✅ **Core Profiling Engine**: AsyncCollector, Emitter, and runtime context
- ✅ **Flask Integration**: Automatic request/response profiling with hooks
- ✅ **SQLAlchemy Instrumentation**: Both sync and async engine support with query redaction
- ✅ **Built-in Dashboard**: Real-time metrics and error tracking with authentication
- ✅ **JSONL Exporter**: Rotating log files with configurable retention
- ✅ **Function Profiling**: Decorator-based timing for sync/async functions with exception tracking
- ✅ **Performance Optimized**: Non-blocking collection with configurable batching and drop-oldest policy

## Documentation

- [Installation](guides/installation.md) - Complete installation guide and options
- [Getting Started](guides/getting-started.md) - Quick setup and basic usage
- [Configuration](guides/configuration.md) - Tuning and customization
- [Framework Adapters](adapters/flask.md) - Flask integration, FastAPI (planned)
- [Database Support](databases/sqlalchemy.md) - SQLAlchemy integration
- [Exporters](exporters/jsonl.md) - JSONL and Console exporters
- [Architecture](architecture/architecture.md) - System design and components
- [UI Dashboard](ui/ui.md) - Built-in monitoring interface
