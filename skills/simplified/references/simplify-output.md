# Simplification Output

Write every simplification response in Chinese using UTF-8. Lead with the applied or proposed result. Render the headings and examples below in Chinese in the actual report.

## Shape

```markdown
Simplified

- `path/to/file.ts:42` · shrink — Removed duplicate state and the branch that synchronized it. Describe what was removed and the evidence that behavior is equivalent.

Skipped

- `path/to/file.ts:88` · contract — This requires a change in error semantics. Track it as a review candidate.

Incidental correctness risks

- Include only findings discovered incidentally and left unchanged during simplification.

Validation

- `exact command` — Give the observed outcome and a short explanation where needed.

Verification gaps

- List tests, platforms, screenshots, traces, or contracts that were not checked or could not be observed.

Summary

Describe the reduction in owned complexity and any residual risk in one sentence.
```

## Requirements

- Describe success as removed concepts, states, sources of truth, dependencies, branches, compatibility paths, or misplaced responsibilities.
- Include the exact location, complexity tag, concrete reduction, and equivalence basis for each applied or proposed change.
- Explain every skipped high-value candidate and whether it needs wider scope, evidence, or separate behavior-change authorization.
- Keep incidental correctness risks separate and use the rule basis and severity from `output.md` when ranking them.
- Report exact observed validation commands and outcomes.
- Identify any independent review the user requested that could not be completed.
- If no candidate passes the gate, say that no high-confidence behavior-preserving simplification was found and list only useful residual risks.
- Omit empty sections and avoid raw JSON, full logs, large diffs, transcript history, line-count celebration, or generic praise.
