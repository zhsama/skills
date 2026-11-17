---
name: sol-max-subagents
description: "Codex-only Sol Max delegation. Use in Codex when selecting workers for independent implementation or testing with a clear plan and acceptance criteria, or when the user requests Sol Max subagents. Choose what to delegate, dispatch suitable work to gpt-6.2-sol at max through Codex's subagent tools, and verify the results."
compatibility: "Codex only. Requires Codex subagent tools supporting gpt-6.2-sol, max reasoning effort, and fork_turns: none."
---

# Sol Max Subagents

Use this skill only from Codex. Its dispatch and coordination instructions depend on Codex's subagent runtime and do not apply to Claude Code or other agents.

The lead keeps its current model and owns task assignment, integration, and final verification. Workers selected for Sol use `gpt-6.2-sol` with `max` reasoning effort.

## Decide and assign

Use the current request and any follow-ups to determine the goals, count, and limits. Loading this skill does not by itself start any agents or define their tasks.

- Decide whether to delegate based on task boundaries, complexity, context handoff cost, and parallel benefit. A complete plan alone does not require subagents.
- For independent implementation or testing with a clear plan and acceptance criteria, consider Sol Max first. Keep work with the lead or select another model when better suited; honor explicit user model choices.
- Honor a specified count and division of work. Otherwise choose the number of workers to fit the independent tasks and runtime limits, including a single worker when sufficient.
- If the task itself is missing and cannot be inferred from context, ask a short question about the task.
- Send follow-ups to the agent responsible for the assignment. Add workers only when the remaining work warrants them, within the user's scope and team limits.

## Dispatch Sol workers

For work assigned to Sol, use Codex's `collaboration.spawn_agent` within the current chat. Pass the dispatch settings explicitly as shown below.

```json
{
  "task_name": "implement_api",
  "model": "gpt-6.2-sol",
  "reasoning_effort": "max",
  "fork_turns": "none",
  "message": "Implement the approved API change in the assigned files. Follow the supplied plan and acceptance criteria, run the required checks, and report the changes and results."
}
```

Adapt the task name and message to the assignment. Use unique lowercase letters, digits, and underscores for `task_name`. When overriding the model, use `fork_turns: "none"` and include the approved plan, relevant context, owned files, acceptance criteria, checks, and permitted actions in the message. A full-history fork does not support this model override.

Give each task clear boundaries. In a shared working directory, assign file ownership and identify dependencies so concurrent edits do not overwrite one another. Each subagent completes its assigned task without creating additional subagents.

Honor the runtime's concurrency limit. Reuse workers or dispatch in batches when necessary. Report any limit that prevents fulfilling an explicit request. If the requested tool, model, or reasoning effort is unavailable, explain the limitation and any proposed fallback rather than silently substituting.

## Coordinate and deliver

While the subagents work, the lead can coordinate, inspect, and integrate independent parts of the task. Handle dependencies and later instructions. Use the returned agent IDs to send messages and wait for results without duplicating assignments.

Once all results are in, check coverage of every requested task, resolve conflicts, and perform the required validation. Report the combined result and remaining issues. Dispatch alone does not complete the task. Each subagent operates only within the user's authorization.
