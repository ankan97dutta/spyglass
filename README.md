<img width="64" height="64" alt="image" src="https://github.com/user-attachments/assets/663b4497-d023-49a6-9ce9-60c50c86df02" />

# Spyglass

> A high performance, non-blocking profiler for Python web applications.

[![Docs](https://github.com/ankan97dutta/spyglass/actions/workflows/docs.yml/badge.svg)](https://ankan97dutta.github.io/spyglass/)

---

## Overview

Spyglass provides drop-in observability across APIs, functions, and database queries with minimal performance impact. It's designed to be:

- **Non-blocking**: Async collection with configurable batching and backpressure handling
- **Framework agnostic**: Works with Flask, FastAPI, Sanic, and custom applications
- **Database aware**: Built-in support for SQLAlchemy, pyodbc, MongoDB, and Neo4j
- **Production ready**: Configurable sampling, error tracking, and multiple export formats

## Features

- **Request Profiling**: Automatic HTTP request/response timing and status tracking
- **Function Profiling**: Decorator-based function timing with exception tracking
- **Database Instrumentation**: Query performance monitoring with row counts
- **Built-in UI**: Real-time dashboard for monitoring and debugging
- **Multiple Exporters**: JSONL (with rotation), Console, Prometheus, OTLP
- **Runtime Context**: Distributed tracing with trace/span ID management
- **Configurable Sampling**: Control data collection volume in production

## Installation

Install the core package with optional dependencies for your specific needs:

### Option 1: Using pip with extras (Recommended)

```bash
# Core package only
pip install spyglass

# With Flask support
pip install spyglass[flask]

# With database support
pip install spyglass[flask,sqlalchemy]

# With all integrations
pip install spyglass[all]
```

### Option 2: Using requirements files

```bash
# Minimal setup (core only)
pip install -r requirements-minimal.txt

# Flask integration
pip install -r requirements-flask.txt

# SQLAlchemy integration
pip install -r requirements-sqlalchemy.txt

# All integrations
pip install -r requirements-all.txt
```

### Option 3: Manual installation

```bash
# Core dependencies
pip install typing_extensions>=4.0

# Flask support
pip install flask[async]>=3.0

# SQLAlchemy support
pip install sqlalchemy>=2.0 aiosqlite greenlet

# Performance optimization
pip install orjson>=3.8
```

## Quick Start

### Flask Integration

```python
from flask import Flask
from spyglass.flask.adapter import SpyglassFlask
from spyglass.exporters.jsonl import JSONLExporter
from spyglass.core.async_collector import AsyncCollector

# Setup exporter and collector
exporter = JSONLExporter(dir="./logs", rotate_bytes=1024*1024, rotate_secs=3600)
collector = AsyncCollector(exporter, queue_size=2048, batch_max=128, flush_interval=0.1)

# Create Flask app and integrate Spyglass
app = Flask(__name__)
spyglass = SpyglassFlask(
    app,
    collector=collector,
    exclude_routes=["/health", "/metrics"],
    sample=1.0  # 100% sampling
)

@app.route('/api/users')
def get_users():
    return {"users": ["alice", "bob"]}

# Start the app
if __name__ == "__main__":
    app.run(debug=True)
```

### Function Profiling

```python
from spyglass.decorators.profile import profile_function
from spyglass.core.emitter import Emitter
from spyglass.exporters.console import ConsoleExporter
from spyglass.core.async_collector import AsyncCollector

# Setup profiling
exporter = ConsoleExporter(pretty=True)
collector = AsyncCollector(exporter, queue_size=128, flush_interval=0.2)
emitter = Emitter(collector)

@profile_function(emitter)
def expensive_calculation(n: int) -> int:
    """This function will be automatically profiled."""
    result = sum(i * i for i in range(n))
    return result

@profile_function(emitter)
async def async_operation(data: list) -> list:
    """Async functions are also supported."""
    processed = [item * 2 for item in data]
    return processed

# Use the profiled functions
result = expensive_calculation(1000)
```

### Manual Event Emission

```python
from spyglass.core.emitter import Emitter
from spyglass.exporters.jsonl import JSONLExporter
from spyglass.core.async_collector import AsyncCollector
from spyglass.runtime import use_span, span_id

# Setup
exporter = JSONLExporter(dir="./logs")
collector = AsyncCollector(exporter)
emitter = Emitter(collector)

# Create a trace context
with use_span(trace_id=span_id()):
    # Emit custom events
    emitter.emit_req("/api/custom", 200, dur_ns=15000000)  # 15ms
    emitter.emit_fn("custom_function", dur_ns=5000000)      # 5ms
    emitter.emit_db("SELECT * FROM users", dur_ns=8000000, rows=100)

# Close collector to flush remaining events
collector.close()
```

### Built-in Dashboard

```python
from flask import Flask
from spyglass.flask.ui import make_ui_blueprint
from spyglass.core.stats import StatsStore

app = Flask(__name__)
stats = StatsStore()  # 15-minute rolling window

# Mount the dashboard at /_spyglass
ui_bp = make_ui_blueprint(stats, ui_prefix="/_spyglass")
app.register_blueprint(ui_bp)

# Visit http://localhost:5000/_spyglass to see the dashboard
```

## Advanced Usage

### Custom Exporters

```python
from spyglass.core.async_collector import AsyncCollector
from spyglass.exporters.base import BaseExporter

class CustomExporter(BaseExporter):
    def export(self, events: list[dict]) -> None:
        for event in events:
            # Custom export logic
            print(f"Custom export: {event}")

# Use custom exporter
exporter = CustomExporter()
collector = AsyncCollector(exporter)
```

### Runtime Context Management

```python
from spyglass.runtime import use_span, span_id, get_trace_id, get_span_id

# Create distributed trace context
with use_span(trace_id="trace-123", span_id="span-456"):
    current_trace = get_trace_id()  # "trace-123"
    current_span = get_span_id()    # "span-456"

    # Nested spans inherit trace context
    with use_span(span_id="span-789"):
        nested_span = get_span_id()  # "span-789"
        parent_trace = get_trace_id() # "trace-123"
```

### Performance Tuning

```python
from spyglass.core.async_collector import AsyncCollector

# High-throughput configuration
collector = AsyncCollector(
    exporter,
    queue_size=8192,        # Large queue for high concurrency
    batch_max=256,          # Larger batches for efficiency
    flush_interval=0.05,    # More frequent flushing
    drop_oldest=True        # Drop events under backpressure
)

# Low-latency configuration
collector = AsyncCollector(
    exporter,
    queue_size=512,         # Smaller queue for lower latency
    batch_max=32,           # Smaller batches for faster processing
    flush_interval=0.01,    # Very frequent flushing
    drop_oldest=False       # Don't drop events
)
```

## Configuration

### Environment Variables

```bash
# Enable debug mode
export SPYGLASS_DEBUG=1

# Set default log directory
export SPYGLASS_LOG_DIR=/var/log/spyglass

# Configure sampling rate (0.0 to 1.0)
export SPYGLASS_SAMPLE_RATE=0.1
```

### Sampling Strategies

```python
# Random sampling
spyglass = SpyglassFlask(app, collector=collector, sample=0.1)  # 10% of requests

# Route-based sampling
spyglass = SpyglassFlask(
    app,
    collector=collector,
    exclude_routes=["/health", "/metrics", "/static"],
    sample=1.0
)
```

## Exporters

### JSONL Exporter
```python
from spyglass.exporters.jsonl import JSONLExporter

# With rotation
exporter = JSONLExporter(
    dir="./logs",
    rotate_bytes=1024*1024,  # 1MB per file
    rotate_secs=3600         # Rotate every hour
)
```

### Console Exporter
```python
from spyglass.exporters.console import ConsoleExporter

# Pretty-printed output
exporter = ConsoleExporter(pretty=True)

# Compact output
exporter = ConsoleExporter(pretty=False)
```

### Prometheus Exporter
```python
from spyglass.exporters.prometheus import PrometheusExporter

exporter = PrometheusExporter(
    port=9090,
    addr="0.0.0.0"
)
```

## Performance Characteristics

- **Event Creation**: ≤15µs per event
- **Memory Overhead**: ~100 bytes per event
- **Throughput**: 100K+ events/second on modern hardware
- **Latency**: Sub-millisecond collection overhead

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
