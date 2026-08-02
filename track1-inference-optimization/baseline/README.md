# Baseline

本目录用于建立可复现的 MiniCPM-o 4.5 / vLLM-Omni 昇腾基线。所有优化都必须与同一环境、同一模型 revision、同一数据和同一命令下的基线比较。

## 1. 记录环境

```bash
bash baseline/run_gate0.sh
```

本地没有昇腾设备时可以用下面的命令做脚本演练；HiDevLab 正式运行不要关闭 NPU、源码和配置检查：

```bash
REQUIRE_NPU=0 REQUIRE_SOURCE=0 bash baseline/run_gate0.sh
```

## 2. 启动服务

在 vLLM-Omni 源码根目录或已正确安装 deploy config 的环境中执行：

```bash
bash /path/to/competition-repo/track1-inference-optimization/baseline/serve.sh
```

可通过环境变量覆盖模型和配置，也可以把其他 CLI 参数直接追加到命令末尾：

```bash
MODEL=/models/MiniCPM-o-4_5 \
DEPLOY_CONFIG=vllm_omni/deploy/minicpmo_4_5.yaml \
bash baseline/serve.sh --disable-log-requests
```

## 3. 正确性冒烟测试

```bash
python3 baseline/smoke_test.py
```

这一步只验证 text-only 路径，不代表语音、多模态或比赛效果校验已经通过。

服务已经启动时，可以一条命令完成“等待服务、单次 smoke、20 次稳定性测试”：

```bash
bash baseline/run_gate1.sh
```

也可以覆盖 API 地址和模型：

```bash
BASE_URL=http://127.0.0.1:8099/v1 \
MODEL=openbmb/MiniCPM-o-4_5 \
bash baseline/run_gate1.sh
```

## 4. 文本流式延迟基线

```bash
mkdir -p reports/runs
python3 baseline/benchmark_text.py \
  --requests 20 \
  --concurrency 1 \
  --output reports/runs/text-c1.json

python3 baseline/benchmark_text.py \
  --requests 40 \
  --concurrency 4 \
  --output reports/runs/text-c4.json
```

脚本记录首个文本 delta 的 TTFT、请求 E2E 和请求吞吐。正式比赛的 chunk latency、音频 TTFP、Daily-Omni、TTS-Seed、Video-MME 必须使用 starter kit 的最终口径补齐。

## 基线纪律

- 每次运行保存环境、启动命令、模型 revision 和原始 JSON。
- 每项优化至少重复三轮，并保留失败结果。
- 正确性或稳定性下降的结果不得作为有效优化。
- 官方评分脚本发布后，以官方指标为准，本目录脚本只作为早期工程基线。
