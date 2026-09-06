# Review Output

Write every review response in Chinese using UTF-8. Lead with findings and keep the summary secondary.

## Finding Shape

```markdown
发现

High · runtime-contract · contract
[path/to/file.ts:42] 必填业务字段被 fallback 掩盖
这里把缺失值转换成空字符串，使无效状态看起来合法。影响是……。建议由 owning schema 强制该字段，并删除调用端 fallback。

Medium · measured · shrink
[path/to/file.tsx:88] 交互更新包含已测得的长任务
在……场景中，trace 显示……。建议……，并用相同方法复测。

偏好建议
- 仅列没有具体风险、但与稳定个人偏好不一致的选择。

验证缺口
- 未运行或未提供的测试、命令、截图、trace、设备或官方契约检查。

总结
一句话说明整体风险。
```

## Requirements

- Order findings by `Critical`, `High`, `Medium`, then `Low`.
- Include the rule basis: `standard`, `runtime-contract`, `measured`, or `project-rule`.
- Cite the exact repository instruction or project-owned contract for every `project-rule` label.
- Distinguish the defect basis from a preferred remedy when they differ.
- Prefix a remedy supported only by Ludwig's preference with `偏好修复方向` and avoid presenting it as the sole contract-valid solution.
- Add a complexity tag when useful: `delete`, `reuse`, `platform`, `dependency`, `yagni`, `shrink`, or `contract`.
- Include a file and line, exact diff/plan/log reference, screenshot area, trace event, or API contract.
- Explain the problem, concrete impact, and suggested correction or decision path.
- Separate facts from inferences and assumptions.
- Keep pure personal preferences out of severity-ranked findings unless a concrete risk is demonstrated.
- Separate validation gaps from defects.
- Describe meaningful complexity reduction as removed concepts, states, sources of truth, dependencies, or compatibility paths rather than lines deleted.
- If no material issue exists, say so directly and list only useful residual risks.
- Do not include raw JSON, full logs, large pasted diffs, transcript history, or generic praise unless requested.
