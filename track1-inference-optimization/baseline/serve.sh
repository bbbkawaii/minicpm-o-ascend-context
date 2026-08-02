#!/usr/bin/env bash
set -euo pipefail

model="${MODEL:-openbmb/MiniCPM-o-4_5}"
host="${HOST:-0.0.0.0}"
port="${PORT:-8099}"
deploy_config="${DEPLOY_CONFIG:-vllm_omni/deploy/minicpmo_4_5.yaml}"
server_bin="${VLLM_OMNI_BIN:-vllm-omni}"

if ! command -v "$server_bin" >/dev/null 2>&1; then
  if [[ "$server_bin" == "vllm-omni" ]] && command -v vllm >/dev/null 2>&1; then
    server_bin="vllm"
  else
    printf 'error: %s is not installed or not on PATH\n' "$server_bin" >&2
    exit 127
  fi
fi

printf 'model=%s\n' "$model"
printf 'deploy_config=%s\n' "$deploy_config"
printf 'listen=%s:%s\n' "$host" "$port"

exec "$server_bin" serve "$model" \
  --omni \
  --deploy-config "$deploy_config" \
  --trust-remote-code \
  --host "$host" \
  --port "$port" \
  "$@"
