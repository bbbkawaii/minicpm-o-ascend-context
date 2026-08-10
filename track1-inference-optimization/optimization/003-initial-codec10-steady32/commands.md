# Reproduction commands

Apply challenge revision `009b80d686fe`, the promoted Stage2=6 patch, the
generic first-chunk implementation, and `activation.patch`. Start the service
with the resulting deploy YAML, then run the c8 official cell:

```bash
NUM_PROMPTS=128 NUM_WARMUPS=3 MAX_CONCURRENCY=8 \
RESULT_DIR=/workspace/user_data/experiments/initial10-steady32/c8-128-r1 \
bash baseline/run_official_seed_tts.sh
```

The c8 rejection gate fired, so c1 and c4 were intentionally not run.
