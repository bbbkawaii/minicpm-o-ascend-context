# 协作开发流程

## 1. 先确定项目归属

- 推理、Benchmark、量化、算子、显存、吞吐、TTFT、TTFP、RTF：进入 `track1-inference-optimization/`。
- Guardian-O 的界面、会话、事件、报告、演示、应用部署：进入 `track2-guardian-o/`。
- 不确定归属时先建 Discussion 或 Issue，不要先写跨项目代码。

## 2. Issue 规则

每项工作先建立 Issue，至少写清：

- 问题与目标
- 所属赛道
- 验收标准
- 运行环境
- 预期产物
- 风险或阻塞

建议标签：`track:1`、`track:2`、`type:bug`、`type:feature`、`type:docs`、`status:blocked`。

## 3. 分支规则

从最新 `main` 创建短生命周期分支：

```bash
git switch main
git pull --ff-only
git switch -c track1/<issue>-<short-name>
# 或
git switch -c track2/<issue>-<short-name>
```

禁止直接在共享的 `main` 上并行开发。一个分支只处理一个 Issue。

## 4. 开发循环

1. 在所属项目目录阅读 `README.md`、`CONTEXT.md` 和相关文档。
2. 先记录基线或失败复现。
3. 做最小范围修改。
4. 运行项目自己的测试和检查。
5. 更新对应文档、指标或演示证据。
6. 提交小而清晰的 commit。
7. 创建 PR，等待至少一名协作者检查。

## 5. Commit 约定

```text
feat(track1): add audio latency benchmark
fix(track1): preserve streaming correctness
feat(track2): add proactive event timeline
docs(track2): define demo fallback path
chore(repo): update competition rule status
```

## 6. PR 验收

- PR 默认只能修改一个赛道目录。
- 必须写明运行命令和结果。
- 性能修改必须附修改前后数据，并说明正确性是否保持。
- 应用修改必须附截图、录屏或可复现交互步骤。
- 不提交权重、密钥、大型日志、原始 profiling 文件或个人数据。
- 合并前应保持分支可独立运行，不依赖另一赛道的未合并代码。

## 7. 冲突处理

- 同一文件只能指定一名当前负责人，其他人通过 Review 或后续 PR 修改。
- 发生冲突时由后提交者基于最新 `main` 重新整理，不强推覆盖他人分支。
- 影响比赛结论、评分口径或提交格式的变更必须附官方来源。
