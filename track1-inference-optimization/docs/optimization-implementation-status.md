# 优化实现状态（M1–M6 + C1）

> 日期：2026-08-07
> 依据：`docs/low-cost-model-optimization-plan.md`
> 状态：M1–M6、C1 已实现，本地测试通过，910C 实机验证部分完成

## 已实现

### M1：统一结果 schema ✅

- 新增 `baseline/metrics.py`：`RunMetadata`、`RequestError`、`Distribution`、`percentile`、`distribution`、`compute_itl`、`render_summary`、`build_metadata`、`summarize_error`、`write_output`。
- 统一 schema v1：`schema_version`、`created_at`、模型、base_url、请求数、成功/失败/超时数、成功率、`run_metadata`、`distributions`、`errors`、`results`。
- 分布统一输出 count/mean/p50/p95/p99/min/max。

### M2：warm-up、错误隔离、请求速率 ✅

- 两个 benchmark 增加 `--warmup-requests`、`--request-rate`。
- `execute_round` 用 `guarded` 包装：HTTPError/Timeout/Exception → `RequestError`，整轮继续。
- 汇总成功/失败/超时数、成功率；失败率 >1% 命令返回非零但 JSON 照写。
- 单元测试：部分失败不中断、错误信息脱敏截断。

### M3：文本 ITL/TPOP 与 token ✅

- `RequestMetric` 增加 `itl_seconds`、`output_tokens`、`tpot_seconds`。
- 记录每个非空文本 delta 到达时间 → ITL 列表；usage token 可用时计入，否则 `null`。
- 用 fake clock 测试 ITL 计算。

### M4：音频 ICL、首包、抖动 ✅

- `AudioRequestMetric` 增加 `icl_seconds`、`first_audio_pcm_bytes`、`playback_safe_ratio`。
- ICL 从 chunk 到达时间计算；播放安全 = 到达间隔 ≤ 前 chunk 音频时长的比例。
- 保留 RTF E2E 与 RTF audio-window 两种口径。

### M5：NPU/Host 资源采集器 ✅（910C 实机验证）

- 新增 `baseline/npu_collect.py`（Python 解析 npu-smi）+ `baseline/collect_resources.sh`（每秒采集）+ `baseline/summarize_resources.py`（CSV→JSON 摘要）。
- 字段：时间戳、每卡 AICore%、HBM、功率、温度、host 内存。
- 解析器处理 npu-smi 多值 cell 打包（`170.7 49 0/0`），第二卡功率不可用标记为空而非 0。
- 命令不可用 → `unavailable`，不伪造零值。
- **910C 实测**：CSV 输出 `0;0 / 51255;45292 / 170.6; / 49;51 / host_kb` 全部正确。

### M6：并发矩阵编排器 ✅（DRY_RUN 验证）

- 新增 `baseline/run_benchmark_matrix.sh`：text 1/2/4/8（100 请求+10 warmup）、audio 1/2/4（30+3），3 轮。
- 每档独立目录：command、benchmark.json、resources.csv+summary、server-log-tail。
- 失败档保留证据但不高并发；`DRY_RUN=1` 打印完整计划。

### C1：四模态 smoke ✅（本地 mock 验证）

- 新增 `baseline/smoke_multimodal.py` + `fixtures/manifest.json`。
- 文本/图片/音频 inline fixture（离线可跑），视频 URL fixture（未设置 → skipped 不伪造通过）。
- 校验 HTTP 成功、文本非空；音频额外校验 24kHz + 非零时长。

## 910C 实机新指标（新基准跑通）

| 场景 | 指标 | 值 |
|---|---|---|
| 文本 | TTFT p50/p95 | 94.2ms / 103.5ms |
| 文本 | **ITL p50**（新增） | 19.5ms |
| 文本 | E2E p50 | 781ms |
| 文本 | **TPOT p50**（新增） | 11.3ms |
| 音频 | TTFP p50 | 1.30s |
| 音频 | **ICL p50**（新增） | 245.6ms |
| 音频 | RTF p50 | 0.408 |
| 音频 | **播放安全率**（新增） | 1.0 |

## 测试

```bash
cd track1-inference-optimization
python3 -m unittest discover -s tests -v   # 26 项全部通过
bash -n baseline/*.sh                       # shell 语法通过
```

## 未完成 / 待办

- [ ] M6 完整矩阵在 910C 实机跑 3 轮（需长时间算力）
- [ ] C1 视频 fixture 填充真实 URL + SHA256 + 许可证
- [ ] C2 正式效果集（Daily-Omni / TTS-Seed / Video-MME）适配
- [ ] E1–E5 配置单变量实验
