---
name: sol-max-subagents
description: "Use in Codex only when a Sol Max worker has been chosen to execute a complete implementation or test plan. Planning, investigation, and review are outside its scope."
compatibility: "Codex only. Requires Codex subagent tools supporting gpt-6.2-sol, max reasoning effort, and fork_turns: none."
---

# Sol Max Subagents

Sol Max is optional once the lead has settled the approach, bounded the work, and specified what to implement or test and how to verify success. These prerequisites also apply when the user names Sol. Keep planning, diagnosis, and design decisions with the lead or another suitable model.

Use the lead or a non-Sol reviewer for code and plan reviews, even when a detailed checklist exists. For example, Sol may implement a regression test for a specified failure and expected outcome. Assessing whether a test suite covers the right failure modes is review work.

## Dispatch Sol workers

For work assigned to Sol, use Codex's `collaboration.spawn_agent` within the current chat. Pass the dispatch settings explicitly as shown below.

```json
{
  "task_name": "add_output_alias",
  "model": "gpt-6.2-sol",
  "reasoning_effort": "max",
  "fork_turns": "none",
  "message": "In the existing CLI argument parser, accept --output as an alias for -o using the same option definition. Extend the parser tests to check both spellings produce the same output path and reject a missing value. Run the parser suite and report the result."
}
```

When overriding the model, use `fork_turns: "none"` and include the plan, relevant context, assigned scope, and acceptance checks in the message. A full-history fork does not support this model override.

The lead handles delegation and assigns file ownership when workers share a checkout. If the requested model or effort is unavailable, report that to the user. If execution reveals a missing design decision, the worker returns it to the lead before continuing. The lead integrates the result and verifies it against the acceptance criteria.
