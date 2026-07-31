# MiniCPM-o 4.5 昇腾推理优化挑战赛 — 赛道调研报告

> **比赛**：OpenBMB 昇腾推理优化与应用创新挑战赛 — 赛道一（高性能推理优化赛道）
> **仓库**：`airbate/minicpm-o-ascend-competition`（私有）
> **状态**：调研阶段，已选择子赛道 B（vLLM-Omni）

---

## 一、比赛概览

### 基本信息

| 项 | 值 |
|---|---|
| **主办方** | OpenBMB |
| **模型** | MiniCPM-o 4.5（全模态，~9B 参数，基于 Qwen2.5） |
| **硬件** | 华为昇腾 910C 单卡 |
| **评测 Benchmark** | Daily-Omni、TTS-Seed、Video-MME |
| **精度门槛** | 优化后精度降幅 ≤ 2 个百分点（相对各自框架官方基线） |
| **Demo 门槛** | 必须接入官方 Demo 并稳定运行 |
| **联系方式** | contact@openbmb.cn |

### 两个子赛道

| | 子赛道 A | 子赛道 B |
|---|---|---|
| **框架** | llama.cpp-omni | vLLM-Omni |
| **镜像** | CANN 9.1.0-beta1 | vllm-omni:v0.25.0 (quay.io/ascend/vllm-omni:v0.25.0-a3) |
| **核心指标** | RTF | RTF + TTFT + TTFP |
| **Demo 仓库** | [OpenBMB/MiniCPM-o-Demo](https://github.com/OpenBMB/MiniCPM-o-Demo) | 官方文档获取 |
| **加分机制** | 无 | PR 合入 minicpm-challenge 分支可获得加分 |
| **编程语言** | C/C++ | Python |
| **硬件** | 单卡 910C | 单卡 910C |

---

## 二、指标定义

### RTF（Real-Time Factor）
**公式**：`RTF = 音频 chunk 生成耗时 ÷ 音频 chunk 时长`

- RTF < 1.0：快于实时（可流式）
- RTF = 1.0：恰好实时
- RTF > 1.0：慢于实时（会有延迟）
- vLLM-Omni 按 Stage 分阶段追踪 RTF，端到端 RTF 最重要

### TTFT（Time to First Token）
从请求到达到第一个有效 token 生成的时间。

**组成**：
- 输入编码时间（tokenization + embedding）
- 模型前向传播（Prefill 阶段）
- 调度延迟（排队）

### TTFP（Time to First Packet）
从请求到达到第一个可消费音频包的时间。

- TTFP ≥ TTFT（多了 TTS 后端延迟）
- 包含语义→声学→声码器转换的全链路延迟

---

## 三、MiniCPM-o 4.5 模型分析

### 模型架构
```
输入模态                        输出模态
┌─ 文本 ────────────────────────► 文本
├─ 图像（SigLIP-400M-SO）──────► 
├─ 视频（SigLIP-400M-SO）──────► 
├─ 音频输入（Whisper 语音编码器）► 
                                 ┌► 语音（语义标记符 → CosyVoice2 TTS → 声码器）
```

**核心组件**：
| 组件 | 描述 |
|---|---|
| LLM 骨干 | Qwen2.5 架构 ~9B Transformer Decoder |
| 视觉编码器 | SigLIP-400M-SO（支持高分辨率图和视频） |
| 语音编码器 | Whisper-based AudioEncoder |
| 语音解码器 | CosyVoice2 声学标记符（AR + NAR） + token2wav 声码器 |
| 全双工 | 支持同时听、说，支持用户随时打断（barge-in） |

### 模型格式

| 格式 | 用途 |
|---|---|
| SafeTensors | HuggingFace 官方格式，vLLM-Omni 直接加载 |
| GGUF | llama.cpp-omni 量化格式 |
| W4A16/W8A16 | 社区量化版本 |

### 显存需求

| 精度 | 估计 VRAM |
|---|---|
| FP16 | ~18-20 GB |
| INT8 | ~10-12 GB |
| INT4 | ~6-8 GB |

### 流式语音生成流程

```
LLM 自回归生成语义标记符（AR）
  → CosyVoice2 将语义标记符转为声学标记符（NAR）
    → token2wav 声码器流式转音频波形
```

vLLM-Omni 通过异步 Stage 架构实现流水线并行：LLM 生成后续语义标记符的同时，早期 token 已经在跑 TTS 和声码器。

---

## 四、两个子赛道深度对比

### 4.1 llama.cpp-omni（子赛道 A）

**仓库**：[tc-mb/llama.cpp-omni](https://github.com/tc-mb/llama.cpp-omni)

| 维度 | 评价 |
|---|---|
| **维护模式** | 单人 fork（tc-mb），基于上游 llama.cpp |
| **编程语言** | C/C++（ggml 底层） |
| **架构** | llama.cpp + ggml 后端 + libmtmd（多模态输入）+ OMTD（输出多模态） |
| **CANN 后端** | 上游 ggml-cann 后端存在但缺陷多（有 ggml_cann_rms_norm 崩溃的已知 bug） |
| **音频输出** | 仍处于规划阶段，上游 Issue #21956："(Planning) Support audio output in mtmd" |
| **OMTD 库** | PR #24852 刚提交，极早期 |
| **文档** | 几乎无文档，靠读源码 |
| **Ascend 先例** | 无将 nn.cpp-omni 部署到 Ascend 的已知案例 |

**风险**：
- 需自行整合 CANN 后端与多模态代码，工作量大
- C/C++ 代码 AI 辅助效率低
- 社区支持几乎为零

### 4.2 vLLM-Omni（子赛道 B）✅ 已选

**仓库**：[vllm-project/vllm-omni](https://github.com/vllm-project/vllm-omni)

| 维度 | 评价 |
|---|---|
| **维护模式** | vLLM 官方组织维护，多机构联合（UC Berkeley、Red Hat、华为） |
| **编程语言** | Python（vLLM 生态） |
| **架构** | Stage 抽象 + 全分离式服务（Encoder/Prefill/Decode/Generator 可独立伸缩） |
| **Ascend 支持** | 官方一等公民支持！有 Dockerfile.npu / Dockerfile.npu.a3、CI 管线 |
| **镜像** | `quay.io/ascend/vllm-omni:v0.25.0-a3` |
| **MiniCPM-o 4.5** | 官方支持，有 examples、benchmark、commit 专门更新 |
| **文档** | 中英文齐全，docs.vllm.ai / docs.vllm.com.cn |
| **vllm-ascend 插件** | 独立维护的 Ascend 后端插件包 |
| **NPU Roadmap** | [Issue #2223](https://github.com/vllm-project/vllm-omni/issues/2223): vLLM-Omni NPU 2026 Q2 Roadmap |

**关键代码结构**：
```
vllm_omni/
  model_executor/models/minicpmo_4_5/     # MiniCPM-o 4.5
  model_executor/models/qwen3_omni/       # Qwen3-Omni（Thinker + Talker MoE）
  model_executor/stage_input_processors/  # 每 Stage 输入处理
  entrypoints/openai/                     # OpenAI 兼容 API
  platforms/                              # NPU/XPU/ROCm 平台抽象
  deploy/                                 # 部署 YAML 配置
  diffusion/                              # 扩散模型支持
docker/Dockerfile.npu                     # NPU Dockerfile
docker/Dockerfile.npu.a3                  # A3 专用 NPU Dockerfile
```

### 4.3 选择结论

**选择 vLLM-Omni（子赛道 B）**，理由：

1. **官方 Ascend NPU 支持**（Docker 镜像 + 文档 + CI），开箱即用
2. **Python 技术栈**，AI 辅助编程效率远高于 C/C++
3. **MiniCPM-o 4.5 已有官方示例和 benchmark**
4. **三个指标**（RTF + TTFT + TTFP）多维度优化，得分点更多
5. **PR 合入加分**
6. **社区活跃**（vllm-ascend 有 600-800 stars，活跃 PR；Red Hat 深度投入）

---

## 五、昇腾 910C 硬件与 CANN 软件栈

### 硬件规格

| 规格 | 值 |
|---|---|
| **内存** | ~64 GB HBM2e（部分变体 128 GB） |
| **内存带宽** | ~3.2 TB/s（卡间），~400 GB/s（HBM） |
| **FP16 算力** | ~800 TFLOPS（稠密） |
| **INT8 算力** | ~400 TOPS |
| **互联** | HCCS（华为缓存一致性系统）、PCIe Gen5 |
| **超级节点** | CloudMatrix 384（384 卡统一结构） |
| **性能标杆** | DeepSeek 推理达 NVIDIA H100 约 60% 性能（2025.02 测试） |

### CANN 软件栈

```
应用层：torch_npu / MindSpore / ONNX Runtime
  ↓
框架适配层：ATC（图编译器）、GE（图引擎）、AscendCL（运行时）
  ↓
算子层：Ascend C（原生算子语言）、ACLNN/ACLBLS（算子库）
  ↓
驱动层：Driver + 固件 + Ascend NPU
```

**torch_npu 工作原理**：
- 通过 PyTorch Plugin（PrivateUse1 调度键）注册 Ascend NPU 为 PyTorch 设备
- OpPlugin 机制将 PyTorch ATen 算子映射到 CANN 算子
- 使用方式：`model.npu()`、`tensor.npu()`、`torch_npu.npu.set_device(0)`

### Ascend NPU 上部署的主要挑战

（来源：arXiv 2607.08215 "On the Limitations of Non-GPU AI Accelerators for Large-Model Inference"）

1. **算子兼容性差距**：缺少 CUDA 融合算子和自定义算子（MoE 融合门控、Attention 变体）
2. **多模态编码器问题**：SigLIP/Whisper 依赖 CUDA 特定的融合 Attention
3. **内存碎片化**：与 cuBLAS/cuDNN 的内存分配模式不同
4. **张量布局不匹配**：TND vs NCHW/NHWC
5. **多模态流水线复杂性**：多 Stage 协调中的设备间通信开销
6. **软件成熟度差**：CANN/torch_npu 的稳定性、文档、调试工具远不如 CUDA
7. **社区碎片化**：MindSpore/torch_npu/TensorFlow 三路分叉

---

## 六、优化方向概览

### LLM 推理通用优化

| 优化方向 | 预期收益 | 难度 |
|---|---|---|
| 模型量化（W8A16/W4A16） | 内存减半，吞吐 1.5-2x | 中 |
| 算子融合（Attention + Norm + Residual） | 减少 kernel launch 开销 | 高（需 Ascend C） |
| KV Cache 优化（PagedAttention/Prefix Caching） | 内存和延迟改善 | 中 |
| Continuous Batching | 吞吐提升 | 低-中 |
| FlashAttention 适配 | Prefill 阶段加速 | 中-高 |
| 推测解码 | Token 生成加速 | 高 |

### 语音生成专项优化

| 优化方向 | 预期收益 | 对哪个指标 |
|---|---|---|
| AR + NAR TTS 并行流水线 | 降 TTFP | TTFP |
| 流式 token2wav 声码器 | 降 TTFP | TTFP |
| 分块 TTS（不等完整输出） | 降 TTFT/TTFP | TTFT, TTFP |
| 异步 Stage 流水线 | 降端到端 RTF | RTF |
| Sleep Mode / ACK Protocol | 降空闲功耗 | RTF |

### 按难度分级（AI 可操作度）

| 难度 | 方向 | AI 成功率 |
|---|---|---|
| 🟢 低 | 量化配置调优、batch size/调度参数调优、KV cache 参数 | 高 |
| 🟡 中 | PagedAttention 适配、异步流水线配置、torch_npu 调优 | 中 |
| 🔴 高 | Ascend C 自定义算子、FlashAttention 适配 | 低 |

---

## 七、关键资源

### 代码仓库

| 名称 | 地址 |
|---|---|
| vLLM-Omni | https://github.com/vllm-project/vllm-omni |
| vLLM-Ascend | https://github.com/vllm-project/vllm-ascend |
| llama.cpp-omni | https://github.com/tc-mb/llama.cpp-omni |
| MiniCPM-o Demo | https://github.com/OpenBMB/MiniCPM-o-Demo |

### 文档

| 名称 | 地址 |
|---|---|
| vLLM-Omni 英文文档 | https://docs.vllm.ai/projects/vllm-omni/en/stable/ |
| vLLM-Omni 中文文档 | https://docs.vllm.com.cn/projects/vllm-omni/en/latest/ |
| vLLM-Omni NPU 安装 | https://docs.vllm.ai/projects/vllm-omni/en/stable/getting_started/installation/npu/ |
| MiniCPM-o 4.5 模型详解 | https://openbmb.github.io/MiniCPM-o-Demo/site/zh/model.html |

### 论文

| 论文 | 链接 |
|---|---|
| vLLM-Omni 论文 | https://arxiv.org/abs/2602.02204 |
| MiniCPM-o 4.5 技术报告 | https://arxiv.org/abs/2604.27393 |
| Ascend 大模型服务 | https://arxiv.org/abs/2506.12708 |
| Ascend 局限性研究 | https://arxiv.org/abs/2607.08215 |

### Docker 镜像

| 镜像 | 地址 |
|---|---|
| A3 官方镜像 | `quay.io/ascend/vllm-omni:v0.25.0-a3` |
| Docker Hub 镜像 | `ascendai/vllm-omni:v0.25.0-a3` |

### 竞赛相关

| 资源 | 地址 |
|---|---|
| vLLM-Omni 竞赛 RFC | https://github.com/vllm-project/vllm-omni/issues/5075 |
| MiniCPM-o 4.5 HuggingFace | https://huggingface.co/openbmb/MiniCPM-o-4_5 |
| FlagOS Ascend 适配 | https://huggingface.co/FlagRelease/MiniCPM-o-4.5-ascend-FlagOS |
| Datawhale ROCm 部署指南 | https://datawhalechina.github.io/hello-rocm/01-deploy/minicpm-o/ |

---

## 八、下一步计划

1. HiDevLab 平台注册 + 申请 910C 算力
2. 拉取 Docker 镜像 + 环境部署测试
3. 运行 MiniCPM-o 4.5 基线示例
4. 配置并运行三点 Benchmark（Daily-Omni / TTS-Seed / Video-MME）
5. 对接官方 Demo
6. 建立基线性能数据（RTF/TTFT/TTFP）
7. 逐方向优化（见第六章）
8. 提交 PR 获取加分

---

*最后更新：2026-08-01*
