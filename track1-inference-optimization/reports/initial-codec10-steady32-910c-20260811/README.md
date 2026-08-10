# Initial codec chunk 10, steady chunk 32

The larger steady chunk was tested as a correction to the rejected 10/25
schedule. Comparison baseline is Stage2 `max_num_seqs=6` with the original
25-frame codec schedule.

| c8 / 128 metric | Stage2=6 | 10/32 | Delta |
|---|---:|---:|---:|
| request throughput (req/s) | 0.7899 | 0.7837 | -0.8% |
| mean TTFT (ms) | 523.2 | 522.1 | -0.2% |
| mean E2E (ms) | 9970.3 | 10051.1 | +0.8% |
| mean audio TTFP (ms) | 3399.0 | 3683.6 | +8.4% |
| mean audio RTF | 2.1809 | 2.2550 | +3.4% |

All 128 requests completed, failed requests were zero, and streaming
continuity was 100%. The candidate is rejected because first-packet latency and
RTF regress. Raw JSON, command, status and stdout are preserved in
`c8-128-r1/`.
