# Getting Started

## Installation

Install Spyglass with the dependencies you need:

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

### What Each Option Provides

- **`spyglass` (core)**: Basic profiling with Emitter and AsyncCollector
- **`spyglass[flask]`**: Core + Flask request/response profiling
- **`spyglass[sqlalchemy]`**: Core + SQLAlchemy query profiling
- **`spyglass[perf]`**: Core + orjson for faster JSON serialization
- **`spyglass[all]`**: Everything including all frameworks and databases

## Quick Start with Flask

Here's a minimal Flask application with Spyglass integration:

```python
from flask import Flask
from spyglass.flask.adapter import SpyglassFlask
from spyglass.exporters.jsonl import JSONLExporter
from spyglass.core.async_collector import AsyncCollector

# Setup exporter and collector
exporter = JSONLExporter(dir="./logs", rotate_bytes=1024*1024, rotate_secs=3600)
collector = AsyncCollector(exporter, queue_size=2048, batch_max=128, flush_interval=0.1)

# Create Flask app
app = Flask(__name__)

# Integrate Spyglass
spyglass = SpyglassFlask(
    app,
    collector=collector,
    exclude_routes=["/health", "/metrics"],
    sample=1.0  # 100% sampling
)

@app.route('/api/users')
def get_users():
    return {"users": ["alice", "bob"]}

@app.route('/health')
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(debug=True)
```

## Function Profiling

Use the `@profile_function` decorator to profile specific functions:

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

## Built-in Dashboard

Enable the built-in dashboard for real-time monitoring:

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

## Manual Event Emission

For custom instrumentation, use the Emitter directly:

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

## What's Available in v0.1.0

### Core Components
- **AsyncCollector**: Non-blocking event collection with configurable batching
- **Emitter**: High-performance event creation and emission
- **Runtime Context**: Distributed tracing with trace/span ID management

### Framework Support
- **Flask**: Automatic request/response profiling with hooks
- **SQLAlchemy**: Query performance monitoring and instrumentation

### Exporters
- **JSONL**: Rotating log files with configurable retention
- **Console**: Pretty-printed output for development

### UI
- **Built-in Dashboard**: Real-time metrics, error tracking, and performance visualization

### Decorators
- **@profile_function**: Automatic timing for sync and async functions

## Next Steps

- [Configuration](configuration.md) - Learn about tuning and customization
- [Framework Adapters](../adapters/) - Explore Flask, FastAPI, and Sanic integration
- [Database Support](../databases/) - Understand SQLAlchemy and other database integrations
- [Exporters](../exporters/) - Configure different output formats
- [Architecture](../architecture/) - Learn about the system design
