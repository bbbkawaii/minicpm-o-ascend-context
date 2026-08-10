# Stage 0 `max_num_seqs=5` on one Ascend 910C

This stacks on the promoted Stage 2 `max_num_seqs=6` configuration.  Only the
Thinker Stage 0 admission cap changes from 4 to 5, together with the required
Ascend PIECEWISE capture list `[1, 2, 4, 5]` and maximum capture size 5.
The deployed source config is commit `e72f329c`.

Candidate and control use the official Seed-TTS runner on the same physical
910C.  Lower is better except request throughput.  The delta column is a
benefit ratio, so positive is better for the candidate.

The runner's `input_lens` and `output_lens` arrays match exactly within every
control/candidate cell, so the comparisons use the same prompt and text-output
workload rather than a different sampled subset.

| Cell | Metric | Stage0=4 control | Stage0=5 | Delta |
|---|---|---:|---:|---:|
| c1 / 32 | request throughput (req/s) | 0.4874 | 0.4772 | -2.09% |
| | mean TTFT (ms) | 325.45 | 324.68 | +0.24% |
| | mean E2E (ms) | 2051.19 | 2095.05 | -2.09% |
| | mean audio TTFP (ms) | 1063.57 | 1060.44 | +0.29% |
| | mean audio RTF | 0.4827 | 0.4941 | -2.32% |
| c4 / 64 | request throughput (req/s) | 0.6702 | 0.7454 | +11.22% |
| | mean TTFT (ms) | 459.50 | 482.07 | -4.68% |
| | mean E2E (ms) | 5914.96 | 5298.57 | +11.63% |
| | mean audio TTFP (ms) | 2294.01 | 2045.25 | +12.16% |
| | mean audio RTF | 1.3262 | 1.1980 | +10.70% |
| c8 / 128 | request throughput (req/s) | 0.7793 | 0.7926 | +1.71% |
| | mean TTFT (ms) | 525.35 | 512.01 | +2.60% |
| | mean E2E (ms) | 10106.24 | 9935.03 | +1.72% |
| | mean audio TTFP (ms) | 3664.72 | 3591.33 | +2.04% |
| | mean audio RTF | 2.2266 | 2.1869 | +1.82% |

The candidate completed **224/224** measured requests with zero failures.
All result files have `validation_exit_code=0`; the observed process exit 134
occurs in the known allocator teardown after a complete JSON result is saved.
Candidate output includes 1,022.96 seconds of audio across all three cells.

No official composite weighting has been published.  For a neutral decision
check, use a geometric mean of improvement ratios with equal weight for c1/c4/c8:

- Core TTFT + audio TTFP + audio RTF: **+2.409%**.
- All five displayed metrics: **+2.856%**.

Raw candidate artifacts are in `candidate/full-c8-128/`; paired c1/c4 controls
are in `paired-stage0-4/`, and the immediately preceding c8 control is in
`paired-stage0-4-c8/`.  This does not replace the required Video-MME,
Daily-Omni and TTS-Seed ASV/WER accuracy gates.
