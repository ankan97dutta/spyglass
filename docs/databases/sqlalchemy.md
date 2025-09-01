# SQLAlchemy Instrumentation

Profilis provides automatic SQLAlchemy query profiling with minimal configuration.

## Quick Start

```python
from sqlalchemy import create_engine
from profilis.sqlalchemy.instrumentation import instrument_engine
from profilis.core.emitter import Emitter
from profilis.exporters.jsonl import JSONLExporter
from profilis.core.async_collector import AsyncCollector

# Setup Profilis
exporter = JSONLExporter(dir="./logs")
collector = AsyncCollector(exporter)
emitter = Emitter(collector)

# Create SQLAlchemy engine
engine = create_engine("sqlite:///app.db")

# Instrument the engine
instrument_engine(engine, emitter)

# All queries will now be automatically profiled
```

### Async SQLAlchemy Support

```python
from sqlalchemy.ext.asyncio import create_async_engine
from profilis.sqlalchemy.instrumentation import instrument_async_engine

# Create async engine
async_engine = create_async_engine("sqlite+aiosqlite:///app.db")

# Instrument the async engine
emitter = Emitter(collector)
instrument_async_engine(async_engine, emitter)

# All async queries will now be automatically profiled
```

## Features

### Automatic Query Profiling
- **Query Timing**: Measures execution time with microsecond precision
- **Row Counts**: Tracks number of rows returned/affected
- **Query Text**: Captures actual SQL queries (with redaction support)
- **Async Support**: Works with both sync and async engines
- **Performance Metrics**: Tracks slow queries and bottlenecks

### Performance Optimized
- **Non-blocking**: All profiling happens asynchronously
- **Minimal Overhead**: ≤15µs per query profiling cost
- **Batch Processing**: Efficient event collection and export
- **Memory Efficient**: Lightweight event representation

## Configuration

### Basic Instrumentation

```python
from profilis.sqlalchemy.instrumentation import instrument_engine
from profilis.core.emitter import Emitter

# Simple instrumentation
emitter = Emitter(collector)
instrument_engine(engine, emitter)

# With custom options
instrument_engine(
    engine,
    emitter,
    redact=True,              # Hide sensitive data (default: True)
    max_len=200               # Maximum query length (default: 200)
)
```

### Advanced Configuration

```python
# Production configuration
instrument_engine(
    engine,
    emitter,
    redact=True,                   # Always redact in production (default)
    max_len=500                    # Truncate very long queries
)
```

## What Gets Profiled

### Database Events (DB)
Each SQL query generates a `DB` event:

```json
{
  "ts_ns": 1703123456789000000,
  "trace_id": "trace-abc123",
  "span_id": "span-def456",
  "kind": "DB",
  "query": "SELECT * FROM users WHERE id = ?",
  "dur_ns": 5000000,
  "rows": 1,
  "engine": "sqlite:///app.db"
}
```

**Fields:**
- **`ts_ns`**: Timestamp in nanoseconds
- **`trace_id`**: Current trace identifier (if in trace context)
- **`span_id`**: Current span identifier (if in span context)
- **`query`**: SQL query text (may be redacted)
- **`dur_ns`**: Query execution time in nanoseconds
- **`rows`**: Number of rows returned/affected
- **`engine`**: Database engine identifier

### Query Metadata (DB_META)
Additional query information is recorded:

```json
{
  "kind": "DB_META",
  "ts_ns": 1703123456789000000,
  "trace_id": "trace-abc123",
  "span_id": "span-def456",
  "query_hash": "abc123def456",
  "query_type": "SELECT",
  "table": "users",
  "parameters": {"id": 123}
}
```

## Integration Patterns

### With Flask Adapter

```python
from flask import Flask
from profilis.flask.adapter import ProfilisFlask
from profilis.sqlalchemy.instrumentation import instrument_engine
from profilis.core.emitter import Emitter

# Setup Flask with Profilis
app = Flask(__name__)
profilis = ProfilisFlask(app, collector=collector)

# Instrument SQLAlchemy
engine = create_engine("sqlite:///app.db")
emitter = Emitter(collector)
instrument_engine(engine, emitter)

# Now Flask requests and SQL queries are automatically correlated
@app.route('/api/users/<user_id>')
def get_user(user_id):
    # This query will be automatically profiled and linked to the request
    user = engine.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return {"user": user}
```

### With Function Profiling

```python
from profilis.decorators.profile import profile_function

@profile_function(emitter)
def get_user_data(user_id: int):
    """Profile both function execution and database queries"""
    # SQLAlchemy queries are automatically profiled
    user = engine.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    posts = engine.execute("SELECT * FROM posts WHERE user_id = ?", (user_id,)).fetchall()
    return {"user": user, "posts": posts}
```

### With Runtime Context

```python
from profilis.runtime import use_span, span_id

def process_user_batch(user_ids: list[int]):
    """Process multiple users with distributed tracing"""
    with use_span(trace_id=span_id()):
        for user_id in user_ids:
            with use_span(span_id=span_id()):
                # Each query inherits the trace context
                user = engine.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
                # Process user data...
```

## Query Redaction

### Automatic Redaction

```python
# Enable query redaction (recommended for production)
instrument_sqlalchemy(
    engine,
    collector,
    redact_queries=True
)

# Queries with sensitive data are automatically redacted
# Original: SELECT * FROM users WHERE email = 'user@example.com' AND password = 'secret'
# Redacted: SELECT * FROM users WHERE email = ? AND password = ?
```

### Custom Redaction Rules

```python
import re
from profilis.sqlalchemy.instrumentation import instrument_sqlalchemy

def custom_redactor(query: str) -> str:
    """Custom query redaction logic"""
    # Redact email addresses
    query = re.sub(r"'[^']*@[^']*'", "?", query)
    # Redact credit card numbers
    query = re.sub(r"'[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{4}'", "?", query)
    return query

instrument_sqlalchemy(
    engine,
    collector,
    redact_queries=True,
    query_redactor=custom_redactor
)
```

## Performance Tuning

### Query Length Limiting

```python
# Limit query text length to reduce memory usage
instrument_engine(
    engine,
    emitter,
    max_len=100  # Truncate queries longer than 100 characters
)
```

### Redaction Control

```python
# Disable redaction for debugging (not recommended for production)
instrument_engine(
    engine,
    emitter,
    redact=False  # Show full query text
)
```

**Note**: The current implementation profiles all queries. For high-volume applications, consider implementing sampling at the collector level or using route-based sampling in Flask.

## Monitoring and Alerting

### Slow Query Detection

```python
import logging

logger = logging.getLogger(__name__)

def monitor_slow_queries(collector):
    """Monitor for slow database queries"""
    # This would be implemented based on your monitoring strategy
    pass

# Example: Alert on queries > 1 second
SLOW_QUERY_THRESHOLD = 1_000_000_000  # 1 second in nanoseconds
```

### Query Performance Metrics

```python
from collections import defaultdict
import statistics

class QueryAnalyzer:
    def __init__(self):
        self.query_stats = defaultdict(list)

    def analyze_query(self, query: str, duration_ns: int):
        """Analyze query performance"""
        self.query_stats[query].append(duration_ns)

        # Alert on slow queries
        if duration_ns > 1_000_000_000:  # 1 second
            logger.warning(f"Slow query detected: {query} ({duration_ns/1_000_000:.2f}ms)")

    def get_stats(self):
        """Get query performance statistics"""
        stats = {}
        for query, durations in self.query_stats.items():
            stats[query] = {
                "count": len(durations),
                "avg_ms": statistics.mean(durations) / 1_000_000,
                "max_ms": max(durations) / 1_000_000,
                "min_ms": min(durations) / 1_000_000
            }
        return stats
```

## Testing

### Unit Testing

```python
import pytest
from profilis.exporters.console import ConsoleExporter

@pytest.fixture
def test_collector():
    """Test collector for unit tests"""
    exporter = ConsoleExporter(pretty=False)
    return AsyncCollector(exporter, queue_size=128, flush_interval=0.01)

@pytest.fixture
def test_engine(test_collector):
    """Test engine with Profilis instrumentation"""
    engine = create_engine("sqlite:///:memory:")
    emitter = Emitter(test_collector)
    instrument_engine(engine, emitter)
    return engine

def test_query_profiling(test_engine, test_collector):
    """Test that queries are profiled"""
    # Execute a query
    result = test_engine.execute("SELECT 1").fetchone()

    # Verify profiling data was collected
    # (Implementation depends on your testing strategy)
    assert result[0] == 1
```

### Integration Testing

```python
def test_sqlalchemy_integration(test_engine, test_collector):
    """Test SQLAlchemy integration with Profilis"""
    # Create test data
    test_engine.execute("CREATE TABLE test (id INTEGER, name TEXT)")
    test_engine.execute("INSERT INTO test VALUES (1, 'test')")

    # Query the data
    result = test_engine.execute("SELECT * FROM test WHERE id = 1").fetchone()

    # Verify the result
    assert result[0] == 1
    assert result[1] == 'test'
```

## Troubleshooting

### Common Issues

1. **No Events Generated**: Ensure the collector is properly configured
2. **Missing Query Text**: Check if redaction is enabled
3. **Performance Impact**: Use sampling and filtering for high-volume applications
4. **Async Engine Issues**: Ensure proper async context setup

### Debug Mode

```python
import os
os.environ['PROFILIS_DEBUG'] = '1'

# This will enable debug logging for SQLAlchemy instrumentation
emitter = Emitter(collector)
instrument_engine(engine, emitter)
```

### Health Checks

```python
def check_sqlalchemy_instrumentation(engine, collector):
    """Check if SQLAlchemy instrumentation is working"""
    try:
        # Execute a simple query
        result = engine.execute("SELECT 1").fetchone()

        # Check if events were generated
        # (Implementation depends on your monitoring strategy)

        return True
    except Exception as e:
        logger.error(f"SQLAlchemy instrumentation check failed: {e}")
        return False
```

## Best Practices

1. **Enable Redaction**: Always enable query redaction in production (default behavior)
2. **Limit Query Length**: Use `max_len` to prevent very long queries from consuming memory
3. **Monitor Performance**: Track query performance metrics over time
4. **Use Async Engines**: For async applications, use `instrument_async_engine()` with async SQLAlchemy engines
5. **Test Thoroughly**: Test instrumentation in your specific environment
6. **Review Queries**: Regularly review profiled queries for optimization opportunities
7. **Correlate with Requests**: Use the same collector for both Flask and SQLAlchemy to correlate requests with queries
