# Reproduction commands

Use the service and Seed-TTS c1/c8 commands from experiment 009, changing only
the candidate value recorded in `changes.md`. Keep:

- one physical Ascend 910C;
- `VLLM_WORKER_MULTIPROC_METHOD=spawn`;
- Hugging Face and Transformers offline mode;
- three warmups, no oversampling, 32 prompts at c1 or 128 prompts at c8;
- source commit `0dced5d4` as the control.

Remote evidence roots used for this sweep:

- `/workspace/user_data/experiments/stage2-maxseq8-steps5-910c-20260811/`
- `/workspace/user_data/experiments/stage2-maxseq7-steps5-910c-20260811/`
- `/workspace/user_data/experiments/stage0-maxseq6-steps5-910c-20260811/`
- `/workspace/user_data/experiments/stage2-steps4-910c-20260811/`
- `/workspace/user_data/experiments/token2wav-fp16-steps5-910c-20260811/`
- `/workspace/user_data/experiments/codec-left-context2-steps5-910c-20260811/`
- `/workspace/user_data/experiments/codec-chunk32-steps5-910c-20260811/`

The durable raw result JSON is archived under
`reports/rejected-sweep-910c-20260811/raw/`.
