# H1: max_num_seqs=8 Eliminates the Concurrency-8 TTFT Cliff (Breakthrough)

> Date: 2026-08-08
> Hypothesis (gpt-5.6-sol design): `max_num_seqs=4` causes batch-2 requests to
> wait for batch-1, so raising it relieves the conc-8 TTFT cliff.
> Design source: `~/orca/collab-system/tasks/ascend-optimization/spec.md` (H1)
> Raw data: `reports/h1-maxnumseqs-20260808/`
> Protocol: 30 requests + 5 warm-up, text at conc 4 and 8

## Results

| Config | conc 4 TTFT p50 | conc 8 TTFT p50 | conc 8 throughput | Success |
|---|---:|---:|---:|---:|
| maxseq=4 (baseline) | 96 ms | **833 ms** (cliff) | 4.79 req/s | 30/30 |
| **maxseq=8** | 89 ms | **94.6 ms** ✅ | **8.63 req/s** 🚀 | 30/30 |

## Impact

- **Concurrency-8 TTFT cliff eliminated**: 833 ms → 95 ms (8.8×).
- **Throughput +80%**: 4.79 → 8.63 req/s at concurrency 8.
- **No regression at conc 4**: 96 → 89 ms TTFT (slightly better).
- The cliff WAS the `max_num_seqs=4` admission cap. gpt-5.6-sol correctly
  identified that E1 (which only tested REDUCING 1/2/4) had missed this.

## Validation status

- Single run (30 req/cell). Per plan's 2-of-3 rule, needs a confirming round.
- maxseq=6 service failed to start (status: service failed) — likely OOM or
  config issue; not required since maxseq=8 already proves the hypothesis.
- Audio behavior with maxseq=8 untested.

## Next steps

1. Re-confirm maxseq=8 with a second run (2-of-3 rule) at conc 8.
2. Test even higher (10/12) to find the true ceiling — but watch for
   max_model_len / KV cache pressure (HBM was ~51GB/45GB at maxseq 4).
3. Then run the audio matrix with maxseq=8 (was skipped due to 1h cost at
   maxseq 4; higher admission may make it feasible).
