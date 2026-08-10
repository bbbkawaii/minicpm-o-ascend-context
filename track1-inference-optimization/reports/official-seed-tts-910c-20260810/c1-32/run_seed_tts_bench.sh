#!/usr/bin/env bash

set -u

num_prompts="${1:?num_prompts is required}"
num_warmups="${2:?num_warmups is required}"
run_name="${3:?run_name is required}"

source /usr/local/Ascend/ascend-toolkit/set_env.sh
export PYTHONPATH="/workspace/user_data/vllm-omni-minicpm-challenge:${PYTHONPATH:-}"
export VLLM_CACHE_ROOT=/workspace/user_data/cache/vllm
export VLLM_WORKER_MULTIPROC_METHOD=spawn
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

output_dir=/workspace/user_data/baseline/minicpm-challenge-009b80d6
log_path="${output_dir}/${run_name}.log"
status_path="${output_dir}/${run_name}.status"
result_name="${run_name}.json"

vllm-omni bench serve \
  --omni \
  --host 127.0.0.1 \
  --port 8091 \
  --backend openai-chat-omni \
  --endpoint /v1/chat/completions \
  --model openbmb/MiniCPM-o-4_5 \
  --served-model-name openbmb/MiniCPM-o-4_5 \
  --tokenizer /workspace/shared_assets/models/OpenBMB/MiniCPM-o-4_5 \
  --trust-remote-code \
  --dataset-name seed-tts \
  --dataset-path /workspace/user_data/datasets/seed-tts-eval/seedtts_testset \
  --seed-tts-root /workspace/user_data/datasets/seed-tts-eval/seedtts_testset \
  --seed-tts-locale en \
  --num-prompts "${num_prompts}" \
  --num-warmups "${num_warmups}" \
  --max-concurrency 1 \
  --no-oversample \
  --disable-tqdm \
  --print-stage \
  --percentile-metrics ttft,e2el,audio_ttfp,audio_rtf,audio_duration \
  --metric-percentiles 50,90,99 \
  --extra-body '{"modalities":["text","audio"],"chat_template_kwargs":{"enable_thinking":false,"use_tts_template":true}}' \
  --save-result \
  --save-detailed \
  --result-dir "${output_dir}" \
  --result-filename "${result_name}" \
  >"${log_path}" 2>&1

exit_code=$?
printf '%s\n' "${exit_code}" >"${status_path}"
exit "${exit_code}"
