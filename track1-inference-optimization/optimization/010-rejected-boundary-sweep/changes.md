# Candidate changes

All candidates start from source commit `0dced5d4`; none was retained.

| Candidate | Exact change |
|---|---|
| Stage2 8 | `stages[2].max_num_seqs: 6 -> 8` |
| Stage2 7 | `stages[2].max_num_seqs: 6 -> 7` |
| Stage0 6 | `stages[0].max_num_seqs: 5 -> 6`; Ascend capture sizes `[1,2,4,5] -> [1,2,4,6]`; max capture `5 -> 6` |
| Token2Wav 4 | `connectors.connector_of_shared_memory.extra.token2wav_n_timesteps: 5 -> 4` |
| Token2Wav FP16 | add `token2wav_float16: true`; temporarily align Flow inputs/noise to the Flow parameter dtype and cast Flow mel back to the HiFT parameter dtype in `batched_token2wav.py` |
| Left context 2 | `codec_left_context_frames: 3 -> 2` |
| Chunk 32 | `codec_chunk_frames: 25 -> 32` |

The FP16 alignment code was validated only as an experiment and was reverted
with the FP16 configuration after its performance gate failed.
