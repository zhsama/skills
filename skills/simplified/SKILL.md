---
name: simplified
description: "Review TypeScript ecosystem code, diffs, PRs, plans, architecture, dependencies, performance, tests, and tooling using zhsama's engineering preferences. Use for review, simplification, or cleanup requests. Reviews are read-only by default. Apply changes only when the user explicitly asks to simplify, clean up, fix, or implement the target."
---

# Simplified

Review risks or simplify correct code against stable, cross-project TypeScript ecosystem preferences. Keep project history and repository-specific layouts out of this skill. Treat current user instructions, repository rules, exact installed versions, and verified runtime behavior as higher-priority facts.

## Intent and Permission

Classify the objective and permission independently from the user's wording:

- `review`: Find correctness, security, contract, architecture, performance, testing, tooling, and maintainability issues.
- `simplify`: Reduce owned concepts, states, sources of truth, dependencies, branches, and compatibility paths while preserving observable behavior. Focus discovery on quality; route incidental correctness concerns to a separate report without changing them.
- `read-only`: Use for review, analysis, planning, or simplification advice.
- `apply`: Use only when the user directly asks to simplify, clean up, fix, or implement an explicit target.

Ask only when a material edit would otherwise rest on ambiguous permission or scope.

## Operating Rules and Inputs

- Require an actual target: diff, PR, files, branch, plan, logs, screenshots, trace, or pasted code. When the user implies the current workspace, inspect `git status` plus staged, unstaged, and untracked changes rather than relying on a single diff command.
- Confirm that the target belongs to the current repository before loading repository instructions or project skills. Treat standalone pasted code, plans, logs, and screenshots as context-free unless linked to the workspace.
- Inspect the target and follow the callers, tests, and ownership boundaries that bear on the conclusion. Preserve unrelated worktree changes, search beyond the target read-only when needed, and extend the write scope only with explicit authorization.
- Verify version-sensitive claims against the installed package types/source and matching official documentation before treating them as blockers. Do not assume the newest documentation matches the installed version.
- Distinguish standards, runtime contracts, measured evidence, project rules, and personal preferences. Use personal preferences to choose among contract-preserving alternatives, never as authority to change behavior or as disguised external standards.
- Report only actionable issues with a concrete impact, keeping non-risk style preferences separate from severity-ranked findings.
- Require actual command output before claiming lint, typecheck, tests, build, screenshots, traces, or benchmarks passed.
- Respond in Chinese using UTF-8 for every intermediate update and final response.

## References

Classify the target's domain and load only the relevant references:

| File | Load when |
| --- | --- |
| `references/core-review.md` | Reviews and comprehensive simplifications. Defines evidence, rule basis, minimality, contracts, and review severity. |
| `references/simplification-candidates.md` | Any simplification; also source-organization review involving comments, types, constants, or aliases. |
| `references/simplification-execution.md` | Cross-module simplification or an explicitly requested comprehensive pass. |
| `references/simplicity-and-architecture.md` | Architecture, abstractions, ownership, module boundaries, or public APIs. |
| `references/typescript-toolchain.md` | TypeScript types, schemas, tsconfig, compiler, lint, module resolution, declaration, or monorepo tooling. |
| `references/react-and-web.md` | React, frontend, browser, UI, accessibility, CSS, rendering, or web API review. |
| `references/performance.md` | Runtime, render, bundle, build, cache, streaming, memory, latency, or other performance claims. |
| `references/dependencies-and-runtime.md` | Dependencies, SDKs, parsing, HTTP, network, sockets, protocols, native, OS, or package publishing. |
| `references/testing-and-validation.md` | Test changes, bug fixes, CI, or validation that spans multiple behavior boundaries. |
| `references/output.md` | Before writing a final `review` response. |
| `references/simplify-output.md` | Before reporting a comprehensive simplification. |

## Review Branch

1. Run the minimality, contract, and applicable domain passes against the verified target and project context.
2. Rank concrete findings by user impact and engineering risk, each with a location, rule basis, concrete impact, and decision path.
3. With `apply` permission, fix only confirmed in-scope findings and validate the changed behavior.
4. Load `references/output.md` and return findings first, followed by preference suggestions and validation gaps.

## Simplify Branch

Read `references/simplification-candidates.md` and identify the actual comparison. For a PR, compare against its target branch; a stack layer uses its parent, not the default branch. For workspace changes, include staged, unstaged, and relevant untracked files. Keep edits within the requested target and the updates needed to complete its cleanup.

For a local change such as simplifying one function, inspect the callers and the observable behavior to preserve. Use the candidate checklist only where it applies; do not manufacture a candidate for every row. Run the closest check that exercises the affected behavior and any checks the project requires. Report the change, the basis for equivalence, and the observed result or validation gap.

For a cross-module change or a request for comprehensive simplification, follow the four passes in `references/simplification-execution.md` under a single behavior contract and write boundary.

With `read-only` permission, return candidates as advice. With `apply` permission, change only candidates with a stated behavior contract, a credible basis for equivalence, and proportionate validation; keep uncertain candidates as advice and report incidental behavior changes separately.

Ordinary simplification does not automatically become a controlled ablation study. When the user requests experimental evidence comparing variants, use `ablation-experiment` if available and follow its experiment-design and approval process.
