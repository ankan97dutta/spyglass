#!/usr/bin/env bash
set -euo pipefail
: "${GH_OWNER:?}"; : "${GH_REPO:?}"

MS="v0.1.0 – Core + Flask + SQLAlchemy + UI"
MNUM="$(gh api repos/$GH_OWNER/$GH_REPO/milestones --jq ".[] | select(.title==\"$MS\") | .number")"

issue() {
  local title="$1"; shift
  local body="$1"; shift
  gh issue create -R "$GH_OWNER/$GH_REPO" -t "$title" -b "$body" -m "$MNUM" "$@"
}

issue "Scaffold repo & toolchain" \
"**Goal**: Project skeleton with strict quality gates.

### Subtasks
- Create \`src/profilis\`, \`tests\`, \`examples\`, \`pyproject.toml\` (extras: flask, fastapi, sanic, sqlalchemy, pyodbc, mongo, neo4j, perf, all)
- Add \`README.md\`, \`LICENSE\`, \`CONTRIBUTING.md\`, \`py.typed\`
- Configure ruff/black, mypy (strict), pre-commit
- CI: lint/type/tests on 3.9–3.12; wheel build

### Acceptance
- \`pip install -e .\` works; CI green across versions; wheels built

### Tests
- Sanity import; mypy/ruff pass; coverage ≥ 85%
" -l "type:core"

issue "Core runtime: ContextVar + ids + fast clocks" \
"### Subtasks
- Implement \`span_id()\` via 64-bit hex
- Implement \`now_ns()\` via \`perf_counter_ns()\`
- ContextVar store for trace/span (async-safe)

### Acceptance
- No locks on hot path; safe across async

### Tests
- ID uniqueness; ContextVar propagation in async
" -l "type:core" -l "type:perf"

issue "AsyncCollector (bounded, drop-oldest) + batch writer" \
"### Subtasks
- Non-blocking enqueue; drop-oldest on full
- Writer thread: batch flush; \`atexit\` flush
- Config: \`queue_size\`, \`flush_interval\`, \`batch_max\`

### Acceptance
- No blocking under back-pressure

### Tests
- Burst 10× queue size → no errors; atexit drains
" -l "type:core" -l "type:perf"

issue "Emitter hot path + StatsStore (15m window)" \
"### Subtasks
- Emitter builds tiny dicts and enqueues (REQ/FN/DB)
- Stats: RPS, error%, p50/p95, 60s sparkline

### Acceptance
- Enqueue cost ≤ 15µs/event on dev hardware

### Tests
- Microbenchmarks; percentile math property tests
" -l "type:core" -l "type:perf"

issue "Exporters: JSONL (rotating) + Console (+orjson optional)" \
"### Subtasks
- JSONL writer with size/time rotation & atomic rename
- Console exporter; \`[perf]\` extra uses \`orjson\`

### Acceptance
- Rotation creates \`profilis-YYYYmmdd-HHMMSS.jsonl\`

### Tests
- Rotation by size/time; unicode-safe writes
" -l "type:exporter"

issue "Flask adapter: request hooks + exceptions + bytes" \
"### Subtasks
- \`before_request/after_request/teardown_request\`
- Route template detection; bytes in/out
- Exception capture with \`exception_type\`
- Sampling + route exclusions (\`/health\`, \`/metrics\`)

### Acceptance
- One metric per request; exceptions recorded

### Tests
- Flask client: 200/400/500; async view; static route
" -l "type:adapter" -l "area:flask"

issue "@profile_function decorator (sync/async) + nesting" \
"### Subtasks
- Sync/async wrapper; inherit current trace
- Set \`parent_span_id\`; record exceptions

### Acceptance
- Nested spans correlate correctly

### Tests
- Nested call graph; exception path
" -l "type:core"

issue "SQLAlchemy (sync/async) engine instrumentation + redaction" \
"### Subtasks
- Hook \`before/after_cursor_execute\` on Engine and AsyncEngine.sync_engine
- Rowcount when available
- \`redact_statement\` (strings/numerics → ?, max len)

### Acceptance
- Metrics for sync/async engines; statements redacted by default

### Tests
- SQLite (sync/async) integration; redaction unit tests
" -l "type:db" -l "area:sqlalchemy"

issue "Built-in UI: JSON endpoint + HTML dashboard (Flask)" \
"### Subtasks
- \`/metrics.json\` (StatsStore snapshot)
- Minified HTML (KPIs, routes, DB top, functions, sparkline)
- Bearer token auth; \`ui_enabled\`, \`ui_prefix\`

### Acceptance
- Live updates every 4s; 401 if token missing (when configured)

### Tests
- JSON schema snapshot; auth check; rendering smoke
" -l "type:ui" -l "area:flask"

echo "Created v0.1.0 issues on $GH_OWNER/$GH_REPO"
