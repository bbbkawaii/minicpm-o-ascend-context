# 赛道一：MiniCPM-o 4.5 昇腾推理优化

> 赛道一 · 子赛道 B（vLLM-Omni）
>
> 独立项目：不依赖赛道二的源码、服务、配置、测试或提交材料。

## 目录结构

```
├── docs/
│   ├── competition-research.md    # 竞赛全面调研报告（两赛道对比+最终选择）
│   ├── reference-resources.md     # 可借鉴项目与资源汇总（8方向200+搜索）
│   ├── execution-plan.md          # 赛道一分阶段执行与质量门禁
│   └── track1-execution-manual.md # 可交给执行模型逐步实施的详细施工手册
├── baseline/                      # 环境检查、服务启动与早期 Benchmark
│   ├── run_gate0.sh               # Gate 0 环境与版本采集
│   ├── run_gate1.sh               # Gate 1 smoke + 稳定性编排
│   └── benchmark_text.py          # 流式 TTFT/E2E Benchmark
├── optimization/                  # 可复现优化实验
├── demo/                         # Demo 对接
├── reports/                       # 性能测试报告和模板
├── submissions/                  # 最终提交材料
├── tests/                         # 本地工具测试
└── README.md
```

## 快速链接

| 资源 | 地址 |
|---|---|
| vLLM-Omni 仓库 | https://github.com/vllm-project/vllm-omni |
| vLLM-Ascend 插件 | https://github.com/vllm-project/vllm-ascend |
| 竞赛 RFC | https://github.com/vllm-project/vllm-omni/issues/5075 |
| Starter Kit | `recipes/OpenBMB/` in vLLM-Omni |
| MiniCPM-o 4.5 模型 | https://huggingface.co/openbmb/MiniCPM-o-4_5 |
| 昇腾适配权重 | https://huggingface.co/FlagRelease/MiniCPM-o-4.5-ascend-FlagOS |
| W4A16 量化版 | https://huggingface.co/88plug/MiniCPM-o-4.5-W4A16 |
| vLLM-Omni 中文文档 | https://docs.vllm.com.cn/projects/vllm-omni/en/latest/ |
| Docker 镜像 | `quay.io/ascend/vllm-omni:v0.25.0-a3` |
| FlagOS vLLM 插件 | https://github.com/flagos-ai/vllm-plugin-FL |

## 关键资源速查

| 想做什么 | 看什么 |
|---|---|
| 搭环境 | [vLLM-Omni NPU 安装指南](https://docs.vllm.ai/projects/vllm-omni/en/stable/getting_started/installation/npu/) + Dockerfile.npu.a3 |
| 启动推理 | [MiniCPM-o 4.5 在线服务示例](https://docs.vllm.ai/projects/vllm-omni/en/latest/user_guide/examples/online_serving/minicpmo/) |
| 跑 Benchmark | `recipes/OpenBMB/` 目录 |
| 做量化 | W8A16 [Commit 5018f2d](https://github.com/vllm-project/vllm-ascend/commit/5018f2d8fd6dc11240900e38049150619895570d) + [在线量化文档](https://docs.vllm.com.cn/projects/vllm-omni/en/latest/user_guide/quantization/online/) |
| 做优化 | [veRL Ascend 调优指南](https://verl.readthedocs.io/en/latest/ascend_tutorial/dev_guide/performance/perf_tuning_on_ascend.html) + FlexNPU 论文 |
| 执行后续优化 | [低成本模型优化实现方案](docs/low-cost-model-optimization-plan.md) |
| 参考同类优化 | [Qwen3-Omni Ascend 优化实战](https://blog.csdn.net/Lumos_Lovegood/article/details/161293031) |

## 开始执行

先完整阅读 [`docs/track1-execution-manual.md`](docs/track1-execution-manual.md)。执行模型每次只能完成其中一个 Gate，并在通过验收后才能进入下一阶段。

本地工具检查：

```bash
cd track1-inference-optimization
python3 -m unittest discover -s tests -v
bash -n baseline/*.sh
```

HiDevLab 中从 Gate 0 开始：

```bash
cd track1-inference-optimization
bash baseline/run_gate0.sh
```

## 独立性约束

- 所有赛道一依赖、脚本、报告和提交材料必须位于本目录。
- 不得导入或调用 `../track2-guardian-o/` 中的任何内容。
- 性能结果必须由本项目自己的启动命令和 Benchmark 复现。
- 上游贡献应直接提交到 vLLM-Omni 等公开项目，不通过赛道二间接共享。

## 状态

- [x] 赛道调研（见 `docs/competition-research.md`）
- [x] 资源调研（见 `docs/reference-resources.md`）
- [x] 基线工程骨架（环境检查、服务启动、text smoke、早期 TTFT/E2E）
- [x] HiDevLab 算力申请
- [x] Docker 环境部署
- [x] 基线模型运行
- [x] 910C 双卡文本与语音早期基线
- [ ] Benchmark 评测（Daily-Omni / TTS-Seed / Video-MME）
- [ ] Demo 对接
- [ ] 性能优化
- [ ] PR 提交至 minicpm-challenge 分支
- [ ] 最终材料打包

---

*2026 OpenBMB 昇腾推理优化与应用创新挑战赛*
