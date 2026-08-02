# Optimization Experiments

每个优化建立独立目录，例如 `optimization/001-stage-memory-budget/`，至少包含：

- `hypothesis.md`：瓶颈证据、修改理由和预期影响。
- `changes.patch` 或代码引用：准确记录改动。
- `commands.md`：完整复现命令。
- `results.json`：原始机器可读结果。
- `conclusion.md`：正确性、性能、稳定性和是否保留。

禁止只记录“提升约 X%”而不保留基线、运行次数和原始数据。
