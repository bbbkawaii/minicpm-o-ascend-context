# 2026-08-11 one-card rejected-candidate sweep

All candidates were measured on one physical Ascend 910C against source
commit `0dced5d4`. The fixed control is Stage0/Stage1/Stage2
`max_num_seqs=5/4/6`, `codec_chunk_frames=25`,
`codec_left_context_frames=3`, and `token2wav_n_timesteps=5`.

The table uses an improvement-oriented sign: positive is better for every
column. Throughput is candidate/control; latency and RTF are control/candidate.

| Candidate | Cell | Throughput | TTFT | E2E | Audio TTFP | Audio RTF | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| Stage2 `max_num_seqs=8` | c8/128 | -3.50% | -4.14% | -3.55% | -12.63% | -3.37% | reject |
| Stage2 `max_num_seqs=7` | c8/128 | -9.58% | -7.14% | -9.66% | -36.30% | -10.38% | reject |
| Stage0 `max_num_seqs=6` | c8/128 | -12.16% | -6.47% | -13.01% | -40.44% | -13.57% | reject |
| Token2Wav 4 steps, run 1 | c1/32 | -2.03% | -2.05% | -2.07% | +3.85% | -1.82% | reject |
| Token2Wav 4 steps, run 2 | c1/32 | -25.66% | -26.97% | -34.52% | -29.43% | -32.96% | reject |
| Token2Wav 4 steps, run 1 | c8/128 | -14.49% | -11.25% | -15.03% | -54.87% | -16.41% | reject |
| Token2Wav 4 steps, run 2 | c8/128 | +19.60% | +1.36% | +16.62% | +2.61% | +17.24% | reject: unstable |
| Token2Wav FP16 | c1/32 | -0.14% | -2.55% | -0.13% | -1.57% | -0.10% | reject |
| Token2Wav FP16 | c8/128 | -5.38% | +7.79% | -5.89% | +10.58% | -3.56% | reject: mixed |
| Codec left context 2 | c1/32 | -46.52% | -65.73% | -87.01% | -63.17% | -96.59% | reject |
| Codec chunk 32 | c1/32 | -2.57% | -1.60% | -2.64% | -9.45% | -2.49% | reject |

Every retained JSON row completed all requested prompts with zero request
failures. Token2Wav FP16 initially exposed a missing NPU dtype-alignment path
(`float` input against `Half` convolution bias). A temporary alignment patch
made it run, but the c1/c8 neutral ten-cell geometric aggregate was only
`+0.008%`, effectively zero, while introducing precision and maintenance risk.

No candidate qualified for WER or ASV evaluation. The remote source was
restored to clean `0dced5d4`, and the NPU was left with no vLLM worker process.
Raw benchmark JSON is in [`raw/`](raw/).
