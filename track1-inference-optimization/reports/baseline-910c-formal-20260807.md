# Baseline Report — MiniCPM-o 4.5 on Ascend 910C (Formal)

> Date: 2026-08-07
> Machine: HiDevLab DevEnv_404669
> Status: **FORMAL** — full repro evidence (raw JSON, commands, environment) archived in `reports/rerun-20260807/`

## Environment

| Item | Value |
|---|---|
| Hardware | Atlas 800T A3 (Ascend 910C × 2, 64 GiB HBM each) |
| NPU 0 / NPU 1 | device 0 (thinker), device 1 (talker+Token2Wav) |
| Driver / CANN | npu-smi 25.5.1 / CANN 9.0.0 |
| Python | 3.12.13 |
| torch / torch_npu | 2.10.0 |
| vLLM-Omni | 0.25.0+npu @ `0a12ac52` (minicpm-challenge) |
| Deploy config | `minicpmo_4_5_2gpu.yaml` |
| Serve port | 8091 |

Full env dump: `rerun-20260807/environment.txt`

## Text baseline (20 req, concurrency 2, 5 warm-up)

| Metric | p50 | p95 | p99 |
|---|---:|---:|---:|
| TTFT (ms) | **92.6** | 96.5 | 102.9 |
| ITL (ms) | **19.5** | — | — |
| E2E (ms) | **780** | — | — |
| Request throughput | 2.55 req/s | | |

> TPOT / output_tokens: `null` — the streaming endpoint does not return usage
> tokens. Per the review fix, we do NOT substitute character counts for tokens.

### Per-device resources (text)

| Device | AICore peak | HBM peak (MB) |
|---|---:|---:|
| 0 (thinker) | 50% | 51256 |
| 1 (talker) | 0% | 45292 |
| Host peak | 123.8 GB | |

## Audio/TTS baseline (8 req, concurrency 1, 2 warm-up)

| Metric | p50 |
|---|---:|
| TTFT (ms) | 557 |
| TTFP (ms) | **1295** |
| ICL (ms) | **239.5** (56 samples) |
| E2E (s) | 3.05 |
| RTF (E2E) | **0.406** |
| Playback-safe ratio | 1.0 |
| First audio chunk (s) | 0.84 |
| Max playback gap (ms) | 288 |
| Audio chunks | 8 per request |

### Per-device resources (audio)

| Device | AICore peak | HBM peak (MB) |
|---|---:|---:|
| 0 (thinker) | 69% | 51256 |
| 1 (talker) | 77% | 45292 |
| Host peak | 122.8 GB | |

## Repro evidence (archived in `reports/rerun-20260807/`)

- `text_benchmark.json` / `audio_benchmark.json` — raw v1-schema results
- `text-resources-summary.json` / `audio-resources-summary.json` — per-device resource aggregation
- `environment.txt` — date, npu-smi, python, torch/npu, vllm-omni commit, deploy config

## Reproduction commands

```bash
export PATH=/usr/local/python3.12.13/bin:$PATH
source /usr/local/Ascend/ascend-toolkit/set_env.sh

cd /vllm-workspace/vllm-omni
vllm serve /workspace/shared_assets/models/OpenBMB/MiniCPM-o-4_5 \
  --omni --served-model-name openbmb/MiniCPM-o-4_5 --trust-remote-code \
  --deploy-config vllm_omni/deploy/minicpmo_4_5_2gpu.yaml \
  --stage-init-timeout 600 --host 0.0.0.0 --port 8091

# Text (20 req, conc 2, 5 warm-up), collecting resources:
bash baseline/collect_resources.sh --interval 1 --outdir /tmp/res &
python3 baseline/benchmark_text.py --base-url http://127.0.0.1:8091/v1 \
  --model openbmb/MiniCPM-o-4_5 --requests 20 --concurrency 2 \
  --warmup-requests 5 --output text_benchmark.json

# Audio (8 req, conc 1, 2 warm-up):
python3 baseline/benchmark_audio.py --base-url http://127.0.0.1:8091/v1 \
  --model openbmb/MiniCPM-o-4_5 --requests 8 --concurrency 1 \
  --warmup-requests 2 --output audio_benchmark.json
```

## Gotchas (confirmed on this run)

1. **Branch**: must use `minicpm-challenge`. Default HEAD breaks with transformers 5.x.
2. **Registry subprocess crash**: pre-generate modelinfo caches under `$VLLM_CACHE_ROOT/modelinfos/`.
3. **Streaming returns no usage tokens** → TPOT/output_token_throughput are `null` (not char-substituted).
4. **Per-device collection**: device_id is the chip index (0/1), not the npu-smi group id (4).
