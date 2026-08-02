# 赛道二：见微 Guardian-O

> 全模态实验操作教练与安全伴随助手
>
> 独立项目：拥有自己的前端、后端、模型适配、测试、部署和提交材料，不依赖赛道一。

**当前阶段**：产品、架构和开发流程已经定义，应用源码尚未开始实现。第一个编码里程碑是可在普通电脑独立运行的 Mock Web MVP。

## 产品一句话

Guardian-O 持续观察实验操作并理解用户语音，在关键步骤主动提醒、接受用户随时打断，尤其识别可能导致实验失败的不规范操作，解释其对实验结果的影响，并在会话结束后生成可追溯的操作报告。

## 比赛 MVP

使用水、空容器、标签卡和护目镜等安全道具，完成一个可重复的实验室安全演练：

1. 用户展示任务卡并开始伴随会话。
2. 助手发现未佩戴护目镜并主动提醒。
3. 助手发现用户拿错标签容器并生成证据卡。
4. 助手发现用户跳过标签确认，并说明该不规范操作可能造成取样错误、污染或结果失真，导致本次演练失败。
5. 用户在助手说话时打断并追问原因。
6. 助手继续观察，确认用户纠正操作，结束后生成包含安全风险和实验结果影响的操作报告。

## 目录

```text
track2-guardian-o/
├── backend/       # 独立会话网关、事件策略和模型适配
├── frontend/      # 独立 Web UI、音视频采集和实时交互
├── docs/          # 产品、架构、流程、演示和提交文档
├── submissions/   # 赛道二独立提交材料
├── tests/         # 赛道二独立测试
├── CONTEXT.md
└── README.md
```

## 开发顺序

1. 用假后端完成 90 秒交互原型。
2. 固化事件协议、会话状态和报告格式。
3. 接入 MiniCPM-o 4.5 的半双工稳定路径。
4. 接入全双工、主动提醒和用户打断。
5. 在昇腾环境完成复现与降级验证。
6. 完成 PPT、项目说明、演示视频和提交包。

详细流程见 [`docs/development-process.md`](docs/development-process.md)。

在阶段 1 合并前，本目录没有安装或启动命令；协作者应从 `track2` Issue 模板领取 Mock Web MVP 任务，不要把规划文档描述成已实现功能。

## 首要文档

- [`docs/product-concept.md`](docs/product-concept.md)：产品定义和获奖逻辑
- [`docs/architecture.md`](docs/architecture.md)：独立技术架构和接口边界
- [`docs/development-process.md`](docs/development-process.md)：协同开发阶段与验收
- [`docs/demo-script.md`](docs/demo-script.md)：90 秒演示脚本
- [`docs/submission-checklist.md`](docs/submission-checklist.md)：最终材料清单
- [`docs/decision-map.md`](docs/decision-map.md)：尚未解决的关键决策

## 安全边界

Guardian-O 是教学、培训和标准化操作辅助工具，不替代专业实验室安全员，不提供安全认证，也不对真实危险操作作自动授权。比赛演示禁止使用真实危险材料。
