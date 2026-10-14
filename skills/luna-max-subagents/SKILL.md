---
name: luna-max-subagents
description: "由主 agent 按用户 prompt 指定的数量和任务创建 gpt-5.6-luna、max 推理强度的 subagent，并协调与汇总结果。用于用户要求 Luna Max 子代理协作时。"
compatibility: "Requires a subagent runtime supporting gpt-5.6-luna, max reasoning effort, and the documented dispatch and coordination parameters."
---

# Luna Max Subagents

主 agent 保持当前模型，负责理解任务、分配工作、整合和验证结果。子代理统一使用 `gpt-5.6-luna`，推理强度为 `max`。

## 数量与任务

从用户当前及后续 prompt 读取子代理数量、各自任务和限制。本技能不预设数量或任务，也不因被加载就立即创建子代理。

- 用户给出数量和分工时，按指定执行；只给出总体任务时，在指定数量内拆分工作。
- 数量或任务缺失且无法从上下文确定时，简短询问缺失信息；用户明确让主 agent 自行决定时才自行选择。
- 后续 prompt 调整已有分工时，优先给对应子代理发送补充任务；明确要求新增时才增加数量。

## 创建子代理

使用运行时的子代理工具，例如 `collaboration.spawn_agent`；不要用创建 Codex 侧栏任务的工具代替。

每次创建明确传入：

```json
{
  "task_name": "inspect_api",
  "model": "gpt-5.6-luna",
  "reasoning_effort": "max",
  "fork_turns": "none",
  "message": "具体任务、必要上下文、可访问的文件或资源、交付要求和操作范围。"
}
```

示例中的名称和任务正文按实际分工替换。`task_name` 使用不重复的小写字母、数字和下划线。显式覆盖模型时不要使用 `fork_turns: "all"`；使用 `none` 并在消息中提供足够上下文，或使用运行时支持的有限历史数量。

每个任务应有明确边界。共享工作目录时明确文件责任与依赖，避免并发覆盖同一处修改。子代理完成被分配的工作即可，不自行扩增子代理数量。

遵守运行时并发上限；超出上限时，若支持释放名额则分批创建，否则说明限制并让用户选择可行安排，不悄悄减少数量。若子代理工具、指定模型或 `max` 不可用，说明具体限制，不擅自更换模型或推理强度。

## 协调与交付

主 agent 在子代理工作期间推进独立的协调、检查或整合工作，处理依赖及用户补充要求。使用返回的 agent ID 跟踪、发送消息和等待结果，不重复创建同一任务。

收齐结果后检查是否覆盖用户指定的全部任务，解决冲突并执行任务所需的验证，再给出统一结果和剩余问题。创建子代理不等于完成任务；子代理的操作权限沿用用户对当前工作的授权范围。
