# Reproduction commands

The source worktree is revision `009b80d686fe` with the already promoted
Stage 2/Stage 0 changes and source commit `fa13e254` for this experiment.

## Start the candidate service

```bash
source /usr/local/Ascend/ascend-toolkit/set_env.sh
export PYTHONPATH=/workspace/user_data/vllm-omni-minicpm-challenge:${PYTHONPATH:-}
export VLLM_OMNI_SOURCE=/workspace/user_data/vllm-omni-minicpm-challenge
export VLLM_WORKER_MULTIPROC_METHOD=spawn
export VLLM_CACHE_ROOT=/workspace/user_data/cache/vllm
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

cd /workspace/user_data/vllm-omni-minicpm-challenge
git show --stat fa13e254
rg -n 'token2wav_n_timesteps' vllm_omni/deploy/minicpmo_4_5.yaml
vllm serve /workspace/shared_assets/models/OpenBMB/MiniCPM-o-4_5 \
  --omni \
  --host 0.0.0.0 \
  --port 8091 \
  --trust-remote-code \
  --served-model-name openbmb/MiniCPM-o-4_5
```

The MiniCPM-o 4.5 deployment loader consumes
`vllm_omni/deploy/minicpmo_4_5.yaml`; this candidate adds the explicit
`token2wav_n_timesteps: 9` value there.

## Official Seed-TTS serving matrix

Run one healthy service and keep cells sequential on the same physical card.
The existing official runner records its expanded command in each result
directory.

```bash
export ASCEND_ENV=/usr/local/Ascend/ascend-toolkit/set_env.sh
export VLLM_OMNI_SOURCE=/workspace/user_data/vllm-omni-minicpm-challenge
export MODEL=openbmb/MiniCPM-o-4_5
export TOKENIZER=/workspace/shared_assets/models/OpenBMB/MiniCPM-o-4_5
export DATASET_PATH=/workspace/user_data/datasets/seed-tts-eval/seedtts_testset

NUM_PROMPTS=32 NUM_WARMUPS=3 MAX_CONCURRENCY=1 \
RESULT_DIR=/workspace/user_data/experiments/stage2-steps9-910c-20260811/candidate/c1-32 \
bash baseline/run_official_seed_tts.sh

NUM_PROMPTS=64 NUM_WARMUPS=3 MAX_CONCURRENCY=4 \
RESULT_DIR=/workspace/user_data/experiments/stage2-steps9-910c-20260811/candidate/c4-64 \
bash baseline/run_official_seed_tts.sh

NUM_PROMPTS=128 NUM_WARMUPS=3 MAX_CONCURRENCY=8 \
RESULT_DIR=/workspace/user_data/experiments/stage2-steps9-910c-20260811/candidate/c8-128 \
bash baseline/run_official_seed_tts.sh
```

For the reported A/B result, restore `token2wav_n_timesteps: 10`, restart the
same host, run c8/128, then restore `9` and run the candidate c8/128
immediately afterward.

## Source Seed-TTS English WER gate

The official source test requests 2,000 prompts at concurrency four with no
oversampling.  The local English dataset contains 1,088 unique items, so the
full run evaluates 1,088 synthesized utterances.  The benchmark invocation
uses the source's Seed-TTS dataset/payload/evaluator and an explicit local
tokenizer for offline operation.

```bash
export SEED_TTS_WER_EVAL=1
export SEED_TTS_EVAL_DEVICE=npu:1
export SEED_TTS_HF_WHISPER_MODEL=/workspace/user_data/models/whisper-large-v3-official
export VLLM_SEED_TTS_DATASET_PATH=/workspace/user_data/datasets/seed-tts-eval/seedtts_testset
export SEED_TTS_ROOT=/workspace/user_data/datasets/seed-tts-eval/seedtts_testset
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1

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
  --dataset-path "$VLLM_SEED_TTS_DATASET_PATH" \
  --seed-tts-root "$SEED_TTS_ROOT" \
  --seed-tts-locale en \
  --num-prompts 2000 \
  --num-warmups 0 \
  --max-concurrency 4 \
  --no-oversample \
  --disable-tqdm \
  --extra-body '{"modalities":["text","audio"],"chat_template_kwargs":{"enable_thinking":false,"use_tts_template":true}}' \
  --seed-tts-wer-eval \
  --save-result \
  --result-dir /workspace/user_data/experiments/stage2-steps9-910c-20260811/wer-full \
  --result-filename benchmark.json
```

Compare `seed_tts_content_error_mean` against the source test threshold
`0.05`; pass only when it is at or below that value and request/PCM/ASR failure
counts are zero.
