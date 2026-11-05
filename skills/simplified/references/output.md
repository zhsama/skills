# Review Output

Write every review response in Chinese using UTF-8. Lead with findings and keep the summary secondary. Render the headings and examples below in Chinese in the actual report.

## Finding Shape

```markdown
Findings

High · runtime-contract · contract
[path/to/file.ts:42] A fallback hides a missing required field
The caller converts a missing value to an empty string, making invalid state look valid. Explain the impact. Enforce the field in its owning schema and remove the fallback at the call site.

Medium · measured · shrink
[path/to/file.tsx:88] An interaction produces a measured long task
Identify the interaction and what its trace shows. Give a correction and repeat the measurement under the same conditions.

Preference suggestions
- Include a choice here when it poses no concrete risk but differs from a stable personal preference.

Verification gaps
- List relevant tests, commands, screenshots, traces, device checks, or official contracts that could not be verified.

Summary
State the overall risk in one sentence.
```

## Requirements

- Order findings by `Critical`, `High`, `Medium`, then `Low`.
- Include the rule basis: `standard`, `runtime-contract`, `measured`, or `project-rule`.
- Cite the exact repository instruction or project-owned contract for every `project-rule` label.
- Distinguish the defect basis from a preferred remedy when they differ.
- If a remedy reflects only zhsama's preference, label it “preferred repair direction” in the language of the report. Acknowledge other remedies that satisfy the contract.
- Add a complexity tag when useful: `delete`, `reuse`, `platform`, `dependency`, `yagni`, `shrink`, or `contract`.
- Include a file and line, exact diff/plan/log reference, screenshot area, trace event, or API contract.
- Explain the problem, concrete impact, and suggested correction or decision path.
- Separate facts from inferences and assumptions.
- Keep pure personal preferences out of severity-ranked findings unless a concrete risk is demonstrated.
- Separate validation gaps from defects.
- Describe meaningful complexity reduction as removed concepts, states, sources of truth, dependencies, or compatibility paths rather than lines deleted.
- If no material issue exists, say so directly and list only useful residual risks.
- Do not include raw JSON, full logs, large pasted diffs, transcript history, or generic praise unless requested.
