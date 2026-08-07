# 优化实现状态（M1–M6 + C1）

> 日期：2026-08-07（评审修复后）
> 依据：`docs/low-cost-model-optimization-plan.md`
> 状态：M1–M6、C1 已实现，评审 10 项问题已修复；本地测试通过。**910C 新指标为 provisional**（待完整复现记录）

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

## 910C 新指标（⚠️ provisional，待补原始 JSON/命令/环境记录）

| 场景 | 指标 | 值 |
|---|---|---|
| 文本 | TTFT p50/p95 | 94.2ms / 103.5ms |
| 文本 | ITL p50 | 19.5ms |
| 文本 | E2E p50 | 781ms |
| 文本 | TPOT p50 | 11.3ms |
| 音频 | TTFP p50 | 1.30s |
| 音频 | ICL p50 | 245.6ms |
| 音频 | RTF p50 | 0.408 |
| 音频 | 播放安全率 | 1.0 |

> 这些数字在评审修复前采集，尚未附完整原始 JSON、执行命令和环境记录。按项目"有效结果"定义，应标记为 provisional，待重跑后正式化。

## 测试

```bash
cd track1-inference-optimization
python3 -m unittest discover -s tests -v   # 27 项全部通过
bash -n baseline/*.sh                       # shell 语法通过
```

## 未完成 / 待办

- [ ] 910C 重跑完整基准，补原始 JSON/命令/环境记录（正式化 provisional 指标）
- [ ] M6 完整矩阵 910C 跑 3 轮（需长时间算力）
- [ ] C1 视频 fixture 填充真实 URL + SHA256 + 许可证
- [ ] C2 正式效果集（Daily-Omni / TTS-Seed / Video-MME）适配
- [ ] E1–E5 配置单变量实验

