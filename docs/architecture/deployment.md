# Deployment

- Per‑process queue + writer thread (no cross‑process locks).
- Prometheus scrapes per‑worker /metrics.
- JSONL rotates; ship with fluent‑bit/vector.

Graceful shutdown: keep serving until in‑flight requests finish, then **best‑effort flush with timeout**.
