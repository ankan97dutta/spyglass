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

MS="v0.2.0 – pyodbc + Mongo + Neo4j"

issue() {
  local title="$1"; shift
  local body="$1"; shift
  gh issue create -R "$GH_OWNER/$GH_REPO" -t "$title" -b "$body" -m "$MS" "$@"
}

issue "pyodbc raw wrapper (execute/executemany)" \
"### Subtasks
- Wrap cursor.execute / executemany (non-invasive)
- Capture sql text (preview), params (redacted), duration, rowcount
- Config: vendor label (e.g., mssql), statement redaction, preview length
- Handle errors: still emit with exception flag
- Docs: usage snippet & pitfalls (autocommit, context managers)

### Acceptance
- Metrics recorded without changing cursor semantics
- Works with SQL Server and SQLite/pyodbc in CI

### Tests
- Mock cursor: timing + argument pass-through
- (Optional) SQL Server container; else sqlite/odbc fallback
" -l "type:db" -l "area:pyodbc"

issue "MongoDB adapter: PyMongo + Motor (async)" \
"### Subtasks
- Register CommandListener (started/succeeded/failed)
- Build preview: \`<cmd> db.collection\` (redacted)
- Include success flag; counters from reply (n, nModified) when present
- Ensure Motor compatibility (async)
- Docs: installation, minimal example

### Acceptance
- Works with PyMongo and Motor
- Commands recorded: find, insert, update, delete, aggregate

### Tests
- Mongo container: sync + async tests
- Failure path (CommandFailedEvent) emits with exception info
" -l "type:db" -l "area:mongo"

issue "Neo4j adapter: sync + async driver wrappers" \
"### Subtasks
- Wrap Session.run / Tx.run (sync) and AsyncSession.run / tx.run (async)
- Capture cypher (redacted), duration, counters from summary
- Support parent_span_id from current trace
- Docs: usage with GraphDatabase / AsyncGraphDatabase

### Acceptance
- Sync & async drivers emit metrics; counters populated where available

### Tests
- Neo4j container: create/match queries; counters validated
- Error path emits with exception_type
" -l "type:db" -l "area:neo4j"

echo "Created v0.2.0 issues on $GH_OWNER/$GH_REPO"
