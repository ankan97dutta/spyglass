# FastAPI Adapter

> **Note**: FastAPI support is planned for v0.3.0. The current v0.1.0 release includes Flask integration and core profiling capabilities.

## Current Status

FastAPI integration is not yet available in v0.1.0. The roadmap includes:

- **v0.1.0** — Core + Flask + SQLAlchemy + UI ✅
- **v0.2.0** — pyodbc + Mongo + Neo4j
- **v0.3.0** — ASGI (FastAPI/Sanic) 🔄
- **v0.4.0** — Sampling + Prometheus + Resilience
- **v1.0.0** — Benchmarks + Docs + Release

## What's Available Now

While waiting for FastAPI support, you can use Profilis's core profiling capabilities:

### Function Profiling

```python
from profilis.decorators.profile import profile_function
from profilis.core.emitter import Emitter
from profilis.exporters.jsonl import JSONLExporter
from profilis.core.async_collector import AsyncCollector

# Setup profiling
exporter = JSONLExporter(dir="./logs")
collector = AsyncCollector(exporter)
emitter = Emitter(collector)

@profile_function(emitter)
async def fastapi_handler():
    """Profile individual FastAPI handlers"""
    # Your FastAPI logic here
    pass
```

### Manual Request Profiling

```python
from fastapi import FastAPI, Request
from profilis.core.emitter import Emitter
from profilis.exporters.jsonl import JSONLExporter
from profilis.core.async_collector import AsyncCollector
from profilis.runtime import use_span, span_id
import time

app = FastAPI()

# Setup Profilis
exporter = JSONLExporter(dir="./logs")
collector = AsyncCollector(exporter)
emitter = Emitter(collector)

@app.middleware("http")
async def profilis_middleware(request: Request, call_next):
    start_time = time.time_ns()

    # Create trace context
    with use_span(trace_id=span_id()):
        try:
            response = await call_next(request)
            duration = time.time_ns() - start_time

            # Emit request event
            emitter.emit_req(
                route=str(request.url.path),
                status=response.status_code,
                dur_ns=duration
            )

            return response
        except Exception as e:
            duration = time.time_ns() - start_time

            # Emit error event
            emitter.emit_req(
                route=str(request.url.path),
                status=500,
                dur_ns=duration
            )
            raise
```

## Planned Features for v0.3.0

The FastAPI adapter will include:

- **Automatic Request Profiling**: Middleware-based request/response timing
- **ASGI Integration**: Native ASGI middleware support
- **Route Detection**: Automatic route template identification
- **Exception Handling**: Built-in error tracking and reporting
- **Performance Optimization**: Minimal overhead for high-throughput APIs

## Alternative Solutions

### Use Flask for Now

If you need immediate profiling, consider using Flask for the profiling layer:

```python
from flask import Flask
from profilis.flask.adapter import ProfilisFlask
from profilis.exporters.jsonl import JSONLExporter
from profilis.core.async_collector import AsyncCollector

# Setup Profilis with Flask
flask_app = Flask(__name__)
exporter = JSONLExporter(dir="./logs")
collector = AsyncCollector(exporter)
profilis = ProfilisFlask(flask_app, collector=collector)

# Use the same collector for FastAPI manual profiling
# (when FastAPI support is available)
```

### Manual Instrumentation

For critical paths, use manual instrumentation:

```python
from profilis.core.emitter import Emitter
from profilis.runtime import use_span, span_id

@app.get("/api/critical")
async def critical_endpoint():
    with use_span(trace_id=span_id()):
        # Your critical logic here
        result = await expensive_operation()

        # Manual profiling
        emitter.emit_fn("expensive_operation", dur_ns=1000000)

        return result
```

## Stay Updated

- **GitHub Issues**: Track progress on [FastAPI integration](https://github.com/ankan97dutta/profilis/issues)
- **Roadmap**: See [docs/overview/roadmap.md](../overview/roadmap.md) for detailed planning
- **Discussions**: Join the conversation in [GitHub Discussions](https://github.com/ankan97dutta/profilis/discussions)

## Related Documentation

- [Getting Started](../guides/getting-started.md) - Core Profilis usage
- [Configuration](../guides/configuration.md) - Tuning and customization
- [Architecture](../architecture/) - System design and components
- [Exporters](../exporters/) - Available output formats
