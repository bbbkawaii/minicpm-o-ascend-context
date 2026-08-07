# 优化实现状态（M1–M6 + C1）

> 日期：2026-08-07（评审修复后 + 910C 正式化）
> 依据：`docs/low-cost-model-optimization-plan.md`
> 状态：M1–M6、C1 已实现，评审 10 项问题已修复；本地测试通过。**910C 指标已正式化**（见 `reports/baseline-910c-formal-20260807.md` + `reports/rerun-20260807/`）

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

- [ ] M6 完整矩阵 910C 跑 3 轮（需长时间算力）
- [ ] C1 视频 fixture 填充真实 URL + SHA256 + 许可证
- [ ] C2 正式效果集（Daily-Omni / TTS-Seed / Video-MME）适配
- [ ] E1–E5 配置单变量实验


