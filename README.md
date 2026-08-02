# MiniCPM-o 4.5 × 昇腾竞赛工作区

本仓库同时保存两个赛道的工作，但它们是两个**独立项目**。两者不共享源码、运行时、依赖、测试、部署脚本或提交包，也不存在调用关系。

## 项目入口

| 项目 | 目录 | 独立目标 | 当前状态 |
|---|---|---|---|
| 赛道一：高性能推理优化 | [`track1-inference-optimization/`](track1-inference-optimization/) | 在昇腾 NPU 上优化 MiniCPM-o 4.5 的推理性能与复现质量 | 基线工程已建立，等待 HiDevLab 算力 |
| 赛道二：创新应用 | [`track2-guardian-o/`](track2-guardian-o/) | 独立开发“见微 Guardian-O”全模态实验操作教练 | 产品定义完成，等待 Web MVP |

## 强制边界

- 每个项目实现后必须能在自己的目录内独立安装、运行、测试和打包；尚未进入编码阶段的项目必须明确标注状态。
- 禁止从一个项目导入另一个项目的 Python、JavaScript、配置或脚本。
- 禁止建立仓库级共享 `src/`、共享依赖锁文件或共享提交目录。
- 一个功能 PR 默认只能修改一个项目；必须修改根目录治理文件时，需要在 PR 中解释原因。
- 赛道一和赛道二分别提交，任何一方失败都不能阻塞另一方运行。

边界定义见 [`CONTEXT-MAP.md`](CONTEXT-MAP.md)，决策原因见 [`docs/adr/0001-independent-track-projects.md`](docs/adr/0001-independent-track-projects.md)。

## 协作入口

1. 先阅读 [`docs/competition-rules.md`](docs/competition-rules.md)，确认任务属于哪个赛道。
2. 再阅读对应项目的 `README.md` 和 `CONTEXT.md`。
3. 按 [`CONTRIBUTING.md`](CONTRIBUTING.md) 创建 Issue、分支、测试和 PR。
4. 一个 PR 只解决一个清晰问题，并附运行证据。

## 仓库结构

```text
.
├── CONTEXT-MAP.md
├── CONTRIBUTING.md
├── docs/
│   ├── competition-rules.md
│   └── adr/
├── track1-inference-optimization/
│   ├── baseline/
│   ├── docs/
│   ├── optimization/
│   ├── reports/
│   ├── submissions/
│   └── tests/
└── track2-guardian-o/
    ├── backend/
    ├── frontend/
    ├── docs/
    ├── submissions/
    └── tests/
```

## 规则状态提醒

本仓库的规则摘要用于团队执行，不替代主办方公告。正式硬件、镜像、评分脚本、提交格式，以及同一参赛者能否同时参加两个赛道，均以官方最新公告、starter kit 和官方群书面答复为准。
