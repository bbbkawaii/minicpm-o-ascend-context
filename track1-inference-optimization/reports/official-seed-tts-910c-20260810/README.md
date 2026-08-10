# Official Seed-TTS single-card baseline (2026-08-10)

## Scope

This is the first baseline in this repository collected with the competition's
official vLLM-Omni Seed-TTS runner on one physical Ascend 910C card. It is not
the earlier custom text/audio probe and it is not a two-card result.

The server used challenge commit `009b80d686fe` and the unmodified official
`vllm_omni/deploy/minicpmo_4_5.yaml`. All three competition performance cells
were measured with 3 warm-up requests, English Seed-TTS, and oversampling
disabled: concurrency 1/32 requests, 4/64 requests, and 8/128 requests.

## Result

| Concurrency | Requests | Throughput (ours / ref) | TTFT ms (ours / ref) | E2E ms (ours / ref) | TTFP ms (ours / ref) | RTF (ours / ref) |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 32/32 | 0.4661 / 0.5383 | **329.59** / 333.26 | 2145.20 / **1857.22** | 1069.69 / **986.47** | 0.5032 / **0.4423** |
| 4 | 64/64 | **0.6789** / 0.6042 | **476.46** / 533.87 | **5825.26** / 6600.51 | **2253.83** / 3411.08 | **1.3019** / 1.5734 |
| 8 | 128/128 | 0.6914 / **0.7547** | **494.64** / 547.34 | 11410.62 / **10450.68** | 4198.13 / **3352.75** | 2.5142 / **2.3024** |

All 224 measured requests succeeded and every cell reported 100% streaming
continuity. Concurrency 4 beats the reference on every performance metric.
Concurrency 1 already wins TTFT but trails on audio work; concurrency 8 wins
TTFT but queues audio work behind the stage admission cap.

The official JSON and full CLI/stage output are stored in `c1-32/`, `c4-64/`,
and `c8-128/`. A second unchanged concurrency-1 run is in `c1-32-r2/`.

### Concurrency-1 repeatability

| Metric | Round 1 | Round 2 | Two-run mean | Range / mean |
|---|---:|---:|---:|---:|
| Throughput (req/s) | 0.4661 | 0.4474 | 0.4567 | 4.10% |
| TTFT (ms) | 329.59 | 324.44 | 327.02 | 1.58% |
| E2E (ms) | 2145.20 | 2234.97 | 2190.09 | 4.10% |
| Audio TTFP (ms) | 1069.69 | 1070.06 | 1069.87 | 0.03% |
| Audio RTF | 0.5032 | 0.5224 | 0.5128 | 3.73% |

The 8.4% TTFP gap to the reference is much larger than the measured 0.03%
repeat range, so it is a stable optimization target rather than one noisy run.

## Stage evidence and first optimization target

| Stage | Mean generation time | Interpretation |
|---|---:|---|
| Stage 0 (`llm`) | 318.26 ms | Not the current bottleneck; global TTFT already beats the reference. |
| Stage 1 (`tts`) | 1313.45 ms | Streaming talker; contributes to first-packet latency. |
| Stage 2 (`code2wav`) | 2129.37 ms | Primary RTF/E2E hotspot. |

Two independent experiments now follow from the matrix:

1. For concurrency 8, test whether the teammate's two-card text-only
   `max_num_seqs=8` result can be migrated safely to the one-card official
   config. The single-card config explicitly warns about Code2Wav activation
   OOM above four active sequences, so this starts as a guarded startup and
   short audio probe, not a promoted optimization.
2. For concurrency 1, separate the first codec chunk size from the steady
   chunk size. A smaller first chunk can reduce TTFP while larger later chunks
   amortize Code2Wav launch overhead and protect RTF. The current MiniCPM
   bridge exposes only one `codec_chunk_frames=25` value.

Do not tune Stage 0 while its TTFT already beats the reference. Any chunking
change must rerun the Seed-TTS ASV/WER accuracy gate before it is accepted.

## Reproduction

The exact wrapper used on the 910C host is saved as
[`c1-32/run_seed_tts_bench.sh`](c1-32/run_seed_tts_bench.sh). The service was
already warm and listening on port 8091. Invoke the saved wrapper as:

```bash
bash run_seed_tts_bench.sh 32 3 seed-tts-official-c1-32
```

The wrapper records a process status of `134` because the client process hits
an allocator teardown abort after it prints and saves the result. This happens
after 32/32 successful requests and does not invalidate the saved benchmark;
the JSON's `completed=32` and `failed=0` are the acceptance signals.
