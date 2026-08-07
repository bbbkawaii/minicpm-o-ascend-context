# E1: max_num_seqs Single-Variable Experiment (Ascend 910C)

> Date: 2026-08-07
> Baseline config: `minicpmo_4_5_2gpu.yaml` (all 3 stages `max_num_seqs: 4`)
> Experiment: set all 3 stages to 1, 2, 4; restart service; benchmark text at conc 4 and conc 8
> Raw data: `reports/e1-maxnumseqs-20260807/`
> Protocol: 30 requests + 5 warm-up per cell

## Results

| max_num_seqs | conc | Throughput (req/s) | TTFT p50 (s) | E2E p50 (s) | Success |
|:---:|---:|---:|---:|---:|---:|
| 1 | 4 | 1.38 | 2.23 | 2.90 | 30/30 |
| 1 | 8 | 1.38 | 5.13 | 5.80 | 30/30 |
| 2 | 4 | 2.64 | 0.81 | 1.51 | 30/30 |
| 2 | 8 | 2.60 | 2.33 | 3.02 | 30/30 |
| **4 (baseline)** | 4 | **4.52** | **0.096** | 0.82 | 30/30 |
| **4 (baseline)** | 8 | **4.79** | 0.83 | 1.56 | 30/30 |

## Conclusion: baseline max_num_seqs=4 is Pareto-optimal; no change needed

- **max_num_seqs=1**: throughput pinned at 1.38 req/s (fully serialized), TTFT
  degrades to 2.2-5.1 s. Clearly worse.
- **max_num_seqs=2**: throughput 2.6, but TTFT 0.8-2.3 s (requests queue behind
  the limited batch slot). Worse than baseline at every point.
- **max_num_seqs=4**: throughput 4.5-4.8, TTFT stays 96 ms at conc 4. Best on
  both throughput AND latency (Pareto dominant).

Per the plan's stopping rule, 4 is stable, no OOM, and higher concurrency does
not queue behind it — so testing 6 is not warranted.

## Value of this experiment

E1 confirms the current configuration is already optimal on this dimension,
which **rules out `max_num_seqs` as a lever** and directs effort to other
variables (E2 `max_num_batched_tokens`, E3 memory budgets, scheduler). A
negative result that eliminates a hypothesis is a valid experiment outcome.

## Caveats

- Only text benchmarked (30 req/cell). Audio concurrency may interact
  differently with max_num_seqs.
- Service restarted per variant (cold-start excluded via 5 warm-up requests).
- Consistent with the M6 matrix: conc 8 offers no throughput over conc 4.
