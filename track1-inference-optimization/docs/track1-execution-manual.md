# 赛道一执行施工手册

> 项目：MiniCPM-o 4.5 昇腾推理优化挑战赛<br>
> 路线：vLLM-Omni / Ascend 910C<br>
> 文档用途：交给执行模型逐步实施；每次只执行一个阶段，不允许跨 Gate 跳步
> 最后核对日期：2026-08-02

## 0. 最终目标

在官方统一昇腾环境中完成一套可以被主办方复现的 MiniCPM-o 4.5 推理方案，并在保持效果正确、输出稳定的前提下，优化以下指标：

- TTFT：收到请求到首个有效文本 token 的时间。
- 单 chunk latency：流式输出相邻 chunk 的生成延迟。
- TTFP：收到请求到首个可播放音频包的时间。
- E2E latency：收到请求到请求全部完成的时间。
- Throughput：单位时间内完成的请求数或有效输出量。
- 并发 session：系统能够稳定承载的同时会话数。
- 资源利用率：NPU 利用率、显存/内存占用和空闲浪费。
- 稳定性：长时间运行的成功率、错误率和恢复能力。

比赛采用“正确性和效果校验优先、性能排名随后、工程复现最后审查”的逻辑。因此，任何导致模型能力缺失、精度不合格或服务不稳定的性能数字，都不能当作有效成绩。

## 1. 执行模型的硬性规则

交给执行模型前，必须同时提供本文件和当前阶段编号。执行模型必须遵守以下规则：

1. 一次只执行一个 Gate。
2. 执行命令前先说明命令目的和可能修改的文件。
3. 不得自行升级、降级或重装 `torch`、`torch_npu`、`vllm`、`vllm-ascend`、`vllm-omni`、CANN。
4. 不得删除已有环境、模型、缓存、日志或结果文件。
5. 不得执行 `rm -rf`、`git reset --hard`、覆盖式复制等不可恢复命令。
6. 不得把密码、验证码、Access Token、Cookie 或 SSH 私钥写进仓库和日志。
7. 遇到版本不一致、NPU kernel 错误、进程崩溃或不确定参数时必须停止，并保存完整错误。
8. 每次实验只改变一个主要变量。
9. 每项有效优化至少重复三轮。
10. 没有正确性验证的数据不得标记为“性能提升”。
11. 官方 starter kit、评分脚本和赛事群公告优先级高于本手册。
12. 每个 Gate 完成后输出：做了什么、产生了哪些文件、结果、失败项、下一步建议。

## 2. 人与执行模型的职责边界

### 2.1 参赛者本人负责

- 比赛报名、HiDevLab 申请、账号登录和验证码。
- 选择硬件、创建和释放云端环境。
- 确认官方截止日期、最终硬件、镜像和提交要求。
- 授权代码仓库访问，但不向模型发送密码或长期 Token。
- 最终提交、视频录制和答辩出席。

### 2.2 执行模型可以负责

- 检查环境和版本。
- 建立源码、模型、配置和日志目录。
- 启动服务并执行测试。
- 编写、修改和测试脚本。
- 收集 Benchmark 和 NPU 监控数据。
- 分析日志、定位瓶颈并设计单变量实验。
- 生成性能报告、复现文档、PPT 内容和 PR 描述。

### 2.3 必须升级给高能力模型处理的情况

- 官方规则、starter kit 与本手册冲突。
- 镜像中的 vLLM/vLLM-Ascend/vLLM-Omni 版本不对齐。
- NPU kernel、HCCL、CANN、`torch_npu` 内部错误。
- 服务启动发生 segmentation fault、进程无日志退出或设备失联。
- 连续两次合理调整后仍然 OOM。
- 需要修改 MiniCPM-o 模型实现、scheduler、connector 或 Ascend 自定义算子。
- 优化后性能提升但效果、音频或稳定性下降。
- 需要选择是否量化、修改 chunk 策略或更改三阶段拓扑。

## 3. 总体阶段与 Gate

| Gate | 阶段 | 完成标志 |
|---|---|---|
| 0 | 官方信息与环境冻结 | 硬件、镜像、版本、代码 commit、模型 revision 全部有记录 |
| 1 | Ascend text smoke | 连续 20 次 text-only 请求成功 |
| 2 | 全模态正确性 | 文本、语音、图像、音频、视频路径均通过最小样例 |
| 3 | 正式 Benchmark 基线 | 正确性、延迟、吞吐、并发、资源和稳定性均有原始结果 |
| 4 | 优化实验 | 每项改动都有假设、单变量数据、三轮结果和正确性验证 |
| 5 | 最终复现与提交 | 干净环境可重跑，材料齐全，上游 PR 有明确状态 |

任何 Gate 未通过，不允许进入后续 Gate。

## 4. 目录约定

云端环境建议使用以下目录。`$WORKSPACE` 可以按 HiDevLab 实际路径修改，但确定后不得在同一轮实验中更换。

```bash
export WORKSPACE=/workspace/minicpm-ascend-competition
export UPSTREAM_DIR=/vllm-workspace/vllm-omni
export MODEL_ID=openbmb/MiniCPM-o-4_5
export SERVER_HOST=127.0.0.1
export SERVER_PORT=8099

mkdir -p "$WORKSPACE"/{source,reports/runs,logs,artifacts,models,experiments,submissions}
```

目录含义：

- `source/`：参赛仓库和辅助源码。
- `reports/runs/<RUN_ID>/`：每次运行的环境、命令、结果和摘要。
- `logs/`：服务和监控原始日志。
- `artifacts/`：WAV、截图、profile 等大文件。
- `models/`：模型路径说明或本地模型；不要重复下载已有缓存。
- `experiments/`：每个优化实验一个独立目录。
- `submissions/`：最终提交包。

## 5. Gate 0：创建和冻结环境

### 5.1 HiDevLab 环境选择

正式目标环境：

- 算力：昇腾 910C。
- 推荐镜像：vLLM-Omni `v0.25.0`。

如果 910C 暂时无资源，可以使用 910B4 做软件链路验证，但所有正式性能数据必须在官方指定的 910C 环境重新采集。不要用 310P 作为该全模态模型的主开发环境。

### 5.2 打开两个终端

- 终端 A：服务端，保持前台运行并观察日志。
- 终端 B：环境检查、请求、Benchmark 和监控。

在尚未确认 HiDevLab 是否支持后台任务持久化前，不要依赖 `nohup`。优先保留终端 A 的前台服务。

### 5.3 第一次进入环境后只做检查

在终端 B 执行：

```bash
date -u
hostname
pwd
uname -a
python3 --version
git --version
npu-smi info
```

验收条件：

- `npu-smi info` 能看到实际 NPU。
- 硬件型号与申请型号一致。
- 设备状态正常，没有明显健康告警。
- Python 版本处于 vLLM-Ascend 支持范围内，通常应为 `>=3.10,<3.13`。

如果 `npu-smi` 不存在或看不到设备：停止，不要安装软件；保存输出并检查是否进入了正确实例。

### 5.4 记录 Python 包版本

执行：

```bash
python3 - <<'PY'
from importlib import import_module

for name in ("torch", "torch_npu", "vllm", "vllm_ascend", "vllm_omni"):
    try:
        module = import_module(name)
        print(f"{name}={getattr(module, '__version__', 'unknown')}")
    except Exception as exc:
        print(f"{name}=ERROR {type(exc).__name__}: {exc}")
PY
```

随后执行：

```bash
python3 -m pip freeze | sort | grep -Ei 'torch|vllm|ascend|transformers|huggingface|stepaudio|librosa'
```

禁止事项：看到包版本与文档不同后，不要立即 `pip install -U`。先记录现状，由高能力模型判断版本对齐关系。

### 5.5 定位 vLLM-Omni 源码

执行：

```bash
python3 - <<'PY'
import inspect
import os
import vllm_omni

print(os.path.dirname(inspect.getfile(vllm_omni)))
PY
```

然后检查常见目录：

```bash
for candidate in /vllm-workspace/vllm-omni /workspace/vllm-omni; do
  if [ -d "$candidate" ]; then
    printf 'found=%s\n' "$candidate"
    git -C "$candidate" status --short --branch || true
    git -C "$candidate" rev-parse HEAD || true
  fi
done
```

如果只有已安装 Python 包而没有 Git 源码，先停止并记录；不要立即重新安装。需要确认比赛允许的源码基线和镜像内部布局。

### 5.6 建立本次运行目录

```bash
export RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-gate0"
export RUN_DIR="$WORKSPACE/reports/runs/$RUN_ID"
mkdir -p "$RUN_DIR"
```

将前述命令输出保存到：

- `$RUN_DIR/system.txt`
- `$RUN_DIR/npu-smi.txt`
- `$RUN_DIR/python-packages.txt`
- `$RUN_DIR/source-version.txt`

如果参赛仓库已经进入云端，可以直接执行：

```bash
bash baseline/run_gate0.sh
```

该脚本会自动记录系统、NPU、Python 包、源码 commit 和 deploy config。正式 HiDevLab 环境不要设置 `REQUIRE_NPU=0` 或 `REQUIRE_SOURCE=0`。

### 5.7 Gate 0 验收

必须回答以下问题：

- 实际硬件是什么？
- CANN/驱动是什么版本？
- Python、torch、torch_npu 版本是什么？
- vLLM、vLLM-Ascend、vLLM-Omni 版本或 commit 是什么？
- 模型从哪里加载，revision 是什么？
- 默认 deploy config 文件内容是什么？
- 官方 starter kit 是否已经拿到？

任何一项回答不了，Gate 0 不通过。

## 6. 获取代码与模型

### 6.1 代码原则

优先使用镜像内已经配套的 vLLM-Omni 源码。官方 NPU 文档表明 vLLM-Omni 依赖 vLLM-Ascend，并且不同版本必须对齐；使用最新 `main` 可能临时不可用。

如果镜像内已有 `/vllm-workspace/vllm-omni`：

```bash
cd /vllm-workspace/vllm-omni
git status --short --branch
git rev-parse HEAD
git describe --tags --always --dirty
```

不要在基线阶段直接切换分支、拉取 `main` 或修改源码。

### 6.2 私有参赛仓库

优先使用 SSH 或平台支持的安全凭据克隆。不要把 Token 写入命令历史、仓库文件或聊天内容。

```bash
cd "$WORKSPACE/source"
git clone git@github.com:airbate/minicpm-o-ascend-competition.git
```

如果 SSH 尚未配置，由参赛者本人完成 GitHub 授权；执行模型不得索取私钥或 Access Token。

### 6.3 检查模型缓存

先检查是否已有模型，避免重复下载：

```bash
find /root/.cache/huggingface /workspace /models -maxdepth 3 \
  -type d -iname '*MiniCPM*4_5*' 2>/dev/null | head -20
```

如果模型由服务命令自动从 Hugging Face 下载，第一次启动可能耗时很长。必须区分“正在下载”与“进程卡死”。观察磁盘占用、下载日志和网络错误，不要重复启动多个下载进程。

如果官方 starter kit 指定模型 revision，必须固定 revision，不能只写模型名称。

### 6.4 模型下载失败处理

按顺序检查：

1. 是否能够访问 Hugging Face。
2. 是否需要平台镜像源或 ModelScope 路径。
3. 磁盘剩余空间是否足够。
4. 是否已经有部分缓存。
5. 官方是否提供预置模型路径。

不要为了绕过网络问题下载来源不明的量化权重作为基线。

## 7. Gate 1：Ascend text-only smoke

### 7.1 检查 deploy config

进入 vLLM-Omni 源码根目录：

```bash
cd "$UPSTREAM_DIR"
find vllm_omni -path '*deploy*' -name 'minicpmo_4_5*.yaml' -print
```

查看实际默认配置：

```bash
sed -n '1,240p' vllm_omni/deploy/minicpmo_4_5.yaml
```

将文件复制到运行记录，但不修改原文件：

```bash
cp vllm_omni/deploy/minicpmo_4_5.yaml "$RUN_DIR/deploy-config.yaml"
sha256sum "$RUN_DIR/deploy-config.yaml" > "$RUN_DIR/deploy-config.sha256"
```

重要：不同 vLLM-Omni 版本的默认设备数量和阶段内存预算发生过变化。只能信任当前镜像实际文件和官方 starter kit，不能根据旧文章猜配置。

### 7.2 启动前设置

```bash
export VLLM_WORKER_MULTIPROC_METHOD=spawn
export MODEL_ID=openbmb/MiniCPM-o-4_5
export SERVER_PORT=8099
```

检查命令是否存在：

```bash
command -v vllm-omni || command -v vllm
vllm-omni --help 2>/dev/null | head -40 || vllm --help | head -40
```

不要同时启动两个服务进程。

### 7.3 在终端 A 启动服务

优先使用当前 v0.25.0 官方示例：

```bash
cd "$UPSTREAM_DIR"
vllm-omni serve "$MODEL_ID" \
  --omni \
  --deploy-config vllm_omni/deploy/minicpmo_4_5.yaml \
  --trust-remote-code \
  --host 0.0.0.0 \
  --port "$SERVER_PORT" \
  2>&1 | tee "$WORKSPACE/logs/server-gate1.log"
```

如果镜像只提供 `vllm` 命令，停止并先查看 `vllm serve --help`。确认支持 `--omni` 后，才可把命令替换为 `vllm serve`。

### 7.4 判断服务是否准备完成

在终端 B 执行：

```bash
curl -fsS "http://127.0.0.1:${SERVER_PORT}/v1/models" | python3 -m json.tool
```

如果失败：

- `connection refused`：服务尚未监听或已经退出，查看终端 A。
- 长时间无响应：检查模型是否仍在下载/加载。
- OOM：保存完整日志和 deploy config，不要连续随机修改内存参数。
- ImportError：记录包版本，不要直接升级。
- NPU kernel/CANN 错误：停止并交给高能力模型。

### 7.5 发送最小 text-only 请求

如果参赛仓库已克隆：

```bash
cd "$WORKSPACE/source/minicpm-o-ascend-competition/track1-inference-optimization"
python3 baseline/smoke_test.py \
  --base-url "http://127.0.0.1:${SERVER_PORT}/v1" \
  --model "$MODEL_ID" \
  | tee "$RUN_DIR/text-smoke.json"
```

如果脚本暂不可用，可用 curl：

```bash
curl -fsS "http://127.0.0.1:${SERVER_PORT}/v1/chat/completions" \
  -H 'Content-Type: application/json' \
  -d "{
    \"model\": \"${MODEL_ID}\",
    \"messages\": [{
      \"role\": \"user\",
      \"content\": [{\"type\": \"text\", \"text\": \"Reply with exactly: ASCEND_SMOKE_OK\"}]
    }],
    \"modalities\": [\"text\"],
    \"chat_template_kwargs\": {
      \"enable_thinking\": false,
      \"use_tts_template\": false
    },
    \"temperature\": 0,
    \"max_tokens\": 64,
    \"stream\": false
  }" | tee "$RUN_DIR/text-smoke-curl.json" | python3 -m json.tool
```

### 7.6 连续正确性测试

执行 20 次串行请求。执行模型应编写或复用脚本，输出至少包括：

- 成功数和失败数。
- 空响应数。
- 每次 E2E。
- 服务端错误摘要。

验收条件：20/20 请求成功，无空响应，无服务重启。

如果参赛仓库已经在云端，Gate 1 可以直接使用：

```bash
bash baseline/run_gate1.sh
```

脚本会等待 `/v1/models` 就绪，执行单次 smoke，并把 20 次稳定性结果保存到新的 `reports/runs/<RUN_ID>/` 目录。

### 7.7 Gate 1 输出文件

- 环境记录。
- deploy config 及 sha256。
- 服务启动命令。
- 完整服务日志。
- 单次 smoke JSON。
- 20 次稳定性摘要。
- Gate 1 结论。

## 8. Gate 2：全模态正确性

### 8.1 安装依赖前先检查

MiniCPM-o Talker 需要 `stepaudio2-minicpmo`。先检查：

```bash
python3 -c 'import stepaudio2; print("stepaudio2 available")' || true
python3 -m pip show stepaudio2-minicpmo || true
```

镜像如果缺少依赖，先保存检查结果，再依据镜像说明决定是否安装。不要自行重装整个 vLLM-Omni。

### 8.2 使用上游官方示例

```bash
cd "$UPSTREAM_DIR/examples/online_serving/minicpmo"
ls -la
```

依次执行，不要并行：

```bash
bash run_curl_multimodal_generation.sh text
bash run_curl_multimodal_generation.sh use_image
bash run_curl_multimodal_generation.sh use_audio '["text"]'
```

如果当前版本的脚本参数不同，先运行 `sed -n '1,240p'` 阅读脚本，不能猜参数。

### 8.3 流式文本与语音

根据当前源码中实际存在的脚本选择：

```bash
find . -maxdepth 1 -type f -iname '*stream*' -print
```

官方近期示例为：

```bash
python streaming_chat_completion.py \
  --base-url "http://127.0.0.1:${SERVER_PORT}/v1" \
  --output "$WORKSPACE/artifacts/minicpmo-stream.wav"
```

验收：

- 文本 delta 能持续输出。
- 产生非空 WAV。
- 音频可以正常解码和播放。
- WAV 为单声道 24 kHz，或与当前官方实现一致。
- 服务端没有阶段异常退出。

可以用 Python 标准库检查 WAV：

```bash
python3 - <<'PY'
import wave

path = "/workspace/minicpm-ascend-competition/artifacts/minicpmo-stream.wav"
with wave.open(path, "rb") as wav:
    print({
        "channels": wav.getnchannels(),
        "sample_width": wav.getsampwidth(),
        "sample_rate": wav.getframerate(),
        "frames": wav.getnframes(),
        "seconds": wav.getnframes() / wav.getframerate(),
    })
PY
```

### 8.4 Daily-Omni 正确性特别要求

Daily-Omni 的答案是 A–D 单字母。请求中必须显式设置：

```json
{
  "modalities": ["text"],
  "chat_template_kwargs": {
    "enable_thinking": false
  }
}
```

不要在纯文本正确性 Benchmark 中请求音频，否则会改变 assistant template，并额外测试 Talker/Code2Wav，无法和 text-only 基线公平比较。

### 8.5 Gate 2 验收矩阵

| 输入 | 输出 | 最小验证 |
|---|---|---|
| 文本 | 文本 | 非空、语义正确 |
| 文本 | 文本+语音 | WAV 可播放、采样率正确 |
| 图像+文本 | 文本 | 回答包含图像中的关键信息 |
| 音频+文本 | 文本 | 能识别音频问题并回答 |
| 视频+文本 | 文本 | 能回答视频内容问题 |

每一项保存请求、响应、服务日志片段和产物路径。

## 9. Gate 3：建立正式基线

### 9.1 Benchmark 前纪律

- 服务启动后先完成预热。
- 同一轮数据不得重启服务或更换配置。
- 同时只能有一个 Benchmark 客户端控制负载。
- 关闭不必要的后台任务。
- 保存服务日志和 NPU 监控。
- 正式评分脚本发布后，优先使用官方脚本。

### 9.2 预热

先发送至少 5 个不计入结果的请求。记录预热是否触发编译、图捕获或额外模型加载。

### 9.3 早期 text TTFT/E2E

```bash
cd "$WORKSPACE/source/minicpm-o-ascend-competition/track1-inference-optimization"

python3 baseline/benchmark_text.py \
  --base-url "http://127.0.0.1:${SERVER_PORT}/v1" \
  --model "$MODEL_ID" \
  --requests 20 \
  --concurrency 1 \
  --output "$RUN_DIR/text-c1.json"

python3 baseline/benchmark_text.py \
  --base-url "http://127.0.0.1:${SERVER_PORT}/v1" \
  --model "$MODEL_ID" \
  --requests 40 \
  --concurrency 2 \
  --output "$RUN_DIR/text-c2.json"

python3 baseline/benchmark_text.py \
  --base-url "http://127.0.0.1:${SERVER_PORT}/v1" \
  --model "$MODEL_ID" \
  --requests 40 \
  --concurrency 4 \
  --output "$RUN_DIR/text-c4.json"
```

这些数据只用于早期工程对比，不替代官方 Benchmark。

### 9.4 检查官方 Benchmark CLI

先保存完整帮助：

```bash
vllm bench serve --omni --help=all > "$RUN_DIR/vllm-bench-help.txt" 2>&1
sed -n '1,260p' "$RUN_DIR/vllm-bench-help.txt"
```

当前上游可能提供以下 backend：

- `openai-chat-omni`
- `openai-audio-speech`
- `daily-omni`
- 其他当前版本注册的 backend

执行模型必须根据本机 `--help=all` 和 starter kit 生成最终命令，不允许从旧文档猜完整参数。

### 9.5 NPU 监控

在独立终端执行：

```bash
while true; do
  date -u +%Y-%m-%dT%H:%M:%SZ
  npu-smi info
  sleep 2
done | tee "$RUN_DIR/npu-monitor.txt"
```

Benchmark 结束后使用 `Ctrl+C` 停止。不要杀死服务端进程。

如果平台提供更细粒度的官方 profiler，先记录工具版本和命令帮助，再设计 profiling 轮次；profiling 数据不要和无 profiler 的性能数据混为一组。

### 9.6 稳定性测试

至少进行一轮 30 分钟持续请求，记录：

- 总请求数。
- 成功率和失败率。
- p50/p95/p99 延迟。
- NPU/主机内存是否持续增长。
- 是否出现音频损坏、空响应或阶段卡死。
- 是否发生服务重启。

### 9.7 Gate 3 基线报告

复制 `reports/baseline-template.md`，填写所有字段。任何 `TBD` 都必须说明为什么没有数据和计划何时补齐。

## 10. Gate 4：优化实验

### 10.1 实验目录

每项实验使用固定结构：

```text
experiments/NNN-short-name/
├── hypothesis.md
├── environment.txt
├── config-before.yaml
├── config-after.yaml
├── commands.md
├── run-1.json
├── run-2.json
├── run-3.json
├── correctness.md
└── conclusion.md
```

### 10.2 单项实验流程

1. 从 profile 或基线数据提出一个可证伪的瓶颈假设。
2. 复制原配置，不直接修改唯一基线文件。
3. 只改变一个主要变量。
4. 重启服务并完成相同预热。
5. 先跑正确性 smoke。
6. 使用完全相同的 Benchmark 参数运行三轮。
7. 对比中位数和尾延迟，不只看最好的一次。
8. 记录资源、失败率和效果变化。
9. 决定保留、回滚或继续研究。

### 10.3 优化优先级

优先级从高到低：

1. 正确性、崩溃、OOM 和复现问题。
2. deploy config 的三阶段设备与内存预算。
3. `max_num_seqs`、并发和调度参数。
4. 请求形状、batch 和阶段流水线重叠。
5. Thinker TTFT。
6. Talker/Code2Wav chunk 与 TTFP。
7. KV cache、图模式和平台适配。
8. 在效果可控后评估 W8A16。
9. 有明确 kernel 证据后才考虑 Ascend C/Triton 自定义算子。

### 10.4 第一批建议实验

#### 实验 001：默认配置基线

不修改任何配置，建立所有指标和稳定性基线。

#### 实验 002：Stage 内存预算

只有在 OOM、频繁换页或显存明显浪费时进行。基于实际 YAML 修改一个阶段预算，保持总预算和运行时 workspace 安全余量。

#### 实验 003：并发上限

固定输入和输出长度，分别测试 concurrency 1/2/4，寻找吞吐提升与 p95 恶化的拐点。

#### 实验 004：文本与语音路径拆分

分别测 text-only 和 text+audio，估算 Thinker 与 Talker/Code2Wav 对 E2E 的贡献。

#### 实验 005：chunk/流式策略

只有能够同时测 TTFP、chunk latency、音频正确性时才进行。防止通过增大 chunk 获得吞吐但损害首响体验。

### 10.5 暂时不要做的事情

- 没有基线就量化。
- 同时修改 batch、内存、chunk 和模型权重。
- 只看平均延迟，不看 p95/p99 和失败率。
- 直接替换来源不明的 W4A16 权重。
- 在没有 kernel profile 的情况下编写自定义算子。
- 只优化 text-only，却忽略比赛要求的全模态能力。

## 11. 上游 PR 计划

vLLM-Omni 竞赛 RFC 鼓励以下贡献：

- 可复现的 MiniCPM-o 4.5 Ascend serving 路径。
- Ascend deploy config。
- 兼容性修复。
- Benchmark 和复现工具。
- 带前后数据的性能优化。
- 文档。

PR 要求：

- 小而明确，一个 PR 解决一个问题。
- 保持现有 CUDA/GPU 行为。
- 写清硬件、镜像、CANN、驱动、代码和模型版本。
- 提供最小 smoke 或测试。
- 性能 PR 必须提供 before/after 和正确性结果。
- 不提交大日志、模型文件和无关格式化改动。

## 12. 最终提交包

必须准备：

- 可复现代码和配置。
- 环境与依赖版本。
- 一键启动脚本。
- 官方 Benchmark 执行脚本。
- 原始基线和优化结果。
- 正确性、效果和稳定性报告。
- 资源利用率记录。
- 已知限制和失败实验。
- README 与完整复现说明。
- Demo、PPT、演示视频和答辩稿。
- 上游 PR 链接和当前状态。

## 13. 交给执行模型的提示词模板

### 13.1 Gate 0 提示词

```text
你正在执行 MiniCPM-o 4.5 昇腾比赛项目的 Gate 0。
请完整阅读 docs/track1-execution-manual.md，只执行 Gate 0，不要启动模型服务。
先检查 910C、CANN、Python、torch、torch_npu、vLLM、vLLM-Ascend、vLLM-Omni、源码 commit 和 deploy config。
禁止安装或升级依赖，禁止删除文件。
把所有结果保存到一个带 UTC 时间的 reports/runs/<RUN_ID>/ 目录。
完成后报告：硬件、版本、源码位置、模型位置、缺失项、产生的文件，以及 Gate 0 是否通过。
```

### 13.2 Gate 1 提示词

```text
你正在执行 Gate 1。必须先确认 Gate 0 已通过。
使用镜像现有的 vLLM-Omni 和实际 minicpmo_4_5 deploy config，启动 text-only 可用的 OpenAI-compatible 服务。
先运行单次 smoke，再运行 20 次串行稳定性测试。
不要优化、不要量化、不要修改模型源码。
保存启动命令、deploy config、服务日志、请求 JSON、20 次结果和 Gate 1 结论。
出现 OOM、CANN/NPU 内部错误或版本不一致时立即停止并保留完整错误。
```

### 13.3 Gate 2 提示词

```text
你正在执行 Gate 2。必须先确认 Gate 1 的 20/20 text smoke 通过。
只使用当前 vLLM-Omni 源码中的官方 MiniCPM-o 4.5 示例，依次验证文本、文本+语音、图像、音频、视频。
每一步单独执行并保存请求、响应、服务日志和产物。
检查流式 WAV 是否非空、可解码，并记录声道、采样率、帧数和时长。
Daily-Omni 路径必须显式使用 enable_thinking=false。
不要开始任何性能优化。
```

### 13.4 Gate 3 提示词

```text
你正在执行 Gate 3。必须先确认全部必需模态通过 Gate 2。
先预热，再运行固定参数的 concurrency 1/2/4 基线，保存 TTFT、chunk、TTFP、E2E、吞吐、失败率和 NPU 监控。
运行前保存 vllm bench serve --omni --help=all，根据本机帮助和官方 starter kit 生成正式命令，不得猜参数。
同一轮测试不得修改配置或重启服务。完成至少一轮 30 分钟稳定性测试，并填写 reports/baseline-template.md。
```

### 13.5 单项优化提示词

```text
你正在执行一个单变量优化实验。
先阅读基线报告和 profile，写出可证伪的瓶颈假设。
创建 experiments/NNN-name/，保存修改前后配置和完整命令。
只改变一个主要变量；先通过正确性，再使用与基线相同的参数运行三轮。
比较中位数、p95、失败率、资源和效果，最后明确结论为保留、回滚或需要进一步研究。
不要仅凭一次最好成绩宣布提升。
```

## 14. 每日收尾检查

每天结束前确认：

- [ ] 当日代码和配置已经保存。
- [ ] 每次运行都有唯一 RUN_ID。
- [ ] 原始 JSON 和日志没有被覆盖。
- [ ] 环境、模型和源码版本可以追溯。
- [ ] 有效优化都有正确性结果。
- [ ] 失败实验也有记录。
- [ ] 没有凭据、Token 或个人信息进入仓库。
- [ ] 下一步只有一个明确 Gate 或实验。

## 15. 权威参考

- [比赛官方页面](https://ascend.openbmb.cn/competition)
- [vLLM-Omni 竞赛 RFC #5075](https://github.com/vllm-project/vllm-omni/issues/5075)
- [vLLM-Omni NPU 安装](https://docs.vllm.ai/projects/vllm-omni/en/latest/getting_started/installation/npu/)
- [MiniCPM-o 4.5 Online Serving](https://docs.vllm.ai/projects/vllm-omni/en/latest/user_guide/examples/online_serving/minicpmo/)
- [vLLM-Omni Benchmark CLI](https://github.com/vllm-project/vllm-omni/blob/main/docs/cli/bench/serve.md)
- [vLLM-Ascend 安装](https://docs.vllm.ai/projects/ascend/en/latest/installation.html)
- [MiniCPM-o 4.5 模型](https://huggingface.co/openbmb/MiniCPM-o-4_5)
