# Simplification Candidates

Use this checklist to inspect the requested diff or code. State the change's purpose and the behavior to preserve first. For each relevant piece, consider removing, inlining, or merging it and identify what would concretely break. A written checklist is not required for a small change.

## Candidate Inventory

| Piece | Simpler form to consider | Reason to retain it |
| --- | --- | --- |
| Helper or wrapper | Inline or call the underlying API directly | It names a meaningful step, owns an invariant, or isolates a real volatile boundary. One caller alone does not disqualify it. |
| Parameter, option, or generic | Use the actual invariant or an existing type | A real caller, public contract, or supported variation needs it. |
| State, flag, or cache | Derive from the authoritative value | Independent identity, lifecycle, or measured work justifies storage. |
| Branch, guard, or recovery path | Remove an unreachable or redundant path | A reachable input or failure needs it. Static types alone do not validate external input. |
| File or module | Colocate with its owner or combine one responsibility | A distinct runtime, lifecycle, public contract, or cohesive responsibility justifies the boundary. |
| Dependency or custom utility | Reuse the platform or an existing maintained capability | It owns real edge cases or reduces total complexity. Do not hand-roll parsing, networking, or native behavior to shrink a manifest. |
| Repeated logic | Share the stable semantic rule | Similar syntax with different contracts or owners should remain separate. There is no fixed repetition threshold. |
| Comment or documentation | Delete narration and stale explanation | It records a non-obvious reason, invariant, external quirk, or required public contract. |
| Test | Remove redundant implementation assertions | It protects an observable regression or contract not otherwise checked. Passing remaining tests does not prove equivalent coverage. |
| Unrelated change | Leave it out of the proposed cleanup | Preserve unrelated user work; do not revert their edits merely to make the diff smaller. |

## Source Organization

- **Comments:** keep professional English explanations of reasons and constraints. Remove comments that narrate the code, but preserve licenses, required directives, and necessary API documentation. Do not add environment-marker comments when the module boundary already makes the runtime clear.
- **Types:** keep private types beside their behavior. Extract to `types.ts` or a cohesive contract module when sharing or independent ownership warrants it. Derive from an owning schema or declaration instead of maintaining duplicate shapes. Avoid mechanical return annotations, exported private types, and a catch-all types file.
- **Constants:** colocate a value with its single owner. Extract a domain constant when consumers share the same invariant or configuration ownership. Do not centralize unrelated literals, turn every literal into a constant, or inline protocol/configuration values that need a name or separate owner.
- **Aliases and imports:** use explicit, traceable imports and preserve established project aliases. Add an alias only for a concrete navigation or boundary benefit. Keep its authoritative mapping consistent across compiler, build, test, and runtime resolution; prefer package exports across workspace packages. Avoid config-import side effects that rewrite other config files.
- **Moves and merges:** update the affected callers, exports, tests, and configuration together. A shorter file is not an improvement if it spreads one behavior across more places or exposes a private contract.

## Validation and Decisions

Apply accepted edits in coherent batches. Run focused behavioral checks and the relevant type/lint checks, plus any required repository checks. Repeat or broaden validation when the next edit changes the covered behavior or a failure leaves an unresolved concern.

Classify the evidence correctly:

- A behavior regression supports keeping the protection or finding another equivalent implementation.
- A compile/import failure may mean the candidate was incompletely applied; it does not prove the abstraction is necessary.
- An environment failure or missing behavioral coverage leaves the conclusion open.
- A passing test is evidence only for the behavior it exercises. Use caller/contract reasoning as well, and retain uncertain candidates as advice.

Report what complexity was removed or retained and why, with observed validation and remaining uncertainty. Diff size may add context, but it is not the objective or proof of correctness.
