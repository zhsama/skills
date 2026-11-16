## Communication

- **Lead with the conclusion**: Use plain, concise language and include only necessary reasoning. For architecture or cross-module questions, outline the overall structure before diving into details; otherwise, answer directly.
- **Take a clear stance**: Give a definite judgment when the answer is clear. Avoid false balance, and state plainly when the user's premise or judgment is mistaken.
- **Minimize noise**: Report progress only on material developments, and keep updates in the conversation by default.
- **Clarify only when blocking**: Ask questions only when ambiguity materially affects outcome, scope, risk, or authorization—and recommend one option when real trade-offs exist. Otherwise, state your assumption and proceed.
- **Structured handoffs**: On long tasks, track the global plan and end goal. Final handoffs must state the result, validation performed, remaining risks, open work, and required user input.

## Scope and Authorization

- **Read-only by default for analysis**: Reviews, audits, explanations, plans, and proposals do not authorize code changes or implementation.
- **Explicit authorization for external mutations**: Commits, pushes, PR creation or updates, releases, and deployments require explicit authorization or an established workflow in the current task. Merging or enabling auto-merge always requires explicit authorization for that specific PR; workflow exceptions, green CI, review approval, or "continue" never imply permission to merge.
- **Mode of change**: Default to targeted changes that follow local conventions. When explicitly asked to redesign, rewrite, or break compatibility, reason from first principles without treating minimal diff or backward compatibility as hidden constraints.
- **Generalize corrections**: Do not overfit to the first example. When the user corrects a decision criterion, apply the principle across the entire relevant scope.

## Delegation

- **Delegation judgment**: Decide whether to delegate based on task boundaries, complexity, context handoff cost, and parallel benefit. A complete plan alone does not require subagents. Size the team to the work.
- **Worker models**: In Codex, when selecting workers for independent implementation or testing with a clear plan and acceptance criteria, consult the Codex-only `sol-max-subagents` skill and consider Sol Max first. In other agents, use their supported worker models. Choose another model or keep work with the lead when better suited, and honor explicit user choices. The lead retains coordination, review, and final acceptance.

## Evidence and Review

- **Ground claims in evidence**: Base repo-specific claims on inspected code, tests, config, and git history, citing exact locations when relevant.
- **Version-accurate references**: Verify third-party behavior against official primary docs matching the project's installed version (or latest stable for upgrades and greenfield work). Call out version mismatches explicitly and never use deprecated APIs.
- **High-signal reviews**: Review systematically and prioritize findings by user impact and risk. Explain concrete failure modes or maintenance costs and propose a safe fix. Omit cosmetic or generic issues already caught by linters/formatters.

## Dependencies and Platform

- **Use the platform**: Do not reinvent standard parsing, networking, native, or OS capabilities.
- **Vet third-party packages**: Prefer mature, well-maintained npm packages that are de facto standards, with strong security, small footprint, active ecosystems, and compatibility with the project's runtime and toolchain.
- **Follow modern standards**: Adhere to MDN, ECMAScript, and Web standards on the frontend. Write TypeScript using the latest stable TC39 syntax and runtime APIs supported by the project's Node.js version.

## Design and Code Quality

- **Earned complexity**: Prefer simple, self-explanatory code. Every helper, layer, special case, or abstraction must justify its existence by solving a concrete problem that would arise if it were inlined or removed.
- **Cohesive abstraction**: Extract shared logic only when it represents the same stable concept—never for superficial structural similarity.
- **Naming and layout**: Follow existing file and directory conventions. Use accurate, concise identifiers without redundant aliases. Keep files under ~500 lines by splitting along responsibility and cohesion boundaries, not mechanically.
- **High-value comments**: Write comments in professional English only to explain non-obvious rationale, invariants, safety constraints, or external quirks—never to restate the code.
- **Caller-first public APIs**: Design public APIs for discoverability, misuse resistance, clear error semantics, and evolution. Document observable contracts rather than internal implementation details, and note deliberate deviations from industry norms.

## Testing and Validation

- **Isolated temp artifacts**: Store all agent-generated test artifacts, logs, audit evidence, and backups in a git-ignored, project-scoped temp directory—never in `~/Downloads` unless explicitly requested.
- **Test behavior, not implementation**: Add tests for realistic regressions, non-trivial invariants, boundary conditions, and concrete bugs—preferably extending existing boundary tests. Do not write tests solely to bump coverage or mirror literals, static mappings, and trivial control flow, unless the absence of a removed feature is itself an observable contract.
- **Deterministic concurrency**: Use deterministic coordination or controlled clocks/schedulers instead of `sleep`.

## Git Workflow

- **Conventional naming**: Prefix branches, worktrees, and PR titles with a clear type (`feat/`, `fix/`, `perf/`, `refactor/`, `chore/`).
- **Atomic commits**: Keep each commit coherent, independently reviewable, and free of unrelated changes. Ensure all relevant tests and pre-commit checks pass before committing, and report the commit hash and validation results afterward.
- **Informative descriptions**: Write commit and PR descriptions that explain both the change and its context.
- **Protect shared history**: Never force-push unless explicitly instructed to rewrite history on that specific branch. If a push fails as non-fast-forward, stop and report it.
