# Token2Wav seven-step Ascend 910C evidence

Hardware: one physical Ascend 910C card. Candidate source commit: `e3266c5a`.

| Cell | Metric | 8 steps | 7 steps | Change |
|---|---:|---:|---:|---:|
| c1/32 | Throughput (req/s) | 0.4749 | 0.5037 | +6.07% |
| c1/32 | TTFT (ms) | 316.7 | 319.3 | +0.83% |
| c1/32 | E2E (ms) | 2105 | 1985 | -5.72% |
| c1/32 | Audio TTFP (ms) | 991.7 | 966.2 | -2.57% |
| c1/32 | Audio RTF | 0.4909 | 0.4632 | -5.65% |
| c8/128 | Throughput (req/s) | 0.9264 | 1.0312 | +11.31% |
| c8/128 | TTFT (ms) | 532.0 | 519.9 | -2.26% |
| c8/128 | E2E (ms) | 8524 | 7629 | -10.50% |
| c8/128 | Audio TTFP (ms) | 3302.7 | 3114.3 | -5.71% |
| c8/128 | Audio RTF | 1.8933 | 1.6953 | -10.46% |

All paired runs completed every request with zero failures and identical
input/output token-length arrays. Seven-step c4/64 also completed 64/64.

The source Seed-TTS English gate evaluated 1,088/1,088 items: mean WER
`0.033366 <= 0.05`, with zero request, PCM, and ASR failures. Exact benchmark
JSON files are in `raw/`.
