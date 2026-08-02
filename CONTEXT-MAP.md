# Context Map

## Contexts

- [赛道一：推理优化](./track1-inference-optimization/CONTEXT.md) — 独立负责 MiniCPM-o 4.5 在昇腾 NPU 上的性能、正确性、稳定性和复现。
- [赛道二：Guardian-O](./track2-guardian-o/CONTEXT.md) — 独立负责全模态实验操作教练的用户体验、应用逻辑、演示和应用提交材料。

## Relationships

- **赛道一 ↮ 赛道二**：没有源码、API、运行时、部署、测试或提交依赖。
- 两个项目可以分别采用 MiniCPM-o 4.5 和昇腾环境，但必须各自维护适配代码与运行说明。
- 根目录只保存赛事规则和协作治理信息，不保存可运行的共享业务代码。
