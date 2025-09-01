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

MS="v1.0.0 – Benchmarks + Docs Hardening"

issue() {
  local title="$1"; shift
  local body="$1"; shift
  gh issue create -R "$GH_OWNER/$GH_REPO" -t "$title" -b "$body" -m "$MS" "$@"
}

issue "Benchmarks: Flask/FastAPI/Sanic load profiles" \
"### Subtasks
- Demo apps for each framework; Make targets
- Load tests with hey/wrk; Locust soak (30–60 min)
- Record p50/p95 deltas with/without profilis; events/min; CPU%
- Tuning guide: queue size, flush interval, sampling

### Acceptance
- Published, reproducible numbers in \`bench/\` (scripts + results)

### Tests
- Microbench in CI via \`pytest-benchmark\` (stable thresholds)
" -l "type:perf"

issue "Docs: Quickstarts, API reference, dashboards" \
"### Subtasks
- README quickstarts (Flask/FastAPI/Sanic); DB adapters (SQLAlchemy/pyodbc/Mongo/Neo4j)
- API reference (MkDocs/Sphinx) + gh-pages
- Example Prometheus rules + Grafana JSON
- Security & troubleshooting guides

### Acceptance
- Docs build & publish; examples run end-to-end

### Tests
- Doc snippets validated (doctest or run-snippets in CI)
" -l "type:ui"

issue "Release engineering: TestPyPI → PyPI + changelog" \
"### Subtasks
- Semantic versioning; \`CHANGELOG.md\` (Keep a Changelog)
- Build sdist/wheels; verify install on clean runners
- TestPyPI publish & smoke install; then PyPI
- GitHub Release with notes; (optional) signing/provenance

### Acceptance
- \`pip install profilis[flask,sqlalchemy]\` quickstart works on clean envs

### Tests
- CI builds wheels on Linux/macOS/Windows; smoke install 3.9–3.12
" -l "type:core"

echo "Created v1.0.0 issues on $GH_OWNER/$GH_REPO"
