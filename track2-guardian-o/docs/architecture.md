# Guardian-O 独立技术架构

## 1. 边界

本项目拥有自己的模型服务适配层。它可以连接官方或兼容的 MiniCPM-o 4.5 服务，但不得调用、导入或读取赛道一项目中的代码、配置、结果或进程。

## 2. 组件

```text
Browser
  ├─ camera / microphone capture
  ├─ streaming playback and barge-in
  └─ live video, transcript, evidence timeline, report
        │
        ▼
Guardian-O Gateway
  ├─ session lifecycle
  ├─ realtime transport
  ├─ event policy and deduplication
  ├─ latency telemetry
  └─ report generation
        │
        ▼
Track-2 Inference Adapter
  ├─ mock mode
  ├─ stable segmented mode
  └─ full-duplex realtime mode
        │
        ▼
MiniCPM-o 4.5 service on the declared Ascend environment
```

## 3. 三种运行模式

### Mock

不需要模型和 NPU，用确定性脚本产生事件、文本和音频占位。用于前端、产品流程、自动测试和无算力协作。

### Stable

周期性提交视频帧或短视频段，并按段处理用户语音。它必须完整支持任务、提醒、证据卡、追问和报告，是官方复现的最低可靠路径。

### Realtime

持续传输视频和音频，流式接收文本和语音，支持主动说话和用户打断。该模式用于展示 MiniCPM-o 4.5 的全双工能力，但不能成为唯一可运行路径。

## 4. 核心对象

- `Session`：伴随会话及其运行模式、任务和状态。
- `TaskCard`：任务目标、步骤、检查点和允许的提示。
- `Observation`：模型对当前视频、音频和上下文的结构化理解。
- `Event`：经策略确认、可展示和可记录的现场事件。
- `Intervention`：由事件触发的主动提醒。
- `EvidenceCard`：用户可检查的事件证据。
- `OperationReport`：会话结束后的结构化总结。

## 5. 稳定性要求

- 相同事件必须去重，并设置提醒冷却时间。
- 网络断开后界面必须显示状态，不能继续伪装在线。
- 音频播放被打断时应清空旧响应，避免新旧语音重叠。
- 模型不可用时允许切换 Stable，但必须明确显示当前模式。
- 所有延迟指标必须注明测量边界，不能混用浏览器时间和服务端时间。
