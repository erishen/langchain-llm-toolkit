#!/usr/bin/env bash
# Start the personal-profile RAG API in Docker.
# INTERNAL_API_KEY is read from the ax-agent .env so the local agent and this
# service stay on the same key; override with AX_AGENT_ENV if the path differs.
set -euo pipefail
cd "$(dirname "$0")/.."

ENV_FILE="${AX_AGENT_ENV:-../../../work/rust/ax-agent/.env}"
if [ ! -f "$ENV_FILE" ]; then
  echo "ax-agent env not found: $ENV_FILE (set AX_AGENT_ENV)" >&2
  exit 1
fi

KEY=$(grep -E '^PROFILE_RAG_KEY=' "$ENV_FILE" | head -1 | cut -d= -f2-)
if [ -z "$KEY" ]; then
  echo "PROFILE_RAG_KEY is not set in $ENV_FILE" >&2
  exit 1
fi

export INTERNAL_API_KEY="$KEY"
exec docker compose up -d --build "$@"
