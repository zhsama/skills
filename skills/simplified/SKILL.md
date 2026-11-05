---
name: simplified
description: "Review TypeScript ecosystem code, diffs, PRs, plans, architecture, dependencies, performance, tests, and tooling using zhsama's engineering preferences. Use for review, simplification, or cleanup requests. Reviews are read-only by default. Apply changes only when the user explicitly asks to simplify, clean up, fix, or implement the target."
---

# Simplified

Review risks or simplify correct code against stable, cross-project TypeScript ecosystem preferences. Keep project history and repository-specific layouts out of this skill. Treat current user instructions, repository rules, exact installed versions, and verified runtime behavior as higher-priority facts.

## Intent and Permission

Classify the objective and permission independently:

- `review`: Find correctness, security, contract, architecture, performance, testing, tooling, and maintainability issues.
- `simplify`: Reduce owned concepts, states, sources of truth, dependencies, branches, and compatibility paths while preserving observable behavior. Focus discovery on quality; route incidental correctness concerns to a separate report without changing them.
- `read-only`: Use for review, analysis, planning, or simplification advice.
- `apply`: Use only when the user directly asks to simplify, clean up, fix, or implement an explicit target.

Infer both dimensions from the user's wording. Ask only when a material edit would otherwise rest on ambiguous permission or scope.

## Operating Rules

- Read applicable repository instructions and project skills when present. If none exist, continue from the target code, configuration, and tests.
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

## Required Inputs

- Require an actual target: diff, PR, files, branch, plan, logs, screenshots, trace, or pasted code. When the user implies the current workspace, inspect the obvious local diff.
- Confirm the target's repository provenance before loading project-specific rules.
- When the current workspace is the target, inspect status plus staged, unstaged, and untracked changes instead of relying on a single diff command.
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
2. Apply any existing repository instructions and relevant project skills to the target, keeping project rules separate from personal preferences.
3. Inspect the target and follow the callers, tests, and ownership boundaries that bear on the conclusion.
4. Load the references that apply to the objective and scope above. Verify version-sensitive external facts before treating them as blockers.

## Review Branch

1. Run the minimality, contract, and applicable domain passes.
2. Rank concrete findings by user impact and engineering risk.
3. With `apply` permission, fix only confirmed in-scope findings and validate the changed behavior.
4. Load `references/output.md` and return findings first, followed by preference suggestions and validation gaps.

Complete the branch when every finding has a location, rule basis, concrete impact, and decision path, and the permission boundary was respected.

## Simplify Branch

Read `references/simplification-candidates.md` and identify the actual comparison. For a PR, compare against its target branch; a stack layer uses its parent, not the default branch. For workspace changes, include staged, unstaged, and relevant untracked files. Keep edits within the requested target and the updates needed to complete its cleanup.

For a local change such as simplifying one function, inspect the callers and the observable behavior to preserve. Use the candidate checklist only where it applies; do not manufacture a candidate for every row. Run the closest check that exercises the affected behavior and any checks the project requires. Report the change, the basis for equivalence, and the observed result or validation gap.

For a cross-module change or a request for comprehensive simplification, follow the four passes in `references/simplification-execution.md`. Use the same behavior contract and write boundary for all passes.

With read-only permission, return candidates as advice. With apply permission, change only candidates with a credible basis for equivalence. Report incidental behavior changes separately.

Ordinary simplification does not automatically become a controlled ablation study. When the user requests experimental evidence comparing variants, use `ablation-experiment` if available and follow its experiment-design and approval process.

## Verification

Before finalizing, verify:

- The target, objective, permission, and write scope are clear.
- Applicable project rules and references were considered.
- The target and surrounding ownership context were inspected.
- Version-sensitive claims were verified.
- Findings identify their basis and concrete impact.
- Personal preferences were not presented as external standards.
- Validation results and gaps are reported accurately.
- No files were changed during a read-only request.
