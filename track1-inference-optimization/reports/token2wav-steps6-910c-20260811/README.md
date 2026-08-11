# Token2Wav six-step Ascend 910C evidence

Hardware: one physical Ascend 910C card. Source commit: `7a5a95a8`.

| Cell | Metric | 7 steps | 6 steps | Change |
|---|---:|---:|---:|---:|
| c1/32 | Throughput | 0.5037 | 0.5415 | +7.50% |
| c1/32 | TTFT (ms) | 319.3 | 326.6 | +2.29% |
| c1/32 | E2E (ms) | 1985 | 1846 | -6.99% |
| c1/32 | Audio TTFP (ms) | 966.2 | 914.3 | -5.38% |
| c1/32 | Audio RTF | 0.4632 | 0.4304 | -7.09% |
| c8/128 | Throughput | 1.0312 | 1.1773 | +14.17% |
| c8/128 | TTFT (ms) | 519.9 | 535.6 | +3.02% |
| c8/128 | E2E (ms) | 7629 | 6697 | -12.22% |
| c8/128 | Audio TTFP (ms) | 3114.3 | 2862.3 | -8.09% |
| c8/128 | Audio RTF | 1.6953 | 1.4969 | -11.70% |

All requests completed and paired token-length arrays match. The full Seed-TTS
gate is 1,088/1,088 with WER `0.034221 <= 0.05` and zero request/PCM/ASR
failures. Exact JSON is in `raw/`.
