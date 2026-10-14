---
name: ludwig-personal-code-review-preferences
description: "按 Ludwig 的工程偏好审查 TypeScript 生态的代码、diff、PR、方案、架构、依赖、性能、测试和工具链，或在明确要求时保持行为不变地简化。用于用户要求 review、simplify 或 clean-up 时。默认只读；只有明确要求简化、清理、修复或实现时才改代码。"
---

# Ludwig Review

Review risks or simplify correct code against stable, cross-project TypeScript ecosystem preferences. Keep project history and repository-specific layouts out of this skill. Treat current user instructions, repository rules, exact installed versions, and verified runtime behavior as higher-priority facts.

## Intent and Permission

Classify the objective and permission independently:

- `review`: Find correctness, security, contract, architecture, performance, testing, tooling, and maintainability issues.
- `simplify`: Reduce owned concepts, states, sources of truth, dependencies, branches, and compatibility paths while preserving observable behavior. Focus discovery on quality; route incidental correctness concerns to a separate report without changing them.
- `read-only`: Use for review, analysis, planning, or simplification advice.
- `apply`: Use only when the user directly asks to simplify, clean up, fix, or implement an explicit target.

Infer both dimensions from the user's wording. Ask only when a material edit would otherwise rest on ambiguous permission or scope.

## Operating Rules

- Read the current repository instructions and relevant project skills before applying personal preferences.
- Apply repository instructions only after confirming that the target belongs to that repository. Treat standalone pasted code, plans, logs, and screenshots as context-free unless the user links them to the current workspace.
- Inspect the actual target and surrounding ownership boundaries before judging it.
- Preserve unrelated worktree changes. Search beyond the target read-only when needed, and extend the write scope only with explicit authorization.
- Verify version-sensitive claims against the installed package types/source and the matching official documentation. Do not assume the newest documentation matches the installed version.
- Distinguish standards, runtime contracts, measured evidence, project rules, and personal preferences.
- Report only actionable issues with a concrete impact. Keep non-risk style preferences separate from severity-ranked findings.
- Use personal preferences to choose among contract-preserving alternatives. Treat a preference that would change behavior as a review or implementation decision, not as automatic simplification.
- Respond in Chinese using UTF-8 for every intermediate update and final response.

## References

Load only the references relevant to the target:

| File | Load when |
| --- | --- |
| `references/core-review.md` | Every review and simplification. Defines evidence, rule basis, minimality, contracts, and review severity. |
| `references/simplification-execution.md` | Every `simplify` objective. Defines the four passes, preference gate, edit discipline, and completion criteria. |
| `references/simplicity-and-architecture.md` | Every simplification, plus architecture, refactor, abstraction, ownership, folder, module, package, or public API review. |
| `references/typescript-toolchain.md` | TypeScript types, schemas, tsconfig, compiler, lint, module resolution, declaration, or monorepo tooling. |
| `references/react-and-web.md` | React, frontend, browser, UI, accessibility, CSS, rendering, or web API review. |
| `references/performance.md` | Runtime, render, bundle, build, cache, streaming, memory, latency, or other performance claims. |
| `references/dependencies-and-runtime.md` | Dependencies, SDKs, parsing, HTTP, network, sockets, protocols, native, OS, or package publishing. |
| `references/testing-and-validation.md` | Every applied change, plus tests, bug fixes, CI, release validation, or claims that checks passed. |
| `references/output.md` | Before writing a final `review` response. |
| `references/simplify-output.md` | Before writing a final `simplify` response. |

## Required Inputs

- Require an actual target: diff, PR, files, branch, plan, logs, screenshots, trace, or pasted code. When the user implies the current workspace, inspect the obvious local diff.
- Confirm the target's repository provenance before loading project-specific rules.
- When the current workspace is the target, inspect status plus staged, unstaged, and untracked changes instead of relying on a single diff command.
- Require repository instructions when reviewing repository code.
- Require official docs or installed source/types before blocking on a version-sensitive API claim.
- Require actual output before claiming lint, typecheck, tests, build, screenshots, traces, or benchmarks passed.
- For each applied simplification, require a stated behavior contract, a credible equivalence basis, and proportionate validation. Keep uncertain candidates as advice.

## Scope Classification

Classify the target before loading references:

- Correctness, security, or data contract.
- TypeScript types, schemas, compiler, modules, or tooling.
- Architecture, ownership, public API, refactor, or folder structure.
- React, frontend, browser, UI, or accessibility.
- Dependencies, SDKs, parsing, protocols, runtime, or publishing.
- Performance, observability, build, bundle, cache, or streaming.
- Testing, CI, release, or validation.

## Shared Workflow

1. Resolve the target, repository provenance, objective, and permission. Complete this step when the applicable project context, write boundary, and expected outcome are explicit.
2. Load repository instructions, obvious project context, and relevant project skills. Complete this step when project rules are separated from stable preferences.
3. Inspect the target, surrounding owners, callers, callees, tests, public surfaces, and existing facilities. Complete this step when every proposed conclusion can be tied to its owning context.
4. Load `references/core-review.md` and only the applicable domain references. Verify version-sensitive external facts before treating them as blockers. Complete this step when each conclusion has a rule basis and evidence status.

## Review Branch

1. Run the minimality, contract, and applicable domain passes.
2. Rank concrete findings by user impact and engineering risk.
3. With `apply` permission, fix only confirmed in-scope findings and validate the changed behavior.
4. Load `references/output.md` and return findings first, followed by preference suggestions and validation gaps.

Complete the branch when every finding has a location, rule basis, concrete impact, and decision path, and the permission boundary was respected.

## Simplify Branch

1. Load `references/simplification-execution.md`, `references/simplicity-and-architecture.md`, and the applicable domain references.
2. Establish the observable behavior and public contracts to preserve.
3. Execute all four simplification passes and deduplicate their candidates.
4. With `read-only` permission, return accepted candidates as advice. With `apply` permission, use one writer to apply only candidates that pass the preference and equivalence gate.
5. Load `references/testing-and-validation.md`, validate applied changes in repository order, then load `references/simplify-output.md`.

Complete the branch when all four passes ran, every applied change has an equivalence basis and observed validation result, incidental correctness risks remain separate, and no unrelated file changed.

## Verification

Before finalizing, verify:

- The target, objective, permission, and write scope are clear.
- Repository rules and relevant references were loaded.
- The target and surrounding ownership context were inspected.
- Version-sensitive claims were verified.
- Findings identify their basis and concrete impact.
- Personal preferences were not presented as external standards.
- Validation results and gaps are reported accurately.
- No files were changed during a read-only request.
