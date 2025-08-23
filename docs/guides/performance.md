# Performance

- Hot path: ~10–20µs per event
- Use `perf` extra (`orjson`)
- Tuning: queue_size, batch_max, flush_interval
- Prefer Prometheus aggregates in high‑QPS paths
