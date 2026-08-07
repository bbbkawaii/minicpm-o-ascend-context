#!/usr/bin/env bash
# Run the fixed concurrency matrix for text and text+audio benchmarks.
#
# Matrix (from low-cost-model-optimization-plan.md, stage M6):
#   text       : concurrency 1, 2, 4, 8 ; 100 measured + 10 warm-up each
#   text+audio : concurrency 1, 2, 4    ;  30 measured +  3 warm-up each
#
# Behavior:
#   * Each cell writes to optimization/runs/<matrix>/<cell>/ with command,
#     benchmark JSON, resource CSV+summary, and a server log tail.
#   * A failing cell keeps its evidence but does not auto-promote concurrency.
#   * Runs 3 rounds; steady-state stats exclude a cold-start first round.
#   * DRY_RUN=1 prints every planned command without contacting the server.

set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8091/v1}"
MODEL="${MODEL:-openbmb/MiniCPM-o-4_5}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNS_DIR="${RUNS_DIR:-$ROOT_DIR/optimization/runs}"
SERVER_LOG="${SERVER_LOG:-/root/vllm_serve.log}"
ROUNDS="${ROUNDS:-3}"
DRY_RUN="${DRY_RUN:-0}"

# shellcheck disable=SC2016
log() { printf '[%s] %s\n' "$(date -u +%H:%M:%S)" "$*"; }

plan() { printf '%s\n' "$*" >> "$RUNS_DIR/.plan.txt"; }

check_server() {
  # shellcheck disable=SC2016
  local body
  body=$(curl -s -m 10 "$BASE_URL/models" 2>/dev/null || true)
  if ! printf '%s' "$body" | grep -q '"object"'; then
    log "ERROR: server not ready at $BASE_URL/models"
    return 1
  fi
  log "server OK: $BASE_URL/models"
}

run_matrix() {
  local label="$1" requests="$2" warmup="$3"; shift 3
  local concs=("$@")

  for conc in "${concs[@]}"; do
    for round in $(seq 1 "$ROUNDS"); do
      local cell="$RUNS_DIR/$label/conc$conc/round$round"
      mkdir -p "$cell"
      local cmd
      cmd="python3 $ROOT_DIR/baseline/benchmark_audio.py"
      [[ "$label" == "text" ]] && cmd="python3 $ROOT_DIR/baseline/benchmark_text.py"
      cmd="$cmd --base-url $BASE_URL --model $MODEL --requests $requests --concurrency $conc --warmup-requests $warmup --output $cell/benchmark.json"

      printf 'RUN label=%s conc=%s round=%s\n' "$label" "$conc" "$round"
      printf '  %s\n' "$cmd"
      plan "$cmd"

      # Record the resource + summary steps in the plan too, so DRY_RUN
      # prints the complete intended pipeline.
      plan "  collect_resources.sh --outdir $cell"
      plan "  summarize_resources.py $cell/resources.csv --output $cell/resources-summary.json"

      if [[ "$DRY_RUN" == "1" ]]; then
        continue
      fi

      check_server || { echo "server-check-failed" > "$cell/STATUS"; continue; }

      # Start resource collector.
      local pidfile="$cell/collect_resources.pid"
      if command -v npu-smi >/dev/null 2>&1; then
        "$ROOT_DIR/baseline/collect_resources.sh" --interval 1 --outdir "$cell" &
        local collector_pid=$!
      else
        log "WARN: npu-smi unavailable; no resource collection for $cell"
      fi

      # Run benchmark, capturing command + exit.
      set +e
      eval "$cmd" > "$cell/stdout.txt" 2> "$cell/stderr.txt"
      local rc=$?
      set -e
      printf 'rc=%d\n' "$rc" > "$cell/STATUS"
      log "  finished rc=$rc"

      # Stop collector.
      if [[ -n "${collector_pid:-}" ]]; then
        kill -TERM "$collector_pid" 2>/dev/null || true
        wait "$collector_pid" 2>/dev/null || true
      fi
      if [[ -f "$cell/resources.csv" ]]; then
        python3 "$ROOT_DIR/baseline/summarize_resources.py" \
          "$cell/resources.csv" --output "$cell/resources-summary.json" \
          > "$cell/resources-summary.stdout.txt" 2>&1 || true
      fi

      # Server log tail.
      if [[ -n "$SERVER_LOG" && -f "$SERVER_LOG" ]]; then
        tail -50 "$SERVER_LOG" > "$cell/server-log-tail.txt" || true
      fi

      # A failing cell stops this label's higher concurrency (keep evidence).
      if [[ $rc -ne 0 ]]; then
        log "  cell failed rc=$rc; skipping higher concurrency for $label"
        return
      fi
    done
  done
}

main() {
  mkdir -p "$RUNS_DIR"
  : > "$RUNS_DIR/.plan.txt"

  if [[ "$DRY_RUN" == "1" ]]; then
    log "DRY_RUN=1: printing plan only (no server contact)"
  else
    check_server
  fi

  # text: 1, 2, 4, 8 (100 req, 10 warm-up)
  run_matrix "text" 100 10 1 2 4 8
  # text+audio: 1, 2, 4 (30 req, 3 warm-up)
  run_matrix "audio" 30 3 1 2 4

  log "plan written to $RUNS_DIR/.plan.txt"
  log "done"
}

main "$@"
