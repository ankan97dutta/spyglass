#!/usr/bin/env bash
set -euo pipefail

# Auto-detect repository info from git if not set
if [[ -z "${GH_OWNER:-}" || -z "${GH_REPO:-}" ]]; then
  if [[ -d .git ]]; then
    REMOTE_URL=$(git remote get-url origin)
    if [[ "$REMOTE_URL" =~ github\.com[:/]([^/]+)/([^/]+)\.git ]]; then
      GH_OWNER="${BASH_REMATCH[1]}"
      GH_REPO="${BASH_REMATCH[2]}"
      echo "Auto-detected: GH_OWNER=$GH_OWNER, GH_REPO=$GH_REPO"
    else
      echo "Error: Could not parse GitHub URL from git remote"
      exit 1
    fi
  else
    echo "Error: GH_OWNER and GH_REPO must be set, or run from a git repository"
    exit 1
  fi
fi

MS="v0.4.0 – Sampling/Prometheus/Resilience"

issue() {
  local title="$1"; shift
  local body="$1"; shift
  gh issue create -R "$GH_OWNER/$GH_REPO" -t "$title" -b "$body" -m "$MS" "$@"
}

issue "Sampling policies: global rate, per-route overrides, always-on errors" \
"### Subtasks
- Global \`sample_rate\` (0.0..1.0)
- Route excludes (prefix/regex) + per-route overrides
- Always sample 5xx responses
- Seedable RNG for deterministic tests

### Acceptance
- Sampling rules honored in integration; 5xx always sampled

### Tests
- Deterministic RNG unit tests
- Matrix tests across routes & error paths
" -l "type:core" -l "type:perf"

issue "Prometheus exporter: counters & histograms + label plan" \
"### Subtasks
- HTTP: \`profilis_http_requests_total\`, \`profilis_http_request_duration_seconds\` (histogram)
- Functions: \`profilis_function_calls_total\`, \`profilis_function_duration_seconds\` (histogram)
- DB: \`profilis_db_queries_total\`, \`profilis_db_query_duration_seconds\` (histogram)
- Labels: service, instance, worker, route/status, function, db_vendor
- Buckets: [0.005,0.01,0.025,0.05,0.1,0.25,0.5,1,2,5,10]
- Expose /metrics (Flask+ASGI)

### Acceptance
- Prometheus can scrape; sample panels render

### Tests
- Bucket math unit tests; scrape smoke test
" -l "type:exporter" -l "type:perf"

issue "Reliability: exporter/collector failure modes + graceful shutdown" \
"### Subtasks
- Disk-full fallback (noop writer + warn once)
- Collector crash handling (disable or respawn safely)
- Graceful shutdown: best-effort flush with timeout; never block exit
- Health metrics: \`profilis_events_dropped_total\`, \`profilis_queue_depth\`

### Acceptance
- Requests unaffected by failures; shutdown within timeout

### Tests
- Fault injection (raise in exporter; simulate disk full)
- Verify counters increment for drops
" -l "type:core"

echo "Created v0.4.0 issues on $GH_OWNER/$GH_REPO"
