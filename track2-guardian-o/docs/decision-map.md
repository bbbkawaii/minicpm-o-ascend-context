# 赛道二决策地图

目标：在 2026-08-17 提交截止前，完成一个可在官方昇腾环境复现、能充分展示 MiniCPM-o 4.5 全模态实时交互能力、具备冠军竞争力的创新应用。

## Notes

- 当前主推概念：**见微 Guardian-O——全模态实验室操作教练与安全伴随助手**。
- 核心体验：摄像头和麦克风持续输入；助手边看边听，在关键步骤主动语音提醒；用户可随时打断追问；会话结束后生成带证据的操作报告。
- 独立实现：赛道二维护自己的模型适配、延迟指标和稳定性验证，不调用或复用赛道一项目中的服务、配置或结果。
- MVP 只做一个实验室安全演练流程和三个可重复触发的事件，不扩展到医疗、真实危险决策或通用 Agent。
- 用户偏好：以冲击一等奖为目标；Codex 承担产品、代码、测试、文档、PPT 和演示脚本的大部分工作；用户负责账号权限、HiDevLab 操作、最终录屏和提交。

## dual-track-eligibility: 能否同时参加两个赛道？

Blocked by:
Status: open
Type: Research

### Question

同一参赛者或团队是否允许同时提交赛道一和赛道二，是否存在重复获奖、仓库复用或队伍身份限制？

### Answer

公开赛题页没有明确写出同一主体同时参赛与获奖的限制，需要通过官方飞书群或 contact@openbmb.cn 获取书面确认。该问题不阻塞赛道二原型，但会影响最终报名和提交结构。

## concept-proof: 主推概念能否形成冠军级演示？

Blocked by:
Status: open
Type: Prototype

### Question

“实验室操作教练与安全伴随助手”是否能在 90 秒内形成清晰、稳定、可重复的完整演示闭环，并明显优于普通多模态聊天 Demo？

### Answer

当前假设：采用安全道具完成“任务开始 → 主动发现遗漏 → 用户打断追问 → 继续观察 → 自动生成报告”的单场景原型；以假后端先验证交互节奏，再接 MiniCPM-o 4.5。

## mvp-boundary: MVP 功能边界

Blocked by: concept-proof
Status: open
Type: Grilling

### Question

首个可提交版本必须包含哪些用户流程、事件类型和失败兜底，哪些功能明确延期？

### Answer


## runtime-contract: 昇腾推理服务接口契约

Blocked by: concept-proof
Status: open
Type: Research

### Question

赛道二自己的 MiniCPM-o 4.5 适配层如何提供实时视频、音频、流式文本/语音、打断和指标数据，并在全双工暂不可用时降级？

### Answer


## demo-storyboard: 决赛演示脚本与证据

Blocked by: mvp-boundary, runtime-contract
Status: open
Type: Prototype

### Question

如何用一镜到底的演示证明全模态能力、场景价值、交互自然度、低延迟、工程质量和可复现性？

### Answer


## submission-package: 提交材料闭环

Blocked by: demo-storyboard
Status: open
Type: Task

### Question

如何完成可运行 Web Demo、项目说明、部署文档、PPT、演示视频、测试证据和最终提交包？

### Answer
