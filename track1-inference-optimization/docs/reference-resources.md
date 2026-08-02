# 可借鉴项目与资源汇总

> 来源：针对 8 个方向、200+ 次搜索的系统调研
> 更新：2026-08-01

---

## P0 级资源（必须立即获取和阅读）

### 1. 竞赛 Starter Kit
- **[RFC Issue #5075](https://github.com/vllm-project/vllm-omni/issues/5075)** — 竞赛官方 RFC，确认 vLLM-Omni 为指定代码库
- **[PR #4067: recipes/OpenBMB](https://github.com/vllm-project/vllm-omni/pull/4067)** — vLLM-Omni 仓库中 `recipes/OpenBMB/` 目录的原始 PR，竞赛 starter kit
- **[CompeteHub 竞赛页面](https://competehub.dev/zh/competitions/gitcode2074052190424199170)** — 官方赛程和规则

### 2. 环境与部署
- **[vLLM-Omni NPU 安装指南](https://docs.vllm.ai/projects/vllm-omni/en/stable/getting_started/installation/npu/)**
- **[vLLM-Omni Dockerfile.npu.a3](https://github.com/vllm-project/vllm-omni/blob/bb973cb1/docker/Dockerfile.npu.a3)** — 官方 A3 NPU 容器文件
- **[MiniCPM-o 4.5 在线服务示例](https://docs.vllm.ai/projects/vllm-omni/en/latest/user_guide/examples/online_serving/minicpmo/)** — 可直接使用的推理命令和参数

### 3. 模型权重
- **[FlagRelease/MiniCPM-o-4.5-ascend-FlagOS](https://huggingface.co/FlagRelease/MiniCPM-o-4.5-ascend-FlagOS)** — **已适配昇腾的官方模型权重！** 由众智 FlagOS 团队提供，发布即适配 6 芯
- **[88plug/MiniCPM-o-4.5-W4A16](https://huggingface.co/88plug/MiniCPM-o-4.5-W4A16)** — 社区 W4A16 量化版本

---

## P1 级资源（优化必备参考）

### FlagOS 跨芯片适配方案
- **[flagos-ai/vllm-plugin-FL](https://github.com/flagos-ai/vllm-plugin-FL)** — FlagOS 官方 vLLM 插件！针对 Ascend NPU 优化的自定义算子集合
- 关键文章：[业界首个！众智 FlagOS 实现 MiniCPM-o 4.5 发布即 6 芯适配](http://mp.weixin.qq.com/s?__biz=MzkzNTc0NTg2OA==&mid=2247487218&idx=1&sn=a2fa0574517f69a9fbc45d9620027e04)
- 量子位报道：[一次开发跨芯运行](https://www.qbitai.com/2026/02/377464.html)

### Qwen3-Omni 在 Ascend 上（同架构参考）
- **[Qwen3-Omni Ascend 教程](https://github.com/vllm-project/vllm-ascend/blob/8a1b1cec/docs/source/tutorials/models/Qwen3-Omni-30B-A3B-Thinking.md)** — 同架构全模态模型的部署方法，可直接复用
- **[Qwen3-Omni 性能优化实战](https://blog.csdn.net/Lumos_Lovegood/article/details/161293031)** — P99 延迟与 QPS 双提升的详细优化技巧
- **[PR #6828: Qwen3-Omni 量化 + Ascend 适配](https://github.com/vllm-project/vllm-ascend/pull/6828)** — 量化方案可直接适用于 MiniCPM-o

### 量化方案
- **[W8A16 支持 Commit (5018f2d)](https://github.com/vllm-project/vllm-ascend/commit/5018f2d8fd6dc11240900e38049150619895570d)** — Ascend 上 W8A16 的实现
- **[Issue #524: W8A16/W4A16 量化跟踪](https://github.com/vllm-project/vllm-ascend/issues/524)** — 量化支持路线图
- **[vLLM-Omni 在线量化文档](https://docs.vllm.com.cn/projects/vllm-omni/en/latest/user_guide/quantization/online/)** — 无需离线量化的推理加速

### MiniCPM-o 4.5 在 vLLM-Omni 中的实现代码
- **[PR #3337: MiniCPM-o-4_5 新增支持](https://github.com/vllm-project/vllm-omni/pull/3337)**
- **[PR #3907: 全双工实时运行时 + Demo](https://github.com/vllm-project/vllm-omni/pull/3907)**
- **[Commit 6b20e82: 更新 Benchmark](https://github.com/vllm-project/vllm-omni/commit/6b20e8237f2fb1bb083c26d1e9fa982f1766a441)**

---

## 性能优化系统性指南

### 昇腾推理调优
| 资源 | 说明 |
|---|---|
| **[veRL Ascend 调优指南](https://verl.readthedocs.io/en/latest/ascend_tutorial/dev_guide/performance/perf_tuning_on_ascend.html)** | 涵盖图融合、内存管理、NPU 特性开关、算子选择、profiling |
| **[昇腾 vLLM 部署与优化实战](https://ai6s.net/697377e57c1d88441d8f127a.html)** | 高吞吐推理落地指南 |
| **[vLLM Ascend 推理加速技术](https://developer.baidu.com/article/detail.html?id=6892764)** | 百度开发者文章，覆盖完整加速链路 |

### CANN 级优化
| 资源 | 说明 |
|---|---|
| **[ATB 完整指南](https://blog.csdn.net/czhm57/article/details/161839492)** | Ascend Transformer Boost，CANN 级推理加速 |
| **[FlashAttention on NPU](https://hwcomputing.csdn.net/6a0ebe7f10ee7a33f274223f.html)** | CANN 上 FlashAttention 实现与调优 |
| **[flash-attn-npu PyPI](https://pypi.org/project/flash-attn-npu/)** | 昇腾优化版 FlashAttention 包 |

### 前沿论文（竞赛加分项）
| 论文 | 核心思想 |
|---|---|
| **[FlexNPU (arXiv:2606.04415)](https://scirate.com/arxiv/2606.04415)** | NPU 虚拟化，预填充-解码协同调度，提升 NPU 利用率 |
| **[CloudMatrix384 (arXiv:2506.12708)](https://arxiv.org/abs/2506.12708v2)** | 华为超节点上大模型服务的系统架构，含性能数据 |
| **Ascend 局限性 (arXiv:2607.08215)** | 非 GPU 加速器的 MoE/多模态服务局限，知己知彼 |

### 预填充-解码分离
- **[vLLM-Ascend 预填充-解码分离](https://github.com/vllm-project/vllm-ascend/blob/b46ad6e1/docs/source/user_guide/feature_guide/large_scale_ep.md)**
- **[Qwen3-Omni 多模态性能优化 (P99/QPS)](https://blog.csdn.net/Lumos_Lovegood/article/details/161293031)** — 同架构模型的实战优化！

---

## 部署教程与中文社区

| 资源 | 链接 |
|---|---|
| vLLM-Omni 昇腾极速落地指南 | [CSDN](https://hwcomputing.csdn.net/6a2ca79d662f9a54cb7dec64.html) |
| vLLM Ascend 迁移实操 | [天翼云](https://www.ctyun.cn/developer/article/805299591970885) |
| MiniCPM-o 4.5 轻量化部署 | [百度开发者](https://developer.baidu.com/article/detail.html?id=7445032) |
| ROLL（阿里巴巴 Ascend LLM 库） | [文档](https://alibaba.github.io/ROLL/zh-Hans/docs/User%20Guides/Hardware%20Support/ascend_docker_usage/) |
| MindIE/MindFormers 对比 | [知乎](https://zhuanlan.zhihu.com/p/692377206) |

---

## vLLM-Omni 官方 Architecture 参考

| PR | 内容 |
|---|---|
| **[PR #3907](https://github.com/vllm-project/vllm-omni/pull/3907)** | 全双工实时运行时 + MiniCPM-o 4.5 Demo |
| **[PR #4067](https://github.com/vllm-project/vllm-omni/pull/4067)** | Competition recipes/OpenBMB/ |
| **[PR #3337](https://github.com/vllm-project/vllm-omni/pull/3337)** | MiniCPM-o 4.5 模型实现 |
| **[PR #4490](https://github.com/vllm-project/vllm-omni/pull/4490)** | Speech SSE stream_format |
| **[Issue #2223](https://github.com/vllm-project/vllm-omni/issues/2223)** | NPU 2026 Q2 Roadmap |

---

## vLLM-Ascend 关键 PR

| PR | 内容 |
|---|---|
| **[#6828](https://github.com/vllm-project/vllm-ascend/pull/6828)** | Qwen3-Omni 量化 + Ascend 适配 |
| **[#5718](https://github.com/vllm-project/vllm-ascend/pull/5718)** | MoE W8A8 动态量化 |
| **[#5456](https://github.com/vllm-project/vllm-ascend/pull/5456)** | MLA 预填充性能优化 |
| **[Commit 5018f2d](https://github.com/vllm-project/vllm-ascend/commit/5018f2d8fd6dc11240900e38049150619895570d)** | W8A16 量化支持 |

---

## 快速起手路线图

基于以上资源，推荐的执行顺序：

### 第一步：环境搭建
```bash
# 拉取官方 A3 镜像
docker pull quay.io/ascend/vllm-omni:v0.25.0-a3

# 参考 Dockerfile.npu.a3 了解依赖
# https://github.com/vllm-project/vllm-omni/blob/bb973cb1/docker/Dockerfile.npu.a3
```

### 第二步：获取模型
```bash
# 官方昇腾适配权重（推荐）
git lfs install
git clone https://huggingface.co/FlagRelease/MiniCPM-o-4.5-ascend-FlagOS

# 或者原始 HuggingFace 权重
git clone https://huggingface.co/openbmb/MiniCPM-o-4_5
```

### 第三步：启动基线推理
```bash
# 参考官方示例命令
# https://docs.vllm.ai/projects/vllm-omni/en/latest/user_guide/examples/online_serving/minicpmo/

vllm serve FlagRelease/MiniCPM-o-4.5-ascend-FlagOS \
  --host 0.0.0.0 \
  --port 8000 \
  --dtype bfloat16
```

### 第四步：跑 Benchmark
- 从 `recipes/OpenBMB/` 目录获取竞赛 benchmark 脚本
- 运行 Daily-Omni / TTS-Seed / Video-MME 建立基线

### 第五步：逐步优化
1. 启用在线量化（W8A16） → 内存和吞吐改善
2. 调整 batch/调度参数 → 最大化 NPU 利用率
3. 参考 Qwen3-Omni 优化方案 → 算子融合、流水线调优
4. 使用 FlagOS vllm-plugin-FL → 自定义算子集合
5. 参考 ATB → CANN 级 Transformer 加速

---

*调研来自 8 个方向共 200+ 次搜索，资源已按优先级 P0/P1/P2 分级*
