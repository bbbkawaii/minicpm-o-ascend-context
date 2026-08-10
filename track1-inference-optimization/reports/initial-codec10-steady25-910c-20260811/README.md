# Initial codec chunk 10, steady chunk 25

Comparison baseline is the promoted Stage2 `max_num_seqs=6` candidate. The
generic bridge patch emits 10 codec frames on the first Code2Wav call and
returns to 25 frames for later calls.

| Cell | Metric | Stage2=6 | 10/25 | Delta |
|---|---|---:|---:|---:|
| c1 / 32 | request throughput (req/s) | 0.4754 | 0.4978 | +4.7% |
| | mean TTFT (ms) | 323.8 | 315.5 | -2.6% |
| | mean E2E (ms) | 2103.4 | 2008.5 | -4.5% |
| | mean audio TTFP (ms) | 1062.3 | 880.8 | -17.1% |
| | mean audio RTF | 0.4963 | 0.4730 | -4.7% |
| c8 / 128 | request throughput (req/s) | 0.7899 | 0.6345 | -19.7% |
| | mean TTFT (ms) | 523.2 | 499.5 | -4.5% |
| | mean E2E (ms) | 9970.3 | 12426.7 | +24.6% |
| | mean audio TTFP (ms) | 3399.0 | 3754.0 | +10.4% |
| | mean audio RTF | 2.1809 | 2.7353 | +25.4% |

Both cells completed with zero failures and 100% streaming continuity. The
activation is rejected because the c8 regressions outweigh the c1 first-packet
gain. Raw JSON, commands, status files and stdout are preserved under the two
cell directories.
