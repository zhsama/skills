# Simplification Output

Write every simplification response in Chinese using UTF-8. Lead with the applied or proposed result.

## Shape

```markdown
已简化

- `path/to/file.ts:42` · shrink — 删除重复状态和同步分支。移除了……；行为等价依据是……。

跳过

- `path/to/file.ts:88` · contract — 需要改变错误语义，已转为 review 候选。

意外发现的正确性风险

- 仅列 discovery 中偶然发现且未在 simplify 模式修改的问题。

验证

- `exact command`：通过/失败及必要摘要。

验证缺口

- 未运行或无法观察的测试、平台、截图、trace 或契约检查。

总结

一句话说明减少了哪些 owned complexity，以及剩余风险。
```

## Requirements

- Describe success as removed concepts, states, sources of truth, dependencies, branches, compatibility paths, or misplaced responsibilities.
- Include the exact location, complexity tag, concrete reduction, and equivalence basis for each applied or proposed change.
- Explain every skipped high-value candidate and whether it needs wider scope, evidence, or separate behavior-change authorization.
- Keep incidental correctness risks separate and use the rule basis and severity from `output.md` when ranking them.
- Report exact observed validation commands and outcomes.
- Disclose when the four passes ran sequentially because independent reviewer agents were unavailable.
- If no candidate passes the gate, say that no high-confidence behavior-preserving simplification was found and list only useful residual risks.
- Omit empty sections and avoid raw JSON, full logs, large diffs, transcript history, line-count celebration, or generic praise.
