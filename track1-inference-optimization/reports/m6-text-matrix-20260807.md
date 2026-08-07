# M6 Concurrency Matrix — Text (Ascend 910C)

> Date: 2026-08-07
> Matrix: text concurrency 1/2/4/8, 100 requests + 10 warm-up, 3 steady rounds + 1 cold-start round
> Raw data: `reports/m6-matrix-20260807/`
> Deploy: `minicpmo_4_5_2gpu.yaml` (thinker GPU0, talker+Token2Wav GPU1)

## Throughput vs Concurrency

| Concurrency | Request throughput (req/s) | TTFT p50 (ms) | TTFT p95 (ms) | E2E p50 (ms) | Success |
|---|---:|---:|---:|---:|---:|
| 1 | 1.34 | 65.7 | 68.0 | 743 | 1.0 |
| 2 | 2.51 | 98.2 | 101.9 | 796 | 1.0 |
| 4 | 4.80 | 95.8 | 106.3 | 831 | 1.0 |
| 8 | 4.90 | 872 | 907 | 1627 | 1.0 |

## Key findings

1. **Throughput saturates at ~4.9 req/s.** concurrency 1→2→4 scales linearly
   (1.34 → 2.51 → 4.80), but concurrency 8 adds only +0.1 req/s (4.80 → 4.90).
   The two-card pipeline reaches capacity around concurrency 4.

2. **Latency collapses at concurrency 8.** TTFT p50 jumps from ~96 ms (conc 4)
   to **872 ms** (conc 8) — a 9× regression — while E2E doubles (831 → 1627 ms).
   The thinker (device 0) is the bottleneck: at conc 8 its AICore is pinned at
   ~72% while the talker (device 1) stays at 0% (idle for text-only requests).

3. **Optimal operating point ≈ concurrency 4.** It delivers ~98% of peak
   throughput (4.80 of 4.90 req/s) with TTFT p50 under 100 ms. Beyond that,
   latency degrades without throughput gain.

## Per-device resources (steady-state round 1)

| Concurrency | device 0 AICore peak | device 0 HBM | device 1 AICore | device 1 HBM |
|---|---:|---:|---:|---:|
| 4 | 73% | 51.3 GB | 0% | 45.3 GB |
| 8 | 72% | 51.3 GB | 0% | 45.3 GB |

Device 1 (talker) is idle during text-only benchmarks — the asymmetry is
expected since text requests never reach the speech stages.

## Interpretation for E-series experiments

- This matrix is the **baseline curve** for E1 (`max_num_seqs`): if raising
  `max_num_seqs` lifts the conc-8 throughput above 4.90 without degrading
  conc-4 TTFT, that is a real win.
- The conc-8 TTFT cliff (96→872 ms) is the target for E2 (`max_num_batched_tokens`)
  and scheduler tuning.
- E3 (memory budgets) should be validated at conc 4 (the knee), not conc 8.

## Caveats

- Audio matrix (conc 1/2/4) was NOT completed: single-request audio takes
  ~10 s each, so the full audio matrix would run ~1 hour. Text matrix is
  complete; audio at conc 1 is already covered by the formal baseline.
- Steady-state rounds (1-3) showed consistent numbers (per-round throughput
  variance < 1%), so the cold-start round 0 was correctly excluded.
