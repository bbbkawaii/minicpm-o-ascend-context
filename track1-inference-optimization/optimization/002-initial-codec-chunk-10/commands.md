# Reproduction commands

Apply the promoted Stage2=6 patch, the generic first-chunk implementation and
this experiment's activation patch to challenge revision `009b80d686fe`.

```bash
git apply optimization/001-stage2-max-num-seqs-6/changes.patch
git apply optimization/patches/minicpmo-initial-codec-chunk.patch
git apply optimization/002-initial-codec-chunk-10/activation.patch
```

Targeted CPU test (the current Ascend image requires bypassing the repository
pytest config because its declared `pytest-asyncio` dependency is absent):

```bash
PYTHONPATH=$PWD pytest -q -c /dev/null \
  tests/model_executor/stage_input_processors/test_minicpmo_4_5_async_chunk.py
```

The assertions print `20 passed`; this image then aborts during allocator
teardown. Start the service with the patched deploy YAML and run the official
runner sequentially:

```bash
NUM_PROMPTS=32 NUM_WARMUPS=3 MAX_CONCURRENCY=1 \
RESULT_DIR=/workspace/user_data/experiments/initial-codec10/c1-32-r1 \
bash baseline/run_official_seed_tts.sh

NUM_PROMPTS=128 NUM_WARMUPS=3 MAX_CONCURRENCY=8 \
RESULT_DIR=/workspace/user_data/experiments/initial-codec10/c8-128-r1 \
bash baseline/run_official_seed_tts.sh
```
