# Token2Wav five-step Ascend 910C evidence

Hardware: one physical Ascend 910C card. Source commit: `0dced5d4`.

| Cell | Metric | 6 steps | 5 steps | Change |
|---|---:|---:|---:|---:|
| c1/32 | Throughput | 0.5415 | 0.5481 | +1.22% |
| c1/32 | TTFT (ms) | 326.6 | 320.3 | -1.94% |
| c1/32 | E2E (ms) | 1846 | 1824 | -1.19% |
| c1/32 | Audio TTFP (ms) | 914.3 | 879.2 | -3.83% |
| c1/32 | Audio RTF | 0.4304 | 0.4248 | -1.29% |
| c8/128 | Throughput | 1.1773 | 1.2831 | +8.99% |
| c8/128 | TTFT (ms) | 535.6 | 532.8 | -0.52% |
| c8/128 | E2E (ms) | 6697 | 6150 | -8.16% |
| c8/128 | Audio TTFP (ms) | 2862.3 | 2935.3 | +2.55% |
| c8/128 | Audio RTF | 1.4969 | 1.3752 | -8.13% |

All requests completed and paired input/output token-length arrays match.
The c8 audio TTFP regression is retained as an explicit tradeoff; the c8 audio
duration totals differ, so the runs are not claimed to have identical audio
duration. The full Seed-TTS gate is 1,088/1,088 with WER `0.035373 <= 0.05`
and zero request/PCM/ASR failures. Exact JSON is in `raw/`.
