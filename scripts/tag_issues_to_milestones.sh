#!/usr/bin/env bash
set -euo pipefail

# Optional: set these if you're not already inside the repo dir
: "${GH_OWNER:=}"
: "${GH_REPO:=}"

# If owner/repo not set, try to infer from current git remote
if [[ -z "${GH_OWNER}" || -z "${GH_REPO}" ]]; then
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    origin="$(git config --get remote.origin.url || true)"
    if [[ "$origin" =~ github.com[:/](.+)/(.+)\.git ]]; then
      GH_OWNER="${BASH_REMATCH[1]}"
      GH_REPO="${BASH_REMATCH[2]}"
    fi
  fi
fi

if [[ -z "${GH_OWNER}" || -z "${GH_REPO}" ]]; then
  echo "Set GH_OWNER and GH_REPO (e.g., export GH_OWNER=you GH_REPO=spyglass), or run inside a cloned repo."
  exit 2
fi

echo "🔍 Working with repository: ${GH_OWNER}/${GH_REPO}"

# Helper: get milestone ID by title
get_milestone_id() {
  local title="$1"
  gh api "repos/${GH_OWNER}/${GH_REPO}/milestones" --jq ".[] | select(.title == \"$title\") | .number" 2>/dev/null || echo ""
}

# Helper: assign issue to milestone
assign_to_milestone() {
  local issue_number="$1"
  local milestone_number="$2"
  local milestone_title="$3"
  
  if [[ -n "$milestone_number" ]]; then
    echo "➕ Assigning issue #$issue_number to milestone: $milestone_title"
    gh api "repos/${GH_OWNER}/${GH_REPO}/issues/$issue_number" \
      -f milestone="$milestone_number" >/dev/null
  else
    echo "⚠️  Milestone not found: $milestone_title"
  fi
}

# Get all open issues
echo "📋 Fetching open issues..."
ISSUES=$(gh issue list --state open --json number,title,labels --limit 100)

# Define milestone mapping based on issue labels and content
# This mapping logic can be customized based on your project structure
map_issue_to_milestone() {
  local issue_number="$1"
  local title="$2"
  local labels="$3"
  
  # Convert labels to lowercase for easier matching
  local labels_lower=$(echo "$labels" | tr '[:upper:]' '[:lower:]')
  
  # v0.1.0 – Core + Flask + SQLAlchemy + UI
  if [[ "$labels_lower" =~ "type:core" ]] || \
     [[ "$labels_lower" =~ "area:flask" ]] || \
     [[ "$labels_lower" =~ "area:sqlalchemy" ]] || \
     [[ "$labels_lower" =~ "type:ui" ]] || \
     [[ "$title" =~ [Ff]lask ]] || \
     [[ "$title" =~ [Ss]QLAlchemy ]] || \
     [[ "$title" =~ [Uu]I ]]; then
    echo "v0.1.0 – Core + Flask + SQLAlchemy + UI"
    return 0
  fi
  
  # v0.2.0 – pyodbc + Mongo + Neo4j
  if [[ "$labels_lower" =~ "type:db" ]] || \
     [[ "$title" =~ [Mm]ongo ]] || \
     [[ "$title" =~ [Nn]eo4j ]] || \
     [[ "$title" =~ [Pp]yodbc ]]; then
    echo "v0.2.0 – pyodbc + Mongo + Neo4j"
    return 0
  fi
  
  # v0.3.0 – ASGI/FastAPI + Sanic
  if [[ "$labels_lower" =~ "type:adapter" ]] || \
     [[ "$title" =~ [Aa]SGI ]] || \
     [[ "$title" =~ [Ff]astAPI ]] || \
     [[ "$title" =~ [Ss]anic ]]; then
    echo "v0.3.0 – ASGI/FastAPI + Sanic"
    return 0
  fi
  
  # v0.4.0 – Sampling/Prometheus/Resilience
  if [[ "$labels_lower" =~ "type:exporter" ]] || \
     [[ "$labels_lower" =~ "type:perf" ]] || \
     [[ "$title" =~ [Ss]ampling ]] || \
     [[ "$title" =~ [Pp]rometheus ]] || \
     [[ "$title" =~ [Rr]esilience ]]; then
    echo "v0.4.0 – Sampling/Prometheus/Resilience"
    return 0
  fi
  
  # v1.0.0 – Benchmarks + Docs Hardening
  if [[ "$title" =~ [Bb]enchmark ]] || \
     [[ "$title" =~ [Dd]oc ]] || \
     [[ "$title" =~ [Rr]elease ]] || \
     [[ "$title" =~ [Ss]caffold ]] || \
     [[ "$title" =~ [Tt]oolchain ]]; then
    echo "v1.0.0 – Benchmarks + Docs Hardening"
    return 0
  fi
  
  # Default to v0.1.0 for core infrastructure
  echo "v0.1.0 – Core + Flask + SQLAlchemy + UI"
}

# Process each issue
echo "🏷️  Processing issues and assigning to milestones..."
echo "$ISSUES" | jq -r '.[] | "\(.number)|\(.title)|\([.labels[].name] | join(","))"' | while IFS='|' read -r number title labels; do
  echo "📝 Issue #$number: $title"
  echo "   Labels: $labels"
  
  # Map issue to milestone
  milestone_title=$(map_issue_to_milestone "$number" "$title" "$labels")
  echo "   → Milestone: $milestone_title"
  
  # Get milestone ID and assign
  milestone_id=$(get_milestone_id "$milestone_title")
  assign_to_milestone "$number" "$milestone_id" "$milestone_title"
  
  echo "---"
done

echo "✅ Finished assigning issues to milestones!"
echo
echo "📊 Summary of milestone assignments:"
gh api "repos/${GH_OWNER}/${GH_REPO}/milestones" --jq '.[] | "\(.title): \(.open_issues) open issues"' 2>/dev/null || echo "No milestones found"
