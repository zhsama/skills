# Simplification Candidates

Use this checklist to inspect the requested diff or code. State the change's purpose and the behavior to preserve first. For each relevant piece, consider removing, inlining, or merging it and identify what would concretely break. A written checklist is not required for a small change.

## Contract and Ownership

Begin with the behavior's owner and its real consumers. Identify which part of the proposed cleanup would reduce a maintenance obligation: keeping two representations synchronized, tracing a value through forwarding layers, or coordinating a rule across unrelated owners. A candidate needs a concrete explanation of that reduction and the behavior that must remain observable.

Check the candidate against zhsama's existing standards. Keep meaningful domain names and responsibility boundaries even when they have one caller. Share logic when consumers depend on the same rule; similar syntax and a repetition count do not establish that relationship. Preserve options, state, and generic types that actual consumers need, and question those added only for hypothetical uses.

Follow inputs and failure paths before removing checks. A TypeScript annotation does not establish trust at an external boundary. Prefer existing platform or package capabilities for parsing, networking, and native integration; count the obligations a replacement would introduce, not just the dependency it would remove. Assess tests by the regression they detect, and preserve unrelated work outside the authorized cleanup.

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
