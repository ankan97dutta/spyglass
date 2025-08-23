#!/usr/bin/env bash
set -euo pipefail
: "${GH_OWNER:?}"; : "${GH_REPO:?}"

mklabel() { gh label create "$1" -R "$GH_OWNER/$GH_REPO" -c "$2" -d "${3:-}" 2>/dev/null || true; }

# Labels
mklabel "type:core"        "1f6feb" "Core runtime, plumbing"
mklabel "type:adapter"     "8957e5" "Framework adapters"
mklabel "type:db"          "a5d6ff" "Database integrations"
mklabel "type:ui"          "0e8a16" "Built-in UI"
mklabel "type:exporter"    "ffb302" "Exporters & sinks"
mklabel "type:perf"        "d73a4a" "Performance work"
mklabel "area:flask"       "1f6feb" ""
mklabel "area:fastapi"     "1f6feb" ""
mklabel "area:sanic"       "1f6feb" ""
mklabel "area:sqlalchemy"  "8957e5" ""
mklabel "area:pyodbc"      "8957e5" ""
mklabel "area:mongo"       "8957e5" ""
mklabel "area:neo4j"       "8957e5" ""
mklabel "good first issue" "7057ff" ""
mklabel "help wanted"      "008672" ""
mklabel "blocked"          "e11d21" ""

# Milestones
mkms() { gh milestone create "$1" -R "$GH_OWNER/$GH_REPO" 2>/dev/null || true; }
mkms "v0.1.0 – Core + Flask + SQLAlchemy + UI"
mkms "v0.2.0 – pyodbc + Mongo + Neo4j"
mkms "v0.3.0 – ASGI/FastAPI + Sanic"
mkms "v0.4.0 – Sampling/Prometheus/Resilience"
mkms "v1.0.0 – Benchmarks + Docs Hardening"

echo "Labels + milestones ready on $GH_OWNER/$GH_REPO"
