# Reproduction commands

Tested challenge revision: `009b80d686fe` on one physical Ascend 910C card.

## Start the candidate service

```bash
source /usr/local/Ascend/ascend-toolkit/set_env.sh
export PYTHONPATH=/workspace/user_data/vllm-omni-minicpm-challenge:${PYTHONPATH:-}
export VLLM_CACHE_ROOT=/workspace/user_data/cache/vllm
export VLLM_WORKER_MULTIPROC_METHOD=spawn
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

vllm serve /workspace/shared_assets/models/OpenBMB/MiniCPM-o-4_5 \
  --omni \
  --deploy-config vllm_omni/deploy/minicpmo_4_5.yaml \
  --stage-overrides '{"2":{"max_num_seqs":6}}' \
  --trust-remote-code \
  --served-model-name openbmb/MiniCPM-o-4_5 \
  --stage-init-timeout 600 \
  --host 0.0.0.0 \
  --port 8091
```

## Run the official matrix

Run the cells sequentially against the same healthy service. The runner saves
the exact expanded benchmark command in each result directory.

```bash
export ASCEND_ENV=/usr/local/Ascend/ascend-toolkit/set_env.sh
export VLLM_OMNI_SOURCE=/workspace/user_data/vllm-omni-minicpm-challenge
export MODEL=openbmb/MiniCPM-o-4_5
export TOKENIZER=/workspace/shared_assets/models/OpenBMB/MiniCPM-o-4_5
export DATASET_PATH=/workspace/user_data/datasets/seed-tts-eval/seedtts_testset

NUM_PROMPTS=32 NUM_WARMUPS=3 MAX_CONCURRENCY=1 \
RESULT_DIR=/workspace/user_data/experiments/stage2-maxseq6/c1-32-r1 \
bash baseline/run_official_seed_tts.sh

NUM_PROMPTS=64 NUM_WARMUPS=3 MAX_CONCURRENCY=4 \
RESULT_DIR=/workspace/user_data/experiments/stage2-maxseq6/c4-64-r1 \
bash baseline/run_official_seed_tts.sh

NUM_PROMPTS=128 NUM_WARMUPS=3 MAX_CONCURRENCY=8 \
RESULT_DIR=/workspace/user_data/experiments/stage2-maxseq6/c8-128-r1 \
bash baseline/run_official_seed_tts.sh
```
