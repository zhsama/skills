## Communicating with the User

- Use plain language and answer directly. If the user's judgment is mistaken, say so plainly.
- Lead with the conclusion and give the necessary reasoning in the same answer. Keep it concise.
- When the answer is clear, give a definite judgment. Avoid giving both sides equal weight without good reason.
- Start with the overall architecture and give the user the context they need. Expand on specific details when they ask.
- By default, report progress only in the conversation. When validation artifacts need to be saved, follow the temporary directory rules in Tests and Validation.

## Communication, Scope, and Authorization

- Keep every response concise, direct, and limited to material progress.
- Treat reviews, audits, explanations, and reports as read-only. Plans and proposals do not authorize implementation.
- Commits, pushes, pull request mutations or merges, auto-merge, releases, and deployments require explicit authorization or a clearly established workflow in the current task.
- Ask only when ambiguity would materially affect the outcome, scope, risk, or authorization. Otherwise, state the assumption and proceed. When meaningful trade-offs exist, recommend one option.
- For long tasks, maintain the global plan and end goal. Final handoffs must state the result, validation performed, remaining risks, outstanding work, and required user input.

## Evidence, Review, and Decisions

- Base repository-specific claims on inspected code, tests, configuration, current state, and relevant history. Cite exact evidence when it matters.
- For third-party behavior, prefer official primary sources matching the project's current version. Use the latest stable guidance for upgrades and greenfield work, and call out version conflicts.
- Review the relevant scope systematically, prioritize findings by user impact and risk, explain the concrete failure or maintenance cost, and provide a safe path forward.
- Omit generic or purely cosmetic findings already covered reliably by tooling.
- For maintenance work, prefer targeted changes and established conventions. When explicitly asked to redesign, rewrite, or break compatibility, reason from first principles and do not treat compatibility or minimal change as hidden requirements.
- Do not overfit the first example. When the user corrects a decision criterion, apply it across the relevant scope.

## Dependencies and Platform Standards

- Do not reinvent standard parsing, networking, native, or operating-system capabilities.
- Prefer mature npm dependencies, weighing maintenance activity, adoption, de facto standard status, developer reputation, security, size, and compatibility.
- Follow the latest official API documentation for the dependency or SDK version in use. Do not use deprecated APIs.
- Frontend implementations must follow MDN, ECMAScript, and relevant Web standards.
- TypeScript must use the latest stable TC39 syntax and APIs supported by the project's Node.js version.

## Design and Code Standards

- Follow first principles, KISS, and DRY.
- Make every source of complexity justify itself. Prefer simple, self-explanatory code and a small number of coherent abstractions.
- Abstract and reuse highly related logic when it represents the same stable concept. Superficial similarity alone does not justify an abstraction.
- Before keeping a helper, layer, special case, or abstraction, identify the concrete problem that would appear if it were removed, inlined, renamed, or simplified.
- Follow existing conventions for filenames, directory structure, and code organization. Avoid duplication and unnecessary layers.
- Identifiers must be accurate, concise, and consistently styled. Avoid unnecessary aliases.
- Comments must use professional English and explain only non-obvious rationale, invariants, safety constraints, or external quirks. Do not restate the code.
- Keep individual files under 500 lines where practical. Split by responsibility and cohesion, not mechanically.
- Evaluate public APIs from the caller's perspective, including discoverability, misuse resistance, error semantics, configuration, and evolution.
- Public API documentation must describe observable contracts rather than incidental implementation details.
- Compare relevant industry practices with local conventions and explain deliberate deviations.

## Tests and Validation

- Keep agent-generated test artifacts, logs, audit evidence, and backups in an ignored, project-specific temporary directory. Never use `~/Downloads` unless the user explicitly requests it.
- Add tests for realistic observable regressions, non-trivial invariants, boundaries, and concrete bugs.
- Code changes or increased coverage alone are not sufficient justification for a new test.
- Prefer extending existing coverage at the behavior boundary.
- Avoid tests that mirror literals, static mappings, obvious control flow, or implementation details, unless the absence of a removed feature is itself a contract.
- For concurrency, prefer deterministic coordination or controlled scheduling over `sleep`.
- Before committing, ensure all relevant tests and pre-commit checks pass.

## Git Standards

- gh stack is all my needs
- Prefix new branches, worktree names, and pull request titles with a clear type such as `feat/`, `fix/`, `perf/`, `refactor/`, or `chore/`.
- Keep every commit coherent, independently reviewable, and free of unrelated changes.
- Commit and pull request descriptions must accurately explain the changes and relevant context.
- Never force-push unless explicitly asked to rewrite the published history of the specific branch. If a normal push is rejected as non-fast-forward, report it instead of forcing.
- Never merge a pull request or enable auto-merge without explicit authorization for that specific pull request. Green CI, approval, or a request to continue does not authorize merging.
- When commits are requested, report the commit hash and validation performed.
