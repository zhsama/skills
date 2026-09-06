# TypeScript and Toolchain

## Compatibility First

- Inspect the installed TypeScript version, Node/browser targets, framework compiler, bundler, lint parser, editor plugins, and declaration tooling before recommending an upgrade or API.
- Prefer the newest stable version supported by the complete toolchain, not the numerically newest package in isolation.
- Match `target`, `lib`, `module`, and `moduleResolution` to the actual runtime and build pipeline.
- Distinguish application settings from published-library settings. Validate emitted JavaScript, declarations, exports, and consumer compatibility for libraries.
- Treat Stage 4 ECMAScript features as standardized, but still verify runtime availability or transpilation. Treat earlier proposals as explicit experimental choices.

## Type Honesty

- Keep `strict` type checking enabled unless a documented migration constraint prevents it.
- Prefer `unknown` for genuinely unknown values until narrowed or parsed.
- Flag `any` when it erases or spreads an unverified public, domain, or runtime contract. Allow only narrow, isolated compatibility or migration exceptions with a concrete reason.
- Prefer discriminated unions for state variants that have different payloads.
- Keep required business invariants required. Do not add compiler-only fallbacks.
- Give every optional or nullable value a defined absence meaning.
- Flag forced assertions and non-null assertions that replace missing proof.

## Type Shapes

- Use `type` for unions, tuples, mapped/conditional types, aliases, and compositions that benefit from those features.
- Use `interface` when declaration merging, public object extension, or `extends` composition is the clearer or more compiler-efficient contract.
- Prefer `interface extends` over large object intersections when it produces a flatter, conflict-checked type.
- Use const objects or enums according to runtime behavior, interoperability, declaration output, and project convention. Do not treat either syntax as universally wrong.
- Flag `Pick` and `Omit` only when they hide the real domain contract, create accidental coupling, or make ownership unclear.
- Add explicit exported return types when they stabilize a public/declaration surface or improve a measured compiler hotspot; do not annotate trivial locals mechanically.

## Runtime Schemas and Parsing

- Default to Zod for TypeScript runtime schema definition, parsing, validation, and type inference at untrusted boundaries. Zod is the preferred de facto ecosystem choice.
- Reuse a project-owned equivalent schema layer when replacing it with Zod would create two competing contract systems or violate an explicit project rule.
- Parse HTTP/RPC payloads, messages, environment variables, configuration, storage, files, database/SDK results, and other untrusted runtime input at the owning boundary.
- Do not parse or normalize already validated internal values again.
- Derive TypeScript types from the owning Zod schema when the schema is the runtime source of truth. Avoid parallel handwritten types that can drift.
- Do not use Zod to hand-roll parsers for standard formats; first use the canonical platform parser or a maintained format library, then validate the parsed shape with Zod when needed.

## Compiler and Lint Performance

- Measure typecheck and lint performance before restructuring types or projects.
- Investigate wide `include` patterns, uncontrolled global `types`, duplicate project loading, declaration emit, and editor/plugin overhead.
- Inspect large unions, intersections, conditional types, anonymous inferred declaration types, and repeatedly instantiated generics when traces identify type-system cost.
- Use named types, suitable annotations, incremental builds, or project references when evidence supports them.
- Prefer type-aware linting for high-value correctness rules, but account for its typecheck-like cost.
- Do not run expensive formatter behavior inside lint when separate formatting checks avoid duplicate parsing.
