# MiniCPM-o 4.5 昇腾推理后续优化实现方案

> 面向分支：`track1/4-low-cost-optimization-plan`  
> 基线日期：2026-08-07  
> 执行目标：让低成本编码模型按小任务稳定推进，昂贵模型只处理少数高风险问题

## 1. 结论

当前最值得投入的方向不是立即修改模型或编写 Ascend C 算子，而是先补齐正式评测闭环，再用自动化单变量实验搜索两卡部署参数。仓库已经在 Ascend 910C × 2 上跑通文本和语音输出，但图像、音频、视频输入及三个正式效果集仍未验证，现有文本基线只有 10 个请求、音频基线只有 5 个请求，且没有持续采集 NPU 利用率、chunk latency 或高并发曲线。证据见 `reports/baseline-910c-20260807.md:10-20`、`reports/baseline-910c-20260807.md:22-33`、`reports/baseline-910c-20260807.md:35-60`。

推荐优先级如下：

1. **P0：评测可信度**——补齐 warm-up、失败率、ITL/ICL、并发矩阵、NPU 时间序列和三轮重复实验。
2. **P0：正确性门禁**——先跑通所有模态，再接入 Daily-Omni、TTS-Seed、Video-MME。
3. **P1：配置级优化**——搜索 `max_num_seqs`、批处理 token 上限、阶段显存预算和 codec chunk 参数。
4. **P1：流水线级优化**——用 profiler 证明阻塞点后，再优化 Thinker→Talker→Code2Wav 的等待和重叠。
5. **P2：量化**——正确性门禁稳定后才测试官方支持的量化路径。
6. **P3：算子优化**——只有 profiler 证明单个 Ascend 算子是主要瓶颈时才进入。

这一顺序延续了仓库已有的 Gate 设计：先正确性和正式基线，再做 deploy config、scheduler、流水线、图模式、量化，最后才是自定义算子。证据见 `docs/execution-plan.md:23-52`。

## 2. 当前状态审计

### 2.1 已完成

- 已固定正式测试环境：Atlas 800T A3、Ascend 910C × 2、CANN 9.0.0、vLLM-Omni `0.25.0+npu`，上游代码为 `0a12ac52`。证据见 `reports/baseline-910c-20260807.md:8-20`。
- 已使用 `minicpmo_4_5_2gpu.yaml`，Thinker 位于 NPU 0，Talker 与 Token2Wav 位于 NPU 1。证据见 `reports/baseline-910c-20260807.md:18-20`。
- 文本输出和 24 kHz 语音输出已通过最小 smoke。证据见 `reports/baseline-910c-20260807.md:22-27`。
- 文本基线为 TTFT p50 96.7 ms、E2E p50 794 ms；音频基线为 TTFP p50 1.279 s、E2E p50 3.122 s、RTF p50 0.415。证据见 `reports/baseline-910c-20260807.md:35-53`。
- 本地 benchmark 已能解析 SSE 文本增量、WAV 音频 chunk，并计算 TTFT、TTFP、E2E 与 RTF。证据见 `baseline/benchmark_text.py:36-123`、`baseline/benchmark_audio.py:51-129`、`baseline/benchmark_audio.py:132-221`。
- benchmark 的解析与汇总逻辑已有单元测试。证据见 `tests/test_baseline_tools.py:22-38`、`tests/test_audio_benchmark.py:27-108`。

### 2.2 当前不足

1. **P95 可信度不足**：文本只有 10 个请求，音频只有 5 个请求；5 个样本的 p95 基本等同于最大值附近，不能用于判断小幅优化。证据见 `reports/baseline-910c-20260807.md:35-53`。
2. **负载不可比**：文本使用并发 2，音频使用并发 1；当前吞吐只能各自作为初始参考，不能说明系统的容量上限。证据见 `reports/baseline-910c-20260807.md:35-53`。
3. **没有 warm-up 隔离**：两个 benchmark 直接把全部请求计入统计，没有 `--warmup-requests`。证据见 `baseline/benchmark_text.py:126-154`、`baseline/benchmark_audio.py:224-252`。
4. **缺少流式细分指标**：文本只记录第一个文本 delta 和结束时间，未记录 ITL/TPOP；音频只记录首、末音频到达时间和 chunk 数，未记录每个 chunk 的到达间隔。证据见 `baseline/benchmark_text.py:76-102`、`baseline/benchmark_audio.py:160-220`。
5. **并发失败会中断整轮**：future 直接调用 `result()`，任一请求抛错会使汇总失败，无法输出成功率和错误分类。证据见 `baseline/benchmark_text.py:140-154`、`baseline/benchmark_audio.py:238-252`。
6. **缺少资源证据**：基线报告明确记录 NPU 峰值未 profile、Host memory 未记录，稳定性仅约 15 分钟。证据见 `reports/baseline-910c-20260807.md:55-61`。
7. **正式正确性未完成**：图像、音频、视频输入、Daily-Omni、TTS-Seed、Video-MME 都是 TBD。证据见 `reports/baseline-910c-20260807.md:28-33`。
8. **实验目录只有规范，没有执行器**：仓库定义了每个实验应保存 hypothesis、commands、results 和 conclusion，但目前没有自动建立和对比这些产物的脚本。证据见 `optimization/README.md:1-11`。

### 2.3 上游边界

上游竞赛 RFC 要求 benchmark 覆盖 TTFT、chunk latency、E2E、吞吐、并发、资源和稳定性，并要求性能 PR 附前后数据及正确性验证。[vLLM-Omni RFC #5075](https://github.com/vllm-project/vllm-omni/issues/5075)

当前上游官方 benchmark 已经定义并输出 TTFT、TPOP、ITL、TTFC、ICL、TTFP 和 RTF，因此本仓库应优先复用或对齐其口径，而不是再发明一套不可比较的指标。[vLLM-Omni Benchmark CLI](https://docs.vllm.ai/projects/vllm-omni/en/stable/cli/bench/serve/)

基线 commit `0a12ac52` 的两卡配置已经启用 `async_chunk`，三阶段 `max_num_seqs` 均为 4，阶段显存预算依次为 0.90、0.55、0.35；NPU 平台对 Thinker 和 Talker 使用 `PIECEWISE` 图模式。[固定 commit 的两卡配置](https://raw.githubusercontent.com/vllm-project/vllm-omni/0a12ac52/vllm_omni/deploy/minicpmo_4_5_2gpu.yaml)

## 3. 优化目标与否决门禁

### 3.1 主指标

每个实验必须分别报告：

- 文本：TTFT p50/p95、ITL p50/p95、E2E p50/p95、输出 token/s、请求吞吐、失败率。
- 语音：文本 TTFT、音频 TTFP、ICL、E2E、RTF、生成音频秒数/墙钟秒、请求吞吐、失败率。
- 系统：两个 NPU 的利用率 p50/p95、HBM 峰值、Host memory 峰值、服务重启数。
- 正确性：smoke、模态样例、正式效果集结果和相对基线变化。

`new`：上述扩展将建立在当前 TTFT/E2E 汇总 `baseline/benchmark_text.py:105-123` 和 TTFP/RTF 汇总 `baseline/benchmark_audio.py:94-129` 上。

### 3.2 保留候选优化的条件

一个候选优化只有同时满足以下条件才能进入下一轮：

- 三轮重复实验中至少两轮在主指标上同向改善。
- p50 或吞吐改善至少 3%，或者 p95 改善至少 5%；低于该幅度视为噪声，除非置信区间明确不重叠。
- 请求成功率不低于 99%，且不得出现服务重启。
- Daily-Omni、TTS-Seed、Video-MME 不低于主办方门槛；门槛未知时不得声称“效果保持”。
- HBM 不得持续超过 90%，不得出现 OOM、设备健康异常、HCCL 或 CANN 错误。

`Assumption A1`：3%/5% 是本项目的实验筛选阈值，不是官方评分规则；原因是当前仓库未包含官方评分权重或最小有效提升。

### 3.3 立即否决条件

- 任一已通过模态重新失败。
- 音频采样率不再是 24 kHz，或音频为空、截断、文本与语音明显不一致。
- 任何一轮出现 OOM、进程崩溃、设备复位或结果不可复现。
- 为取得更快数字而缩短输出、改变 prompt、关闭必测模态或使用不同数据集。

当前音频 benchmark 已验证每个 chunk 的采样率一致且总时长大于零，可直接扩展为该门禁。证据见 `baseline/benchmark_audio.py:180-220`。

## 4. 低成本模型执行协议

低成本模型一次只领取一个任务目录，禁止同时改 benchmark、deploy config 和上游 runtime。仓库现有协作规则已经要求先记录基线、做最小修改、运行测试并提交小 commit。证据见 `CONTRIBUTING.md:36-44`。

### 4.1 每个任务的输入

执行模型必须收到：

```text
任务编号：例如 M1
允许修改文件：明确到目录或文件
只读参考：明确列出
基线 commit：37c1dd3
验收命令：可复制执行
禁止事项：不得改依赖版本、不得删除产物、不得跨任务
输出：变更摘要、测试结果、风险、下一步
```

### 4.2 每个任务的固定循环

1. 读取任务指定文件和 `track1-inference-optimization/CONTEXT.md`。
2. 先运行任务的现有测试，记录基线。
3. 只修改允许文件。
4. 增加失败测试，再实现功能，再运行全部本地测试。
5. 在无 NPU 的本地环境只验证解析、编排和文档；不得伪造性能结果。
6. 在 910C 环境运行时，保存原始 JSON、日志摘要和命令。
7. 任何不确定的 vLLM 参数必须通过当前 commit 的 `--help` 或 YAML 确认。
8. 提交一个原子 commit，不自动合并多个实验。

### 4.3 必须升级给高能力模型的情况

- 需要修改 vLLM scheduler、EngineCore、connector、模型实现或 Ascend kernel。
- 出现 segmentation fault、heap corruption、CANN/HCCL 内部错误或设备失联。
- 两次合理的显存调整仍然 OOM。
- 优化后性能提高但任一效果集下降。
- 需要判断量化校准方法、算子融合正确性或跨平台 CUDA 回归。

这些升级条件与仓库现有执行手册对 NPU 内部错误、OOM、scheduler、connector、算子和量化的边界一致。证据见 `docs/track1-execution-manual.md:46-76`。

## 5. 实施阶段

## 阶段 M：把 benchmark 变成可信仪器（P0）

### M1：统一结果 schema

`new`：新增 `baseline/metrics.py`，从 `baseline/benchmark_text.py:16-33` 中迁移 percentile/distribution 公共逻辑，并定义 `RunMetadata`、`RequestError`、`Distribution`。

实现步骤：

1. 定义 schema version，例如 `"schema_version": 1`。
2. 每份输出写入 UTC 时间、模型名、base URL、请求数、并发、warm-up 数、prompt SHA256、Python 版本。
3. 指标统一输出 count、mean、p50、p95、p99、min、max。
4. 错误只保存类型和脱敏摘要，不保存 token 或凭据。
5. 更新两个 benchmark 使用相同 schema。
6. 增加空输入、单样本、偶数样本、异常请求的单元测试。

验收：

```bash
cd track1-inference-optimization
python3 -m unittest discover -s tests -v
```

### M2：warm-up、错误隔离与请求速率

`new`：扩展 `baseline/benchmark_text.py:126-160` 和 `baseline/benchmark_audio.py:224-258`。

实现步骤：

1. 增加 `--warmup-requests`，warm-up 完成后才开始计时。
2. 增加 `--request-rate`；未设置时保持 closed-loop，设置时按固定速率发起请求。
3. 每个 future 捕获异常并生成 `RequestError`，整轮继续执行。
4. 汇总成功数、失败数、超时数、HTTP 状态分布和成功率。
5. 失败率大于 1% 时命令返回非零状态，但仍写出 JSON。
6. 增加 mock HTTP 500、超时和部分成功测试。

验收：构造 1 个成功、1 个失败响应时，输出必须包含两条请求记录，进程返回非零，JSON 可解析。

### M3：文本 ITL/TPOP 与 token 指标

`new`：扩展 `RequestMetric`，当前结构只有 TTFT、E2E、输出字符数。现状见 `baseline/benchmark_text.py:16-21`。

实现步骤：

1. 记录每个非空文本 delta 的到达时间。
2. 计算相邻 delta 的 ITL 列表。
3. 记录服务返回的 usage token；若流式接口无 usage，则把 token 数标记为 `null`，禁止用字符数冒充 token。
4. 计算 TPOP：首个 delta 到完成的时间除以后续输出单元数。
5. 输出 request throughput 与 output token throughput，后者仅在 token 数可用时产生。
6. 用可控 fake clock 写单元测试，避免依赖真实 sleep。

验收：三次 delta 到达时间为 0.1/0.2/0.4 秒时，ITL 必须为 0.1/0.2 秒。

### M4：音频 ICL、首包大小与抖动

`new`：扩展 `AudioRequestMetric`，当前只保存首末时间、chunk 数和 PCM 字节数。现状见 `baseline/benchmark_audio.py:30-48`。

实现步骤：

1. 保存每个音频 chunk 的到达时间、PCM 字节和音频时长。
2. 计算 ICL p50/p95/p99、首包 PCM 时长、最大播放缺口。
3. 定义播放安全指标：`arrival_gap <= previous_chunk_audio_duration` 的比例。
4. 保留当前 RTF E2E 和 audio-window 两种定义，不合并口径。
5. 增加不同 chunk 大小、变化采样率和空 chunk 测试。

验收：现有 `tests/test_audio_benchmark.py:67-108` 继续通过，并新增 ICL 数值断言。

### M5：NPU/Host 资源采集器

`new`：新增 `baseline/collect_resources.sh` 和 `baseline/summarize_resources.py`；当前报告只有一次峰值描述且缺少 host memory。对比 `reports/baseline-910c-20260807.md:55-60`。

实现步骤：

1. 每秒执行只读的 `npu-smi info` 或当前镜像支持的 dmon 命令。
2. 同时记录时间戳、每卡利用率、HBM、功耗和温度；用 `/proc/meminfo` 记录 host memory。
3. 原始数据写 CSV，summary 写 JSON。
4. 采集命令不可用时明确失败，不写零值。
5. 通过 trap 停止后台采集器，保留已产生数据。
6. 本地测试使用 fixture，不依赖真实 NPU。

验收：fixture 含两个设备和三个时间点时，summary 正确给出每卡峰值与 p50/p95。

### M6：并发矩阵编排器

`new`：新增 `baseline/run_benchmark_matrix.sh`，复用现有两个 benchmark 的 CLI。现有入口见 `reports/baseline-910c-20260807.md:79-85`。

固定矩阵：

| 模式 | 并发 | 正式请求数 | warm-up |
|---|---:|---:|---:|
| text | 1, 2, 4, 8 | 每档 100 | 每档 10 |
| text+audio | 1, 2, 4 | 每档 30 | 每档 3 |

实现步骤：

1. 每档开始前检查 `/v1/models`。
2. 启动资源采集，运行 benchmark，停止资源采集。
3. 每档独立目录，保存 command、result、resource、server log tail。
4. 任一档失败时继续保存证据，但不自动进入更高并发。
5. 连续执行三轮，轮次之间不重启服务；另做一轮冷启动数据但不混入稳态统计。

验收：`DRY_RUN=1` 能在无 NPU 环境打印全部计划命令且不访问服务。

## 阶段 C：补齐正确性门禁（P0）

### C1：四模态 smoke

`new`：新增 `baseline/smoke_multimodal.py` 和 `fixtures/manifest.json`，扩展当前只验证文本的 smoke 路径。当前缺口见 `reports/baseline-910c-20260807.md:22-33`。

实现步骤：

1. 文本、图片、音频、视频各准备一个许可证清晰的小 fixture；大文件只记录下载 URL 与 SHA256。
2. 每个请求固定模型、temperature、seed、max_tokens 和 `chat_template_kwargs`。
3. 校验 HTTP 成功、文本非空；语音额外校验 24 kHz、非零时长。
4. 输出机器可读 JSON，不以“看起来合理”作为唯一判断。
5. 所有 fixture 记录来源、许可证和 SHA256。

验收：四种输入各运行 5 次，20/20 成功，无空响应。

### C2：正式效果集适配

`new`：新增 `evaluation/README.md` 和只保存命令/结果摘要的 runner；不得提交受限数据集。

实现步骤：

1. 从官方 starter kit 确认 Daily-Omni、TTS-Seed、Video-MME 的精确命令和评分脚本。
2. Daily-Omni 显式设置 `enable_thinking=false`；这是上游文档要求的答案提取口径。[MiniCPM-o 官方 serving 文档](https://docs.vllm.ai/projects/vllm-omni/en/latest/user_guide/examples/online_serving/minicpmo/)
3. 保存数据集版本、命令、模型 revision、输出摘要和分数。
4. 建立 `quality-gate.json`，记录基线分数和允许退化阈值。
5. 每个性能候选自动调用相同的效果门禁。

验收：三个数据集均有可复制命令、原始结果路径和基线分数；未获得官方数据时保持 `blocked`，不得填模拟分数。

## 阶段 E：低风险配置搜索（P1）

所有配置实验都从 commit `0a12ac52` 的 `minicpmo_4_5_2gpu.yaml` 复制新文件，不修改上游原文件。基线配置的可调字段和默认值以[固定 commit YAML](https://raw.githubusercontent.com/vllm-project/vllm-omni/0a12ac52/vllm_omni/deploy/minicpmo_4_5_2gpu.yaml)为准。

### E1：`max_num_seqs` 容量曲线

实验矩阵：三个 stage 同步设置 1、2、4；只有 4 稳定且高并发仍排队时才试 6。

实现步骤：

1. 建立 `optimization/001-max-num-seqs/{1,2,4}/deploy.yaml`。
2. 每个值完全重启服务，等待健康检查和固定 warm-up。
3. 运行 M6 全矩阵和 C1 smoke。
4. 比较并发 1 的延迟与并发 4/8 的吞吐、失败率和 HBM。
5. 选择 Pareto 最优值，不只选最高吞吐。

停止条件：任何 stage OOM，或并发提高但 p95 恶化超过 20%。

### E2：Thinker `max_num_batched_tokens`

基线 NPU override 为 8192。实验值：4096、8192、12288；16384 只有 HBM 余量明确时才试。固定 commit 证据见[两卡配置 NPU override](https://raw.githubusercontent.com/vllm-project/vllm-omni/0a12ac52/vllm_omni/deploy/minicpmo_4_5_2gpu.yaml)。

实现步骤：每个值运行短文本、长文本、图片和视频四类输入，分别观察 TTFT、吞吐和 HBM；不得只用一句话 prompt 得出结论。

### E3：两卡显存预算

基线为 Thinker 0.90、Talker 0.55、Code2Wav 0.35。因为 Talker 与 Code2Wav 共享 NPU 1，两个比例必须作为一组并确保留出 runtime headroom。[固定 commit 配置](https://raw.githubusercontent.com/vllm-project/vllm-omni/0a12ac52/vllm_omni/deploy/minicpmo_4_5_2gpu.yaml)

候选组：

| 组 | Thinker | Talker | Code2Wav | 用途 |
|---|---:|---:|---:|---|
| B0 | 0.90 | 0.55 | 0.35 | 原始基线 |
| B1 | 0.88 | 0.52 | 0.34 | 稳定性/余量 |
| B2 | 0.92 | 0.55 | 0.35 | Thinker KV 容量 |
| B3 | 0.90 | 0.58 | 0.32 | Talker 偏重 |
| B4 | 0.90 | 0.52 | 0.38 | Code2Wav 偏重 |

`Assumption A2`：B1-B4 是待验证搜索点，不是上游推荐值；每组都必须先启动、smoke，再跑压力测试。

### E4：codec chunk 参数

基线 connector 使用 `codec_chunk_frames: 25`、`codec_left_context_frames: 3`。[固定 commit 配置](https://raw.githubusercontent.com/vllm-project/vllm-omni/0a12ac52/vllm_omni/deploy/minicpmo_4_5_2gpu.yaml)

实验只改变 `codec_chunk_frames`：20、25、30；保持 left context 为 3。重点观察 TTFP、ICL、RTF、音频连续性和 TTS-Seed，不得仅根据速度选择。

停止条件：音质门禁下降、chunk 拼接出现可闻断裂、音频总时长异常或服务端 cache 错误。

### E5：图模式 A/B

基线对 Thinker 和 Talker 使用 `PIECEWISE`，Code2Wav 为 eager。只比较：基线 vs 明确关闭图模式的诊断配置；不要让低成本模型自行设计新的图捕获实现。上游文档也指出 Code2Wav 仍需专门的静态 shape graph wrapper 才能安全捕获。[MiniCPM-o pipeline notes](https://docs.vllm.ai/projects/vllm-omni/en/latest/user_guide/examples/online_serving/minicpmo/)

用途：判断当前图模式收益及首次编译成本，不将关闭图模式作为默认优化。

## 阶段 P：Profiler 驱动的代码优化（P2）

### P1：分阶段时间线

`new`：在上游 fork 中增加可开关的阶段时间戳，记录 request id、stage enqueue/start/first-output/end，不记录用户内容。上游 pipeline 的当前阶段边界是 Thinker→Talker→Code2Wav，官方说明 Talker 连续批处理、Code2Wav 按 exact-shape chunk 批处理。[MiniCPM-o pipeline notes](https://docs.vllm.ai/projects/vllm-omni/en/latest/user_guide/examples/online_serving/minicpmo/)

实现步骤：

1. 先定位 commit `0a12ac52` 中现有 tracing/stats 接口。
2. 写 CPU 单元测试验证事件顺序和关闭开关时零输出。
3. 在 910C 上采集并发 1/2/4 各 20 个请求。
4. 将总 E2E 拆成队列、Thinker、bridge、Talker、Code2Wav 和网络序列化。
5. 只有占 E2E 超过 15% 的区间才进入下一项代码优化。

### P2：SharedMemoryConnector 等待参数

基线 connector 轮询间隔为 10 ms。只有 P1 显示 connector 等待占比明显时，才实验 10/5/2 ms；同时记录 host CPU，避免用忙轮询换取表面延迟。[固定 commit 配置](https://raw.githubusercontent.com/vllm-project/vllm-omni/0a12ac52/vllm_omni/deploy/minicpmo_4_5_2gpu.yaml)

### P3：Code2Wav exact-shape batching

只有 P1 显示 Code2Wav 排队或 shape 分桶是主要瓶颈时执行。此任务必须升级给高能力模型，因为它涉及 request-owned cache、exact-shape batch 和潜在音频正确性回归；上游文档明确该阶段的缓存与 shape 边界。[MiniCPM-o pipeline notes](https://docs.vllm.ai/projects/vllm-omni/en/latest/user_guide/examples/online_serving/minicpmo/)

### P4：序列化与 base64 开销

只有 profiler 显示 NPU 已完成但客户端 TTFP/E2E 仍有显著空档时执行。比较服务内部 first-output 时间与客户端到达时间，判断 WAV 封装/base64/SSE 是否是瓶颈，再决定是否优化 buffer 复用或编码路径。

## 阶段 Q：量化与算子（P3）

### Q1：量化可行性 Gate

在以下条件全部满足前不开始量化：

- C2 三个正式效果集已有稳定基线。
- M6 已完成三轮并发矩阵。
- 官方环境确认支持目标量化格式。
- 量化权重来源、许可证、校准方法和 revision 可记录。

vLLM-Ascend 的 W8A16 支持在上游发布说明中仍标注过 Experimental，因此不能直接把“能加载”当作比赛可用。[vLLM-Ascend release notes](https://github.com/vllm-project/vllm-ascend/blob/main/docs/source/user_guide/release_notes.md)

### Q2：量化实验顺序

1. 先 Thinker-only 权重量化，Talker/Code2Wav 保持基线。
2. 跑 C1 与 C2 全部门禁。
3. 跑 M6；比较 HBM、TTFT、吞吐和效果。
4. 只有 Thinker 通过后才考虑 Talker。
5. 不量化 Code2Wav，除非官方路径明确支持且 TTS-Seed 无退化。

### Q3：自定义算子准入

只有 profiler 显示一个算子占目标阶段至少 20%，且现有 vLLM-Ascend 没有等价 fused op 时，才建立 Ascend C 候选。必须同时准备：CPU/reference 实现、shape/dtype 测试、随机误差测试、端到端正确性、前后 profile 和非 Ascend fallback。

## 6. 任务拆分与成本控制

| 批次 | 任务 | 适合模型 | 预计工作量 | 是否需要 910C |
|---|---|---|---:|---|
| 1 | M1 schema + tests | 低成本模型 | 2–4 小时 | 否 |
| 2 | M2 warm-up/error | 低成本模型 | 2–4 小时 | 否 |
| 3 | M3 文本细分指标 | 低成本模型 | 2–4 小时 | 否 |
| 4 | M4 音频 ICL | 低成本模型 | 2–4 小时 | 否 |
| 5 | M5 资源采集器 | 低成本模型 | 3–5 小时 | 最终验证需要 |
| 6 | M6 矩阵编排器 | 低成本模型 | 2–4 小时 | 最终运行需要 |
| 7 | C1 四模态 smoke | 低成本模型 | 3–5 小时 | 是 |
| 8 | C2 正式效果门禁 | 中等模型 + 人工确认 | 0.5–1 天 | 是 |
| 9 | E1–E5 单变量实验 | 低成本模型执行 | 1–2 天算力 | 是 |
| 10 | P1 分阶段 tracing | 高能力模型 review | 0.5–1 天 | 是 |
| 11 | P2/P4 聚焦优化 | 视 profiler 决定 | 1–2 天 | 是 |
| 12 | Q1/Q2 量化 | 高能力模型 | 1–2 天 | 是 |

低成本模型负责机械且可测试的工作：解析、schema、CLI、fixture、编排、文档、运行单变量实验。高能力模型只用于：跨进程流水线、NPU runtime、量化精度、算子和崩溃定位。

## 7. 实验目录与产物

每个实验继续遵守现有 `optimization/README.md:3-11` 的五类产物，并增加 manifest：

```text
optimization/001-max-num-seqs/
├── manifest.yaml
├── hypothesis.md
├── configs/
├── commands.md
├── runs/
│   ├── run-01/
│   │   ├── benchmark.json
│   │   ├── resources.csv
│   │   ├── resources-summary.json
│   │   └── server-log-tail.txt
│   ├── run-02/
│   └── run-03/
├── comparison.json
└── conclusion.md
```

`new`：`manifest.yaml` 至少记录 base commit、上游 commit、模型 revision、镜像、硬件、唯一变量、基线值、候选值、正确性门禁和执行状态。

## 8. 最终验收

### 工具验收

- [ ] `python3 -m unittest discover -s tests -v` 全部通过。
- [ ] `bash -n baseline/*.sh` 全部通过。
- [ ] benchmark 的一个请求失败不会丢失整轮 JSON。
- [ ] 文本输出包含 TTFT/ITL/TPOP/E2E/失败率。
- [ ] 音频输出包含 TTFT/TTFP/ICL/RTF/E2E/失败率。
- [ ] 资源缺失明确标记 unavailable，不写成 0%。

### 基线验收

- [ ] 四模态 smoke 20/20 通过。
- [ ] Daily-Omni、TTS-Seed、Video-MME 均有真实基线。
- [ ] text 并发 1/2/4/8 与 audio 并发 1/2/4 各完成三轮。
- [ ] 30 分钟稳定性成功率至少 99%，无服务重启。
- [ ] 每轮保存两个 NPU 的利用率和 HBM 时间序列。

### 优化验收

- [ ] 至少完成 E1–E4，且每个候选只有一个主要变量。
- [ ] 最终配置在三轮中至少两轮同向改善。
- [ ] 正确性和音频质量门禁无退化。
- [ ] 最终报告包含保留和否决的实验，不只展示最好结果。
- [ ] 上游 PR 小而聚焦，附硬件、版本、命令、前后数据和正确性证据；这与仓库 `CONTRIBUTING.md:56-63` 及上游 RFC 要求一致。

## 9. 非目标

- 不在基线未完整前修改模型结构。
- 不同时更换模型权重、vLLM 版本和 deploy config。
- 不把字符数当 token 数。
- 不把一次最佳结果当作有效提升。
- 不让低成本模型自行处理 NPU 内核崩溃或量化精度争议。
- 不提交模型权重、大型 profile、密钥、个人数据或受限数据集；现有仓库规则见 `CONTRIBUTING.md:56-63`。

## 10. Assumptions

1. **A1**：3% p50/吞吐、5% p95 作为内部筛选阈值；官方未确认该阈值。
2. **A2**：显存候选 B1-B4 仅用于 A/B 搜索，不代表上游推荐。
3. **A3**：“便宜的模型”指低成本编码/执行模型，而不是把 MiniCPM-o 4.5 替换成更小的参赛模型；这是根据“用便宜的模型去实现”与当前竞赛目标作出的解释。
4. **A4**：后续仍能获得同规格 Ascend 910C × 2 环境；若硬件或镜像变化，必须重建基线。

## 11. Open Questions

1. 官方最终评分公式、效果门槛和 starter kit 的确切版本是什么？
2. 当前 HiDevLab 实例是否还能在提交截止前持续使用？
3. 主办方是否允许提交量化权重，提交包容量上限是多少？
4. 最终成果是否必须先合入 vLLM-Omni `minicpm-challenge` 分支，还是允许提交独立 patch？

这些问题在得到官方书面答案前保持 open，不影响先完成 M1–M6 和 C1。

## 12. Grounding Manifest

- Grounded assertions: 37
- Assumptions: 4
- Open questions: 4
- Review rule: 任何描述现状但缺少 `path:line` 或官方链接的陈述都应视为缺陷；任何未来设计必须标记为 `new` 或列入 Assumptions。
