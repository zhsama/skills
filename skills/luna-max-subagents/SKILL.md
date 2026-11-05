---
name: luna-max-subagents
description: "Use when the user requests Luna Max subagents. The lead delegates to gpt-5.6-luna with max reasoning effort, coordinates the work, and checks the results. Default to three subagents unless the user specifies a count or the task calls for a different one."
compatibility: "Requires a subagent runtime supporting gpt-5.6-luna, max reasoning effort, and the documented dispatch and coordination parameters."
---

# Luna Max Subagents

The lead keeps its current model, interprets the request, assigns work, integrates the results, and verifies them. Each subagent uses `gpt-5.6-luna` with `max` reasoning effort.

## Count and assignments

Use the current request and any follow-ups to determine the goals, count, and limits. Loading this skill does not by itself start any agents or define their tasks.

- Honor a specified count and division of work. If the user gives only a goal, divide it among the chosen number of agents.
- Default to three when no count is specified. If another count clearly fits the task better, choose it and briefly explain why without pausing for permission.
- If the task itself is missing and cannot be inferred from context, ask a short question about the task.
- When a follow-up changes an existing assignment, send it to the responsible subagent. Add agents only when explicitly requested.

## Create the subagents

Use the runtime's subagent tool, such as `collaboration.spawn_agent`, to delegate within the current chat. Pass the dispatch settings explicitly as shown below.

```json
{
  "task_name": "inspect_api",
  "model": "gpt-5.6-luna",
  "reasoning_effort": "max",
  "fork_turns": "none",
  "message": "Inspect the API. Include task-specific context, available files or resources, deliverables, and permitted actions."
}
```

Adapt the task name and message to the assignment. Use unique lowercase letters, digits, and underscores for `task_name`. When overriding the model, use `fork_turns: "none"` and include the necessary context in the message, or use limited history if the runtime supports it. A full-history fork does not support this model override.

Give each task clear boundaries. In a shared working directory, assign file ownership and identify dependencies so concurrent edits do not overwrite one another. Each subagent completes its assigned task without creating additional subagents.

Honor the runtime's concurrency limit. If slots can be released, dispatch in batches. Otherwise, explain the limit and let the user choose a feasible arrangement. If the tool, model, or `max` reasoning effort is unavailable, report the specific limitation rather than silently reducing the requested count or changing models or effort.

## Coordinate and deliver

While the subagents work, the lead can coordinate, inspect, and integrate independent parts of the task. Handle dependencies and later instructions. Use the returned agent IDs to send messages and wait for results without duplicating assignments.

Once all results are in, check coverage of every requested task, resolve conflicts, and perform the required validation. Report the combined result and remaining issues. Dispatch alone does not complete the task. Each subagent operates only within the user's authorization.
