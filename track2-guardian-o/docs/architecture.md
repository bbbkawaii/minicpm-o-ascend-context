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
  ├─ event policy, deduplication and confirmation
  ├─ result-impact assessment
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
- `TaskCard`：任务目标、步骤、检查点、结果关键条件和允许的提示。
- `Observation`：模型对当前视频、音频和上下文的结构化理解。
- `Event`：经策略确认、可展示和可记录的现场事件。
- `ResultImpact`：事件对样品、实验条件、数据有效性和任务成败的潜在影响，以及可恢复性判断。
- `Intervention`：由事件触发的主动提醒，包含观察、后果解释和纠正建议。
- `EvidenceCard`：用户可检查的事件证据。
- `OperationReport`：会话结束后的结构化总结，标注实验有效性状态。

## 5. 实验有效性状态

Guardian-O 只根据任务卡定义的可观察检查点和事件规则判断本次流程是否仍有效，不根据画面臆测最终实验结果。会话状态取以下值：

- `valid`：未发现影响结果的未纠正事件。
- `at_risk`：发现可能影响结果的操作，但尚可在不可逆步骤前纠正。
- `invalid`：已跨过任务卡定义的不可逆检查点，当前结果不应继续使用，建议重做。
- `unknown`：证据不足，需用户或指导人员确认。

只有事件被确认且任务卡明确给出影响规则时，系统才能将状态标记为 `invalid`；否则保持 `at_risk` 或 `unknown`，避免把模型推断冒充实验结论。

## 6. 稳定性要求

- 相同事件必须去重，并设置提醒冷却时间。
- 结果影响判断必须关联任务卡检查点、证据帧和可恢复性，不能只凭语言模型自由生成。
- 用户及时纠正后必须重新观察并更新事件和实验有效性状态。
- 网络断开后界面必须显示状态，不能继续伪装在线。
- 音频播放被打断时应清空旧响应，避免新旧语音重叠。
- 模型不可用时允许切换 Stable，但必须明确显示当前模式。
- 所有延迟指标必须注明测量边界，不能混用浏览器时间和服务端时间。
