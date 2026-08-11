# Reproduction commands

The source worktree is revision `009b80d686fe` with source commit `e3266c5a`.

## Start the service

```bash
source /usr/local/Ascend/ascend-toolkit/set_env.sh
export PYTHONPATH=/workspace/user_data/vllm-omni-minicpm-challenge:${PYTHONPATH:-}
export VLLM_OMNI_SOURCE=/workspace/user_data/vllm-omni-minicpm-challenge
export VLLM_WORKER_MULTIPROC_METHOD=spawn
export VLLM_CACHE_ROOT=/workspace/user_data/cache/vllm
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

cd /workspace/user_data/vllm-omni-minicpm-challenge
vllm serve /workspace/shared_assets/models/OpenBMB/MiniCPM-o-4_5 \
  --omni --host 0.0.0.0 --port 8091 --trust-remote-code \
  --served-model-name openbmb/MiniCPM-o-4_5
```

The deployment YAML sets `token2wav_n_timesteps: 7`.

## Seed-TTS performance cells

```bash
export ASCEND_ENV=/usr/local/Ascend/ascend-toolkit/set_env.sh
export VLLM_OMNI_SOURCE=/workspace/user_data/vllm-omni-minicpm-challenge
export MODEL=openbmb/MiniCPM-o-4_5
export TOKENIZER=/workspace/shared_assets/models/OpenBMB/MiniCPM-o-4_5
export DATASET_PATH=/workspace/user_data/datasets/seed-tts-eval/seedtts_testset

NUM_PROMPTS=32 NUM_WARMUPS=3 MAX_CONCURRENCY=1 \
RESULT_DIR=/workspace/user_data/experiments/stage2-steps7-910c-20260811/candidate7/c1-32 \
bash baseline/run_official_seed_tts.sh

NUM_PROMPTS=64 NUM_WARMUPS=3 MAX_CONCURRENCY=4 \
RESULT_DIR=/workspace/user_data/experiments/stage2-steps7-910c-20260811/candidate7/c4-64 \
bash baseline/run_official_seed_tts.sh

NUM_PROMPTS=128 NUM_WARMUPS=3 MAX_CONCURRENCY=8 \
RESULT_DIR=/workspace/user_data/experiments/stage2-steps7-910c-20260811/candidate7/c8-128 \
bash baseline/run_official_seed_tts.sh
```

## Seed-TTS English WER gate

Use the same WER command recorded in experiment 006, with
`SEED_TTS_EVAL_DEVICE=npu:1`, `--num-prompts 2000`, `--max-concurrency 4`,
`--no-oversample`, and `--seed-tts-wer-eval`; write results to
`stage2-steps7-910c-20260811/candidate7/wer-full`.
