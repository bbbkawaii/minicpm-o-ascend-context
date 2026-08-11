# Code2Wav `token2wav_n_timesteps=9` on one Ascend 910C

This candidate stacks the already promoted Stage 2 `max_num_seqs=6` and Stage
0 `max_num_seqs=5` settings.  It changes only the MiniCPM-o 4.5 Code2Wav
solver setting in source commit `fa13e254`:

```yaml
connectors:
  connector_of_shared_memory:
    extra:
      token2wav_n_timesteps: 9  # default: 10
```

## Fresh paired c8 result

The c8/128 control ran on the same physical 910C immediately before the
candidate.  Both sides completed 128/128 requests with zero failures.  Higher
is better only for request throughput; lower is better for the other metrics.

| Metric | 10 steps control | 9 steps candidate | Candidate vs. control |
|---|---:|---:|---:|
| Request throughput (req/s) | 0.780716 | 0.845713 | +8.33% |
| Mean TTFT (ms) | 516.807 | 521.572 | +0.92% slower |
| Mean E2E (ms) | 10086.269 | 9311.704 | -7.68% |
| Mean audio TTFP (ms) | 3460.307 | 3236.602 | -6.46% |
| Mean audio RTF | 2.223885 | 2.031834 | -8.64% |

No unpublished aggregate or weighted competition score is inferred.  The raw
paired measurements are the decision evidence: four of the five published
performance metrics improve; TTFT has a small regression.

## Candidate serving matrix

| Cell | Completed / failed | Throughput (req/s) | Mean TTFT (ms) | Mean E2E (ms) | Audio TTFP (ms) | Audio RTF |
|---|---:|---:|---:|---:|---:|---:|
| c1 / 32 | 32 / 0 | 0.506188 | 333.268 | 1975.178 | 1036.037 | 0.463703 |
| c4 / 64 | 64 / 0 | 0.756452 | 476.955 | 5238.347 | 2096.883 | 1.179489 |
| c8 / 128 | 128 / 0 | 0.845713 | 521.572 | 9311.704 | 3236.602 | 2.031834 |

## Required TTS correctness gate

The source Seed-TTS English WER evaluator requested 2,000 prompts without
oversampling.  It found 1,088 unique items and completed every one.

| Check | Result |
|---|---:|
| Completed / failed | 1088 / 0 |
| Mean WER | 0.032571 |
| Required mean WER | <= 0.05 |
| Request / PCM / ASR failures | 0 / 0 / 0 |
| Gate | **PASS** |

The JSON result was completely saved before a known allocator teardown error
on process exit; the saved result contains all 1,088 completed records and the
WER fields above.  It is not a request or scoring failure.

Raw evidence is committed in [`raw/`](raw/): the three candidate matrix
results, the immediately preceding c8 control, and the full WER result.
Daily-Omni and Video-MME have not been rerun after this TTS-only change.
