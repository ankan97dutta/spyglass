# Profilis

A high‑performance, non‑blocking profiler for Python web applications.

## Features

- **Frameworks**: Flask, FastAPI, Sanic
- **Databases**: SQLAlchemy, pyodbc, MongoDB, Neo4j
- **UI**: Built‑in, real-time dashboard
- **Exporters**: JSONL (rotating), Console, Prometheus, OTLP (future)
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
- ✅ **Flask Integration**: Automatic request/response profiling
- ✅ **SQLAlchemy Instrumentation**: Query performance monitoring
- ✅ **Built-in Dashboard**: Real-time metrics and error tracking
- ✅ **JSONL Exporter**: Rotating log files with configurable retention
- ✅ **Function Profiling**: Decorator-based timing with exception tracking
- ✅ **Performance Optimized**: Non-blocking collection with configurable batching

## Documentation

- [Installation](guides/installation.md) - Complete installation guide and options
- [Getting Started](guides/getting-started.md) - Quick setup and basic usage
- [Configuration](guides/configuration.md) - Tuning and customization
- [Framework Adapters](adapters/) - Flask, FastAPI, Sanic integration
- [Database Support](databases/) - SQLAlchemy, MongoDB, Neo4j
- [Exporters](exporters/) - JSONL, Console, Prometheus
- [Architecture](architecture/) - System design and components
- [UI Dashboard](ui/) - Built-in monitoring interface
