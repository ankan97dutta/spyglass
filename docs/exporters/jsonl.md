# JSONL Exporter

The JSONL (JSON Lines) exporter writes profiling events to rotating log files in JSONL format.

## Quick Start

```python
from spyglass.exporters.jsonl import JSONLExporter
from spyglass.core.async_collector import AsyncCollector

# Basic setup
exporter = JSONLExporter(dir="./logs")
collector = AsyncCollector(exporter)

# With rotation
exporter = JSONLExporter(
    dir="./logs",
    rotate_bytes=1024*1024,  # 1MB per file
    rotate_secs=3600         # Rotate every hour
)
```

## Features

### File Management
- **Automatic Rotation**: Rotate files by size or time
- **Atomic Writes**: Safe file rotation with atomic renames
- **Configurable Retention**: Control file sizes and rotation intervals
- **Timestamped Names**: Automatic timestamp-based file naming

### Performance
- **Non-blocking**: Asynchronous file I/O
- **Buffered Writes**: Efficient batch writing
- **Compression Ready**: Easy integration with compression tools
- **Low Memory**: Minimal memory footprint

## Configuration

### Basic Configuration

```python
from spyglass.exporters.jsonl import JSONLExporter

# Simple setup
exporter = JSONLExporter(dir="./logs")

# With custom directory
exporter = JSONLExporter(dir="/var/log/spyglass")
```

### Rotation Configuration

```python
# Rotate by size only
exporter = JSONLExporter(
    dir="./logs",
    rotate_bytes=10*1024*1024  # 10MB per file
)

# Rotate by time only
exporter = JSONLExporter(
    dir="./logs",
    rotate_secs=86400  # Daily rotation
)

# Rotate by both size and time
exporter = JSONLExporter(
    dir="./logs",
    rotate_bytes=100*1024*1024,  # 100MB per file
    rotate_secs=86400             # Daily rotation
)
```

### Advanced Configuration

```python
# Production configuration
exporter = JSONLExporter(
    dir="/var/log/spyglass",
    rotate_bytes=100*1024*1024,  # 100MB files
    rotate_secs=86400,            # Daily rotation
    filename_template="spyglass-{timestamp}.jsonl",
    compress_old_files=True,      # Compress rotated files
    max_files=30                  # Keep last 30 files
)
```

## File Naming

### Default Naming
By default, files are named with timestamps:

```
logs/
├── spyglass-20241227-120000.jsonl    # 12:00 rotation
├── spyglass-20241227-130000.jsonl    # 13:00 rotation
├── spyglass-20241227-140000.jsonl    # 14:00 rotation
└── spyglass-20241227-150000.jsonl    # Current file
```

### Custom Naming
Use custom filename templates:

```python
# Custom template
exporter = JSONLExporter(
    dir="./logs",
    filename_template="app-{timestamp}-{index}.jsonl"
)

# Result: app-20241227-120000-001.jsonl

# With application name
exporter = JSONLExporter(
    dir="./logs",
    filename_template="{app_name}-{timestamp}.jsonl",
    app_name="myapp"
)

# Result: myapp-20241227-120000.jsonl
```

## Event Format

### Request Events
```json
{"ts_ns": 1703123456789000000, "trace_id": "trace-abc123", "span_id": "span-def456", "kind": "REQ", "route": "/api/users", "status": 200, "dur_ns": 15000000}
{"ts_ns": 1703123456790000000, "trace_id": "trace-abc124", "span_id": "span-def457", "kind": "REQ", "route": "/api/users/1", "status": 200, "dur_ns": 8000000}
```

### Function Events
```json
{"ts_ns": 1703123456791000000, "trace_id": "trace-abc123", "span_id": "span-def458", "kind": "FN", "fn": "get_user_data", "dur_ns": 12000000, "error": false}
```

### Database Events
```json
{"ts_ns": 1703123456792000000, "trace_id": "trace-abc123", "span_id": "span-def459", "kind": "DB", "query": "SELECT * FROM users WHERE id = ?", "dur_ns": 5000000, "rows": 1}
```

## Integration Examples

### With Flask

```python
from flask import Flask
from spyglass.flask.adapter import SpyglassFlask
from spyglass.exporters.jsonl import JSONLExporter
from spyglass.core.async_collector import AsyncCollector

# Setup JSONL exporter
exporter = JSONLExporter(
    dir="./logs",
    rotate_bytes=1024*1024,  # 1MB per file
    rotate_secs=3600         # Hourly rotation
)

collector = AsyncCollector(exporter)

# Integrate with Flask
app = Flask(__name__)
spyglass = SpyglassFlask(app, collector=collector)
```

### With Multiple Exporters

```python
from spyglass.exporters.console import ConsoleExporter
from spyglass.exporters.jsonl import JSONLExporter
from spyglass.core.async_collector import AsyncCollector

# Development: Console + JSONL
if app.debug:
    console_exporter = ConsoleExporter(pretty=True)
    jsonl_exporter = JSONLExporter(dir="./logs")

    # Use both exporters
    collector = AsyncCollector([console_exporter, jsonl_exporter])
else:
    # Production: JSONL only
    jsonl_exporter = JSONLExporter(
        dir="/var/log/spyglass",
        rotate_bytes=100*1024*1024,
        rotate_secs=86400
    )
    collector = AsyncCollector(jsonl_exporter)
```

### With Custom Event Processing

```python
from spyglass.exporters.jsonl import JSONLExporter
from spyglass.core.async_collector import AsyncCollector
import json

class CustomJSONLExporter(JSONLExporter):
    def export(self, events: list[dict]) -> None:
        """Custom export logic"""
        for event in events:
            # Add custom fields
            event['exported_at'] = time.time()
            event['environment'] = 'production'

            # Write to file
            line = json.dumps(event, separators=(',', ':')) + '\n'
            self._write_line(line)

# Use custom exporter
exporter = CustomJSONLExporter(dir="./logs")
collector = AsyncCollector(exporter)
```

## File Management

### Automatic Cleanup

```python
# Keep only last 10 files
exporter = JSONLExporter(
    dir="./logs",
    rotate_bytes=1024*1024,
    max_files=10
)

# Keep files for 7 days
exporter = JSONLExporter(
    dir="./logs",
    rotate_secs=86400,
    max_age_secs=7*86400
)
```

### Manual Cleanup

```python
import os
import glob
from datetime import datetime, timedelta

def cleanup_old_files(log_dir: str, max_age_days: int = 7):
    """Manually cleanup old log files"""
    cutoff = datetime.now() - timedelta(days=max_age_days)

    for file_path in glob.glob(os.path.join(log_dir, "*.jsonl")):
        file_time = datetime.fromtimestamp(os.path.getctime(file_path))
        if file_time < cutoff:
            os.remove(file_path)
            print(f"Removed old file: {file_path}")

# Cleanup old files
cleanup_old_files("./logs", max_age_days=30)
```

## Monitoring and Health Checks

### Exporter Health

```python
def check_exporter_health(exporter: JSONLExporter) -> dict:
    """Check exporter health status"""
    try:
        # Check if directory is writable
        test_file = os.path.join(exporter.dir, "health-check.tmp")
        with open(test_file, 'w') as f:
            f.write("health check")
        os.remove(test_file)

        # Check current file status
        current_file = exporter._get_current_file_path()
        file_size = os.path.getsize(current_file) if os.path.exists(current_file) else 0

        return {
            "status": "healthy",
            "directory": exporter.dir,
            "current_file": current_file,
            "current_file_size": file_size,
            "rotation_config": {
                "rotate_bytes": exporter.rotate_bytes,
                "rotate_secs": exporter.rotate_secs
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

### File Size Monitoring

```python
import os
from pathlib import Path

def monitor_log_directory(log_dir: str) -> dict:
    """Monitor log directory usage"""
    path = Path(log_dir)

    if not path.exists():
        return {"error": "Directory does not exist"}

    total_size = sum(f.stat().st_size for f in path.rglob('*.jsonl'))
    file_count = len(list(path.rglob('*.jsonl')))

    return {
        "directory": log_dir,
        "total_size_bytes": total_size,
        "total_size_mb": total_size / (1024 * 1024),
        "file_count": file_count,
        "files": [
            {
                "name": f.name,
                "size_bytes": f.stat().st_size,
                "modified": f.stat().st_mtime
            }
            for f in path.glob('*.jsonl')
        ]
    }
```

## Performance Tuning

### Buffer Configuration

```python
# Large buffers for high throughput
exporter = JSONLExporter(
    dir="./logs",
    buffer_size=64*1024  # 64KB buffer
)

# Small buffers for low latency
exporter = JSONLExporter(
    dir="./logs",
    buffer_size=4*1024   # 4KB buffer
)
```

### Compression

```python
import gzip

class CompressedJSONLExporter(JSONLExporter):
    def _write_line(self, line: str) -> None:
        """Write compressed lines"""
        compressed = gzip.compress(line.encode('utf-8'))
        self._current_file.write(compressed)

# Use compressed exporter
exporter = CompressedJSONLExporter(
    dir="./logs",
    filename_template="spyglass-{timestamp}.jsonl.gz"
)
```

## Troubleshooting

### Common Issues

1. **Permission Errors**: Ensure write permissions to the log directory
2. **Disk Space**: Monitor available disk space for log rotation
3. **File Locks**: Check for file locking issues during rotation
4. **Performance**: Adjust buffer sizes for your workload

### Debug Mode

```python
import os
os.environ['SPYGLASS_DEBUG'] = '1'

# This will enable debug logging for the JSONL exporter
exporter = JSONLExporter(dir="./logs")
```

### Log Rotation Issues

```python
def diagnose_rotation_issues(exporter: JSONLExporter):
    """Diagnose log rotation problems"""
    issues = []

    # Check directory permissions
    if not os.access(exporter.dir, os.W_OK):
        issues.append(f"Directory {exporter.dir} is not writable")

    # Check disk space
    statvfs = os.statvfs(exporter.dir)
    free_space = statvfs.f_frsize * statvfs.f_bavail
    if free_space < exporter.rotate_bytes:
        issues.append(f"Insufficient disk space: {free_space} bytes available")

    # Check current file
    current_file = exporter._get_current_file_path()
    if os.path.exists(current_file):
        file_size = os.path.getsize(current_file)
        if file_size > exporter.rotate_bytes:
            issues.append(f"Current file exceeds rotation size: {file_size} > {exporter.rotate_bytes}")

    return issues
```

## Best Practices

1. **Use Appropriate Rotation**: Balance file size vs. rotation frequency
2. **Monitor Disk Usage**: Set up alerts for disk space
3. **Implement Cleanup**: Use automatic or manual cleanup strategies
4. **Test Rotation**: Verify rotation works in your environment
5. **Backup Strategy**: Consider backup and archival policies
6. **Performance Monitoring**: Monitor exporter performance impact
