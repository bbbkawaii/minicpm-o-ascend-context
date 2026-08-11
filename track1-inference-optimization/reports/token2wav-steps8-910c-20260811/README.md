# Token2Wav eight-step Ascend 910C evidence

Hardware: one physical Ascend 910C card. Candidate source commit: `1c4e4c58`.

## Paired results

| Cell | Metric | 9 steps | 8 steps | Change |
|---|---:|---:|---:|---:|
| c1/32 fresh restart | Throughput (req/s) | 0.4453 | 0.4749 | +6.65% |
| c1/32 fresh restart | TTFT (ms) | 324.4 | 316.7 | -2.39% |
| c1/32 fresh restart | E2E (ms) | 2245 | 2105 | -6.23% |
| c1/32 fresh restart | Audio TTFP (ms) | 1048.8 | 991.7 | -5.44% |
| c1/32 fresh restart | Audio RTF | 0.5233 | 0.4909 | -6.18% |
| c8/128 same host | Throughput (req/s) | 0.8290 | 0.9264 | +11.75% |
| c8/128 same host | TTFT (ms) | 588.8 | 532.0 | -9.65% |
| c8/128 same host | E2E (ms) | 9537 | 8524 | -10.62% |
| c8/128 same host | Audio TTFP (ms) | 3770.7 | 3302.7 | -12.41% |
| c8/128 same host | Audio RTF | 2.1222 | 1.8933 | -10.79% |

Both sides completed all requests with zero failures. Paired input and output
token-length arrays are identical. The supplemental eight-step c4/64 run also
completed 64/64 requests with no failures.

## Quality gate

The source Seed-TTS English evaluator completed all 1,088 locally available
items. Mean WER is `0.033804`, below the source threshold `0.05`; request, PCM,
and ASR failure counts are all zero.

The exact benchmark JSON files are in `raw/`. No unpublished weighted score is
derived from these metrics.
