#!/usr/bin/env bash
# Run the competition's official vLLM-Omni Seed-TTS serving benchmark.

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
benchmark_bin="${VLLM_OMNI_BIN:-vllm-omni}"
host="${HOST:-127.0.0.1}"
port="${PORT:-8091}"
model="${MODEL:-openbmb/MiniCPM-o-4_5}"
tokenizer="${TOKENIZER:-$model}"
dataset_path="${DATASET_PATH:?set DATASET_PATH to the seedtts_testset directory}"
num_prompts="${NUM_PROMPTS:-32}"
num_warmups="${NUM_WARMUPS:-3}"
max_concurrency="${MAX_CONCURRENCY:-1}"
locale="${SEED_TTS_LOCALE:-en}"
run_id="${RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)-seed-tts-c${max_concurrency}}"
result_dir="${RESULT_DIR:-$repo_root/reports/runs/$run_id}"
result_filename="${RESULT_FILENAME:-benchmark.json}"
result_path="$result_dir/$result_filename"
stdout_path="$result_dir/stdout.txt"
status_path="$result_dir/STATUS"
command_path="$result_dir/command.txt"

if [[ -n "${ASCEND_ENV:-}" ]]; then
  # shellcheck disable=SC1090
  source "$ASCEND_ENV"
fi
if [[ -n "${VLLM_OMNI_SOURCE:-}" ]]; then
  export PYTHONPATH="$VLLM_OMNI_SOURCE:${PYTHONPATH:-}"
fi
if ! command -v "$benchmark_bin" >/dev/null 2>&1; then
  printf 'error: %s is not installed or not on PATH\n' "$benchmark_bin" >&2
  exit 127
fi
if [[ ! -f "$dataset_path/$locale/meta.lst" ]]; then
  printf 'error: Seed-TTS metadata not found: %s/%s/meta.lst\n' \
    "$dataset_path" "$locale" >&2
  exit 2
fi

mkdir -p "$result_dir"
if [[ -e "$result_path" ]]; then
  printf 'error: refusing to overwrite existing result: %s\n' "$result_path" >&2
  exit 2
fi

extra_body='{"modalities":["text","audio"],"chat_template_kwargs":{"enable_thinking":false,"use_tts_template":true}}'
benchmark_command=(
  "$benchmark_bin" bench serve
  --omni
  --host "$host"
  --port "$port"
  --backend openai-chat-omni
  --endpoint /v1/chat/completions
  --model "$model"
  --served-model-name "$model"
  --tokenizer "$tokenizer"
  --trust-remote-code
  --dataset-name seed-tts
  --dataset-path "$dataset_path"
  --seed-tts-root "$dataset_path"
  --seed-tts-locale "$locale"
  --num-prompts "$num_prompts"
  --num-warmups "$num_warmups"
  --max-concurrency "$max_concurrency"
  --no-oversample
  --disable-tqdm
  --print-stage
  --percentile-metrics ttft,e2el,audio_ttfp,audio_rtf,audio_duration
  --metric-percentiles 50,90,99
  --extra-body "$extra_body"
  --save-result
  --save-detailed
  --result-dir "$result_dir"
  --result-filename "$result_filename"
)

if [[ "${SEED_TTS_WER_EVAL:-0}" == "1" ]]; then
  benchmark_command+=(--seed-tts-wer-eval --seed-tts-wer-save-items)
fi

printf '%q ' "${benchmark_command[@]}" >"$command_path"
printf '\n' >>"$command_path"

set +e
"${benchmark_command[@]}" 2>&1 | tee "$stdout_path"
benchmark_rc=${PIPESTATUS[0]}
set -e

set +e
python3 - "$result_path" "$num_prompts" <<'PY'
import json
import sys
from pathlib import Path

result_path = Path(sys.argv[1])
expected = int(sys.argv[2])
try:
    result = json.loads(result_path.read_text())
except Exception as exc:
    print(f"result validation failed: {exc}", file=sys.stderr)
    raise SystemExit(1)

completed = int(result.get("completed", -1))
failed = int(result.get("failed", -1))
if completed != expected or failed != 0:
    print(
        f"result validation failed: completed={completed}, failed={failed}, expected={expected}",
        file=sys.stderr,
    )
    raise SystemExit(1)
print(f"official Seed-TTS result accepted: completed={completed}, failed={failed}")
PY
validation_rc=$?
set -e

printf 'benchmark_process_exit_code=%s\nvalidation_exit_code=%s\n' \
  "$benchmark_rc" "$validation_rc" >"$status_path"

# Some current Ascend images abort in allocator teardown after the runner has
# already printed and saved a complete result. Trust the saved official result,
# not that post-save process status, only after the checks above pass.
if [[ "$validation_rc" -eq 0 ]]; then
  exit 0
fi
if [[ "$benchmark_rc" -ne 0 ]]; then
  exit "$benchmark_rc"
fi
exit "$validation_rc"
