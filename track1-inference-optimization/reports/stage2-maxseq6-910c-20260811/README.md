# Stage 2 `max_num_seqs=6` on one Ascend 910C

Only Code2Wav Stage 2 changed from `max_num_seqs=4` to 6. Stage 0 and Stage 1
remained at 4. Model, dataset, runner, sampling and all other deploy values were
held constant at challenge revision `009b80d686fe`.

## Official matrix result

Lower is better for latency and RTF; higher is better for throughput.
Concurrency-1 baseline is the mean of two preserved runs; c4 and c8 baseline
use one preserved official run.

| Cell | Metric | Baseline | Stage2=6 | Delta |
|---|---|---:|---:|---:|
| c1 / 32 | request throughput (req/s) | 0.4567 | 0.4754 | +4.1% |
| | mean TTFT (ms) | 327.0 | 323.8 | -1.0% |
| | mean E2E (ms) | 2190.1 | 2103.4 | -4.0% |
| | mean audio TTFP (ms) | 1069.9 | 1062.3 | -0.7% |
| | mean audio RTF | 0.5128 | 0.4963 | -3.2% |
| c4 / 64 | request throughput (req/s) | 0.6789 | 0.7226 | +6.4% |
| | mean TTFT (ms) | 476.5 | 477.9 | +0.3% |
| | mean E2E (ms) | 5825.3 | 5475.1 | -6.0% |
| | mean audio TTFP (ms) | 2253.8 | 2242.0 | -0.5% |
| | mean audio RTF | 1.3019 | 1.2239 | -6.0% |
| c8 / 128 | request throughput (req/s) | 0.6914 | 0.7899 | +14.3% |
| | mean TTFT (ms) | 494.6 | 523.2 | +5.8% |
| | mean E2E (ms) | 11410.6 | 9970.3 | -12.6% |
| | mean audio TTFP (ms) | 4198.1 | 3399.0 | -19.0% |
| | mean audio RTF | 2.5142 | 2.1809 | -13.3% |

All three cells completed: 32/32, 64/64 and 128/128, with zero failures and
100% streaming continuity. The service stayed healthy with no OOM. The
benchmark subprocess aborted with allocator status 134 only after each result
had been printed and saved; every `STATUS` records `validation_exit_code=0`.

## Decision

Keep this change as a performance candidate. The c8 TTFT cost remains below
the official 547.3 ms reference, while the four audio/throughput metrics all
improve materially. Accuracy is not established by this performance matrix;
the final stack still requires the official Video-MME, Daily-Omni and TTS-Seed
ASV/WER gates.

Raw artifacts are available under `c1-32-r1/`, `c4-64-r1/`, `c8-128-r1/` and
the preliminary `probe-c6-12/` guard run.
