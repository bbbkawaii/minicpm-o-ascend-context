#!/usr/bin/env bash
set -euo pipefail

base_url="${BASE_URL:-http://127.0.0.1:8099/v1}"
timeout_seconds="${TIMEOUT_SECONDS:-300}"
deadline=$(( $(date +%s) + timeout_seconds ))

while (( $(date +%s) < deadline )); do
  if curl -fsS --max-time 5 "$base_url/models" >/dev/null; then
    printf '%s\n' "ready: $base_url"
    exit 0
  fi
  sleep 2
done

printf '%s\n' "timeout waiting for $base_url/models after ${timeout_seconds}s" >&2
exit 1
