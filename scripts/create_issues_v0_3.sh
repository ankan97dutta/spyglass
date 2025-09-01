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

MS="v0.3.0 – ASGI/FastAPI + Sanic"

issue() {
  local title="$1"; shift
  local body="$1"; shift
  gh issue create -R "$GH_OWNER/$GH_REPO" -t "$title" -b "$body" -m "$MS" "$@"
}

issue "ASGI middleware (Starlette base)" \
"### Subtasks
- Intercept \`http\` scope; route from \`scope.route.path_format\` when available
- Capture method, path, status, latency; exceptions with type
- Ensure ContextVar trace propagation
- Config: sampling, route excludes, always-sample errors

### Acceptance
- Works on Starlette demo app; no metrics for websocket scope

### Tests
- Starlette TestClient: 200/400/500; exception path
" -l "type:adapter" -l "area:fastapi"

issue "FastAPI adapter (thin on top of ASGI)" \
"### Subtasks
- Validate route template extraction with APIRouter & dependencies
- Ensure background tasks / StreamingResponse do not break metrics
- Docs: mounting UI app, example app

### Acceptance
- FastAPI sample app emits correct route templates and statuses

### Tests
- FastAPI TestClient: async endpoints; background tasks
" -l "type:adapter" -l "area:fastapi"

issue "Sanic adapter (native) + optional ASGI UI mount" \
"### Subtasks
- Sanic request/response middleware; exception capture
- Optionally mount ASGI UI at /\_profilis
- Docs: example app

### Acceptance
- Sanic routes emit metrics; ASGI UI serves metrics on mount

### Tests
- Sanic test client: concurrency (100 tasks), success/error routes
" -l "type:adapter" -l "area:sanic"

echo "Created v0.3.0 issues on $GH_OWNER/$GH_REPO"
