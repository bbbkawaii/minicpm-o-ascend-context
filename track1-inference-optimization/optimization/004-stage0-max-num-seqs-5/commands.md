# Reproduction commands

Tested on one physical Ascend 910C, starting from challenge revision
`009b80d686fe` plus the promoted Stage 2 `max_num_seqs=6` change.

## Start the promoted service

```bash
source /usr/local/Ascend/ascend-toolkit/set_env.sh
export PYTHONPATH=/workspace/user_data/vllm-omni-minicpm-challenge:${PYTHONPATH:-}
export VLLM_CACHE_ROOT=/workspace/user_data/cache/vllm
export VLLM_WORKER_MULTIPROC_METHOD=spawn
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

cd /workspace/user_data/vllm-omni-minicpm-challenge
vllm serve /workspace/shared_assets/models/OpenBMB/MiniCPM-o-4_5 \
  --omni \
  --deploy-config vllm_omni/deploy/minicpmo_4_5.yaml \
  --trust-remote-code \
  --served-model-name openbmb/MiniCPM-o-4_5 \
  --stage-init-timeout 600 \
  --host 0.0.0.0 \
  --port 8091
```

The deploy YAML contains the exact candidate values:

```yaml
stages:
  - stage_id: 0
    max_num_seqs: 5
platforms:
  npu:
    stages:
      - stage_id: 0
        compilation_config:
          cudagraph_mode: PIECEWISE
          cudagraph_capture_sizes: [1, 2, 4, 5]
          max_cudagraph_capture_size: 5
```

## Run the official Seed-TTS matrix

Run cells sequentially against one healthy service.

```bash
export ASCEND_ENV=/usr/local/Ascend/ascend-toolkit/set_env.sh
export VLLM_OMNI_SOURCE=/workspace/user_data/vllm-omni-minicpm-challenge
export MODEL=openbmb/MiniCPM-o-4_5
export TOKENIZER=/workspace/shared_assets/models/OpenBMB/MiniCPM-o-4_5
export DATASET_PATH=/workspace/user_data/datasets/seed-tts-eval/seedtts_testset

NUM_PROMPTS=32 NUM_WARMUPS=3 MAX_CONCURRENCY=1 \
RESULT_DIR=/workspace/user_data/experiments/stage0-maxseq5/c1-32-r1 \
bash baseline/run_official_seed_tts.sh

NUM_PROMPTS=64 NUM_WARMUPS=3 MAX_CONCURRENCY=4 \
RESULT_DIR=/workspace/user_data/experiments/stage0-maxseq5/c4-64-r1 \
bash baseline/run_official_seed_tts.sh

NUM_PROMPTS=128 NUM_WARMUPS=3 MAX_CONCURRENCY=8 \
RESULT_DIR=/workspace/user_data/experiments/stage0-maxseq5/c8-128-r1 \
bash baseline/run_official_seed_tts.sh
```

For the reported A/B comparison, restart the same host with Stage 0 restored to
4 and run c1/c4; the c8 control was captured immediately before the candidate.
Each result directory retains the exact expanded benchmark command and JSON.
