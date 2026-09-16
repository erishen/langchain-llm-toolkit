#!/usr/bin/env bash
# Start the personal-profile RAG API (langchain-llm-toolkit) for a local agent.
# Loopback only; INTERNAL_API_KEY authenticates local callers and must be
# supplied by the caller — no default is baked in here.
# Usage: INTERNAL_API_KEY=... ./scripts/start_profile_api.sh  (from apps/langchain-llm-toolkit)

set -euo pipefail
cd "$(dirname "$0")/.."

if [ -z "${INTERNAL_API_KEY:-}" ]; then
  echo "INTERNAL_API_KEY is not set; refusing to start with an implicit default." >&2
  exit 1
fi

if curl -s -m 2 http://127.0.0.1:8001/health >/dev/null 2>&1; then
  echo "profile RAG API already running on 8001"
  exit 0
fi

nohup uv run --package langchain-llm-toolkit \
  uvicorn langchain_llm_toolkit.api:app --host 127.0.0.1 --port 8001 \
  > /tmp/toolkit-api.log 2>&1 &

for i in $(seq 1 25); do
  sleep 2
  if curl -s -m 2 http://127.0.0.1:8001/health | grep -q healthy; then
    echo "profile RAG API up on http://127.0.0.1:8001"
    exit 0
  fi
done
echo "failed to start; see /tmp/toolkit-api.log" >&2
exit 1
