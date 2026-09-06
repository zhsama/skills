# Testing and Validation

## Risk-Based Tests

Follow the current project's explicit test policy. When no policy overrides it, choose the smallest test level that proves the relevant behavior:

- Unit or property tests for pure algorithms and domain transformations.
- Integration or contract tests for schemas, databases, RPC, filesystems, queues, caches, SDKs, and runtime boundaries.
- Component tests for user-visible UI behavior and accessibility contracts.
- End-to-end tests for critical user workflows and cross-boundary integration.
- Type tests for public TypeScript API behavior and declaration contracts.
- Visual, browser, device, or platform tests for rendering and native behavior.
- Reproducible benchmarks, traces, or regression budgets for performance changes.

Do not prefer a larger test level when a smaller one proves the contract more reliably, and do not use a small helper test when the risk lives across a boundary.

## Test Quality

- Assert observable behavior, contract, state transition, or user-visible output rather than incidental implementation details.
- Keep tests isolated and independently reproducible.
- Prefer user-facing roles, labels, text, and explicit test contracts over CSS selectors or internal function names in UI tests.
- Avoid fixtures that hardcode a one-off return merely to satisfy the current implementation.
- Use deterministic clocks, random seeds, and data ownership when time or ordering matters.
- Add a failing reproduction before a testable bug fix when practical.
- Match edge coverage to the actual failure mode: large data, streaming, rapid input, slow network, cancellation, retry, cache staleness, concurrency, or real devices.

## Validation Claims

- Run affected tests first, then the repository's required lint, typecheck, build, integration, or e2e validation.
- For behavior-preserving simplification, capture the closest relevant baseline when practical and rerun the same observation after editing.
- Report exact commands and outcomes without dumping full logs unless requested.
- Do not say validation passed if it was not run or its output was not observed.
- Record unrun tests, unsupported platforms, missing screenshots, absent traces, and unavailable environments as validation gaps.
- For refactors, validate public imports, package exports, generated artifacts, route/registry invariants, and stale paths in addition to runtime behavior.
- For dependency upgrades, validate the migration guide, breaking changes, affected usage, lockfile, declarations, build output, and runtime matrix.
