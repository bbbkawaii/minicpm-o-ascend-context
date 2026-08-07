# E2: max_num_batched_tokens (thinker) Single-Variable Experiment

> Date: 2026-08-07
> Baseline config: `minicpmo_4_5_2gpu.yaml`, thinker NPU override `max_num_batched_tokens: 8192`
> Experiment: set thinker stage-0 NPU override to 4096 / 8192 / 12288
> Raw data: `reports/e2-batchedtokens-20260807/`
> Protocol: 30 requests + 5 warm-up per cell, text benchmark at conc 4 and conc 8

## Results

| batched_tokens | conc | Throughput (req/s) | TTFT p50 (s) | E2E p50 (s) | Success |
|:---:|---:|---:|---:|---:|---:|
| 4096 | 4 | 4.58 | 0.093 | 0.82 | 30/30 |
| 4096 | 8 | 4.67 | 0.853 | 1.60 | 30/30 |
| **8192 (baseline)** | 4 | 3.84 | 0.088 | 0.80 | 30/30 |
| **8192 (baseline)** | 8 | 4.68 | 0.870 | 1.61 | 30/30 |
| 12288 | 4 | 4.52 | 0.095 | 0.83 | 30/30 |
| 12288 | 8 | 4.75 | 0.849 | 1.57 | 30/30 |

## Conclusion: batched_tokens has no effect on the conc-8 TTFT cliff; keep baseline 8192

- At conc 8, all three values show the SAME TTFT cliff (~850-870 ms) and
  throughput (~4.7). Changing thinker batched_tokens 4096↔12288 moves nothing.
- At conc 4, all three are within noise (TTFT 88-95 ms, throughput 3.8-4.6).
- **The conc-8 cliff is NOT caused by thinker batching capacity.** It persists
  regardless of how many tokens the thinker batches in one step.

## Key insight for next steps

The conc-8 TTFT cliff must come from elsewhere — likely:
- scheduler / request-queueing behavior in the thinker stage (async scheduler),
- or the talker/connector backpressure,
- or vLLM-Ascend runtime-level serialization.

This points to **P-stage profiler work** (per-stage timeline) or E3 (memory
budgets / scheduler interplay) rather than more knob-twiddling on batched
tokens. E2 rules out one more configuration dimension.

## Caveats

- Only thinker stage-0 batched_tokens varied; talker (8192) and codec (65536)
  left at baseline.
- Text-only requests; audio behavior with batched_tokens may differ.
