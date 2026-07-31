# MiniCPM-o 4.5 昇腾推理优化挑战赛

> 赛道一 · 子赛道 B（vLLM-Omni）
>
> 私有仓库 · 竞赛调研与方案

## 目录结构

```
├── docs/
│   ├── competition-research.md    # 竞赛全面调研报告（两赛道对比+最终选择）
│   └── reference-resources.md     # 可借鉴项目与资源汇总（8方向200+搜索）
├── baseline/                     # 基线部署与 Benchmark 脚本
├── optimization/                 # 优化方案与代码
├── demo/                         # Demo 对接
├── reports/                      # 性能测试报告
├── submissions/                  # 最终提交材料
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
| 参考同类优化 | [Qwen3-Omni Ascend 优化实战](https://blog.csdn.net/Lumos_Lovegood/article/details/161293031) |

## 状态

- [x] 赛道调研（见 `docs/competition-research.md`）
- [x] 资源调研（见 `docs/reference-resources.md`）
- [ ] HiDevLab 算力申请
- [ ] Docker 环境部署
- [ ] 基线模型运行
- [ ] Benchmark 评测（Daily-Omni / TTS-Seed / Video-MME）
- [ ] Demo 对接
- [ ] 性能优化
- [ ] PR 提交至 minicpm-challenge 分支
- [ ] 最终材料打包

---

*2026 OpenBMB 昇腾推理优化与应用创新挑战赛*
