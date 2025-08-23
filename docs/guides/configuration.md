# Configuration

Key options:
- `enabled` (bool)
- `sample_rate` (0.0..1.0)
- `route_exclude` (list/prefix/regex)
- `non_blocking` (default: true)
- `queue_size`, `flush_interval_s`, `batch_max`
- `exporter` (jsonl|prometheus|otlp)
- `jsonl_path`, rotation size/time
- `ui_enabled`, `ui_prefix`, `ui_auth_token`
