# Simplicity and Architecture

## Clean-Code Standard

Judge simplicity by the amount of behavior a reader must hold in mind, not by raw line count.

Prefer:

- Fewer concepts, mutable states, configuration paths, compatibility branches, and sources of truth.
- Cohesive modules whose code changes for the same reason.
- Explicit dependency direction and narrow public surfaces.
- Local reasoning: the code needed to understand a behavior stays near its owner.
- Direct code until an abstraction names a real concept, enforces a contract, removes semantic duplication, or isolates a volatile boundary.
- Comments that explain constraints, reasons, protocols, or non-obvious transitions rather than restating syntax.
- Precise, consistent names over either verbosity or artificial brevity.

Apply DRY to duplicated semantics and business rules, not merely similar syntax. Do not force together behaviors with different owners or change reasons.

Treat file size as an investigation signal. Split when a file mixes unrelated responsibilities, state machines, runtimes, lifecycles, or change directions; do not split only to meet a line threshold.

## Ownership Pass

Identify:

1. The behavior and invariant being reviewed.
2. The module, package, runtime, schema, service, store, adapter, or component that can enforce it for every caller.
3. The allowed dependency direction.
4. The public API and private implementation surface.
5. The validation and migration boundary.

Flag caller-side repairs when the owning boundary can enforce the rule once. Flag duplicate contracts across runtimes when they must remain synchronized but have no single source or invariant test.

## Module and Package Boundaries

- Classify the artifact first: application, Node service, browser app, CLI, npm library, monorepo package, or cross-runtime package.
- Organize by ownership and change cohesion. Feature-first, layer-first, and runtime-first structures are all valid when they reflect real dependency direction.
- Avoid generic `utils`, `helpers`, `common`, or god-service owners that collect unrelated semantics.
- Keep platform APIs and I/O at explicit boundaries when this improves portability and testability.
- Cross-package consumers should use declared public entry points rather than private deep imports.
- Prefer explicit package exports when they make the public contract reviewable. Do not ban every barrel; judge whether it preserves an intentional API.
- Extract a package only for a real independent owner, runtime/configuration need, reuse boundary, release boundary, or measured tooling benefit.
- Use project references when they model a real project graph and improve measured build/editor behavior, not as automatic monorepo ceremony.

## Abstractions

One caller or implementation is evidence to inspect, not proof of YAGNI. A single implementation may still justify a contract when it:

- Defines a public API.
- Isolates a third-party SDK, transport, database, filesystem, worker, native, or platform boundary.
- Owns a business invariant or state transition.
- Prevents callers from depending on volatile details.
- Improves TypeScript object composition or declaration surfaces.

Inline abstractions that only forward calls, rename values, expose unused options, or serve hypothetical extensibility without owning a contract.

## Refactoring

- State the current pain, target boundary, dependency direction, risks, and validation before moving code.
- Separate mechanical moves from behavior changes when that materially improves review safety.
- Avoid line-range extraction that preserves the same transitive dependency bag.
- Keep compatibility only at real external/public boundaries and remove it after the migration window.
- Search for stale imports, exports, configs, stories, tests, generated artifacts, and old paths after moves.
- Judge success by reduced concepts, clearer ownership, smaller dependency surfaces, and preserved behavior rather than a flatter directory tree.
