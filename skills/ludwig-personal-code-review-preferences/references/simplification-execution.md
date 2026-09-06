# Behavior-Preserving Simplification

Use this reference for every `simplify` objective.

## Definition

Reduce the behavior a maintainer must hold in mind by removing owned concepts, mutable states, sources of truth, dependencies, branches, compatibility paths, or misplaced responsibilities. Preserve observable behavior and public contracts; line count is not the success measure.

Use the rule basis from `core-review.md`:

- Treat current user instructions, project rules, standards, and verified runtime contracts as gates.
- Require measured evidence for optimization claims.
- Use Ludwig's preferences to select among safe, contract-preserving alternatives.

Calling code "functionally correct" selects the quality objective; it does not replace equivalence evidence or validation.

## Target and Behavior Baseline

1. Capture the explicit target and current worktree state. Include staged, unstaged, and untracked target files when the workspace is implied.
2. Read enough callers, callees, tests, schemas, types, public exports, and documentation to state the behavior being preserved.
3. Record the applicable contract dimensions:
   - Inputs, outputs, serialization, and data shape.
   - Error, fallback, recovery, retry, and logging semantics.
   - Side-effect count and ordering.
   - Async ordering, cancellation, cleanup, concurrency, and streaming behavior.
   - State identity, rendering, lifecycle, accessibility, and user-visible behavior.
   - Public types, exports, package boundaries, and supported runtimes.
4. Search the repository read-only for reuse and the owning boundary. Keep writes inside the authorized target; surface an out-of-scope owner change instead of silently expanding the edit.

Complete the baseline when every candidate can name the contract it must preserve and the evidence available to check it.

## Four Independent Passes

Run every pass against the same target, diff, repository rules, and behavior baseline.

### Reuse

Find an existing repository capability with the same semantics. Consider a verified language, platform, framework, or dependency capability when it reduces total owned complexity. Accept reuse only when the semantic contract and ownership match.

### Simplification

Find redundant or derivable state, duplicate sources of truth, dead paths, deep control flow, forwarding wrappers, unused options, speculative extensibility, and compatibility code without a current contract. Name the direct form that performs the same job with fewer concepts.

### Efficiency

Find provably redundant computation, parsing, serialization, I/O, allocation, subscriptions, and retained environments. Distinguish removing objectively duplicate work from claiming a measured performance improvement. Treat reordering, concurrency, caching, memoization, and scheduling as contract-sensitive changes.

### Altitude and Ownership

Find rules enforced below or above their proper owner, caller-side repairs, repeated special cases, leaked runtime details, wide public surfaces, and abstractions that do not own an invariant or volatile boundary. Prefer the smallest owner-level correction that remains inside the authorized scope.

## Apply Domain Preferences

- Load `simplicity-and-architecture.md` and use its Clean-Code Standard and Ownership Pass for every candidate.
- For TypeScript or schema changes, load `typescript-toolchain.md`; preserve type honesty and keep validation at the owning runtime boundary.
- For React or web changes, load `react-and-web.md`; verify state derivation, effect purpose, identity, lifecycle, browser support, and accessibility semantics.
- For dependency, parser, protocol, native, or OS changes, load `dependencies-and-runtime.md`; compare semantic fit and total dependency cost before replacement.
- For efficiency candidates, load `performance.md`; describe structural work removal accurately and reserve optimization claims for measured results.
- Load repository-specific rules as hard constraints. Keep repository-only policies out of these cross-project references.

## Candidate Record

Return one record per candidate:

- Lens and exact location.
- Current concrete complexity cost.
- Proposed simpler form.
- Owned concepts, states, sources of truth, dependencies, or paths removed.
- Behavior-equivalence basis.
- Rule basis and applicable complexity tags.
- Required write scope and owner.
- Validation method and residual risk.

Pure taste, line-count reduction, and syntax similarity are insufficient costs.

## Independent Discovery and One Writer

When agent delegation is allowed and available, assign the four passes to independent read-only reviewers and launch them concurrently up to the available capacity. Give each reviewer the same baseline and exactly one lens. Require candidate records and prohibit project-file edits.

Keep the main agent as the sole writer. Run any undispatched pass locally or in a later wave. If independent agents are unavailable, run all four passes sequentially and disclose the fallback in the final response.

Complete discovery when all four passes returned or were executed sequentially, including passes that found no candidate.

## Preference and Equivalence Gate

Apply a candidate only when all conditions hold:

1. It removes a concrete form of owned complexity.
2. Its behavior-equivalence basis covers every affected contract dimension.
3. It follows current user instructions, repository rules, standards, and verified runtime contracts.
4. It uses semantic DRY and the correct owner rather than joining code that only looks similar.
5. It introduces no speculative abstraction or unjustified dependency.
6. Its write scope is authorized and does not overwrite unrelated worktree changes.
7. Its validation is proportionate to the affected behavior.
8. It does not conflict with another accepted candidate.

Move candidates with a possible behavior, API, schema, error, ordering, accessibility, or compatibility change to an incidental review section. Apply them only under a separately authorized review/fix or implementation objective.

## Editing and Validation

1. Deduplicate candidates and order accepted changes by dependency.
2. Apply the smallest coherent changes sequentially.
3. Inspect the diff after each contract-sensitive batch and remove stale imports, exports, paths, configs, and generated references caused by the edit.
4. Run affected validation in the repository's required order. Reuse the baseline observation when practical.
5. Inspect the final status and diff for scope, contract preservation, and unrelated modifications.

Complete simplification when every accepted candidate was applied or explicitly skipped, every changed behavior surface has an observed validation result or named gap, and the final diff contains only authorized cleanup.
