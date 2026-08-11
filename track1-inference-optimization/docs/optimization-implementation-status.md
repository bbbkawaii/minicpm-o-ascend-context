# 优化实现状态（M1–M6 + C1）

> 日期：2026-08-11（评审修复后 + 官方单卡 Seed-TTS 矩阵）
> 依据：`docs/low-cost-model-optimization-plan.md`
> 状态：M1–M6、C1 已实现，评审 10 项问题已修复；本地测试通过。官方单卡 Seed-TTS 基线、三个性能候选与 TTS-Seed WER 门禁均已归档。

## 2026-08-11 官方单卡进展

- 基线：官方 Seed-TTS c1/c4/c8 矩阵已在一张物理 Ascend 910C 上完成，见
  `reports/official-seed-tts-910c-20260810/`。
- 当前最佳性能栈：Code2Wav Stage 2 `max_num_seqs=6` + Thinker Stage 0
  `max_num_seqs=5`（Ascend 图形状 `[1, 2, 4, 5]`）+ Code2Wav
  `token2wav_n_timesteps=9`。最新源码提交为 `fa13e254`；九步相对十步的
  同机紧邻 c8/128 配对结果为：吞吐 +8.33%、E2E -7.68%、音频 TTFP
  -6.46%、RTF -8.64%，TTFT +0.92% 变慢。完整候选矩阵 224/224 成功、零
  失败；详见 `optimization/005-token2wav-n-timesteps-9/` 和
  `reports/token2wav-steps9-910c-20260811/`。
- TTS-Seed 英文 WER 门禁已通过：1,088/1,088 条完成、均值 `0.032571`
  <= 源码阈值 `0.05`，请求/PCM/ASR 失败均为 0。没有发布的官方综合加权分，
  因此只以原始配对性能结果和明确的 WER 门禁作接受依据。
- 已否决：首块/稳定 codec 分块 10/25 与 10/32。前者在 c8 吞吐回退
  19.7%，后者 c8 TTFP 回退 8.4%。原始证据已保留在实验 002/003。
- 当前仍缺重新运行的官方 Video-MME 与 Daily-Omni 最终验证；性能结果不能
  替代这些门禁。

## 评审修复记录（10/10 完成）

| # | 问题 | 修复 |
|---|---|---|
| 1 [高] | C1 视频假验证 | URL fixture 构造真实 `video_url` 载荷；skipped 返回非零 |
| 2 [高] | 固定速率未实现 | 单调时钟控制 submit 时间，真正按 rate 发起 |
| 3 [高] | warm-up 污染统计 | warm-up 错误分离，不计入 requests/success_rate/exit |
| 4 [高] | 双卡资源无法逐卡汇总 | 采集器每 tick 每卡一行，汇总器按 device_id 分组 |
| 5 [中] | TPOP 口径错误 | token 缺失时 tpot=null；除数为首包后 token；加 output_token_throughput |
| 6 [中] | M4 逐 chunk 证据缺失 | 加 chunks 记录、first_audio_duration、max_playback_gap |
| 7 [中] | HTTP 状态分布缺失 | RequestError.http_status + http_status_distribution |
| 8 [中] | M6 产物不完整 | 每档 command.txt、round0 冷启动、summarize_matrix.py 稳态汇总 |
| 9 [中] | 错误未脱敏 | 正则脱敏 authorization/token/password/api_key/Bearer |
| 10 [低] | C1 可复现不足 | 固定 seed=42；fixture 补 source/license/sha256 |

> 修复过程中另发现并修复：npu-smi 的 device_id 应取 chip 索引(0/1)而非组号(4)，否则双卡数据被归到同一组。

## 910C 正式指标（完整复现证据已归档）

完整报告：`reports/baseline-910c-formal-20260807.md`
原始数据：`reports/rerun-20260807/`（benchmark JSON + 逐卡资源 + environment.txt）

| 场景 | 指标 | 值 |
|---|---|---|
| 文本 | TTFT p50/p95/p99 | 92.6 / 96.5 / 102.9 ms |
| 文本 | ITL p50 | 19.5 ms |
| 文本 | E2E p50 | 780 ms |
| 文本 | 吞吐 | 2.55 req/s |
| 文本 | TPOT | null（流式接口无 usage token，不字符替代） |
| 音频 | TTFT p50 | 557 ms |
| 音频 | TTFP p50 | 1295 ms |
| 音频 | ICL p50 | 239.5 ms |
| 音频 | RTF p50 | 0.406 |
| 音频 | 播放安全率 | 1.0 |

逐卡资源（音频期间）：device 0 AICore 峰值 69%、device 1 77%；两卡 HBM 51256 / 45292 MB；host 峰值 122.8 GB。

## 测试

```bash
cd track1-inference-optimization
python3 -m unittest discover -s tests -v   # 27 项全部通过
bash -n baseline/*.sh                       # shell 语法通过
```

## 未完成 / 待办

- [x] **早期 E1 全阶段 max_num_seqs 实验** → 两卡文本条件下基线(4)为
  Pareto 最优（见 `reports/e1-maxnumseqs-20260807.md`）；该结论不再用于排除
  官方单卡音频的 Stage2 独立调参，Stage2=6 已通过正式矩阵。
- [x] **官方单卡 Seed-TTS 矩阵 + Stage2=6 + Stage0=5 + token2wav=9**
  → 当前最佳性能候选；最新 c8 同机配对与原始结果见
  `reports/token2wav-steps9-910c-20260811/`。
- [x] **TTS-Seed 英文 WER 门禁** → `0.032571 <= 0.05`，1,088/1,088
  完成、零失败；见 `optimization/005-token2wav-n-timesteps-9/`。
- [x] **E2 batched_tokens 实验** → 对 conc-8 TTFT 悬崖无影响,保留基线 8192;悬崖非批处理容量问题(见 `reports/e2-batchedtokens-20260807.md`)
- [x] **E3 显存预算实验** → B3(0.90/0.58/0.32)候选(文本 +3.5% 吞吐/-9% TTFT),需音频复验;B1 否决、B2/B4 噪声;悬崖同样非显存问题(见 `reports/e3-memory-20260807.md`)
- [ ] **B3 音频复验** + C1/剩余正确性门禁(若通过则采用 B3)
- [ ] **P1 分阶段 timeline**(E2+E3 均指向:conc-8 悬崖是 scheduler/背压问题,需 profiler 定位)
- [ ] M6 audio 矩阵(conc 1/2/4,需 ~1h 算力)
- [ ] C1 视频 fixture 填充真实 URL + SHA256 + 许可证
- [ ] C2 正式效果集：重新运行 Daily-Omni / Video-MME 最终验证
