# Core Review and Simplification

Use this reference for reviews and comprehensive simplifications.

## Rule Basis

Classify the basis of each conclusion:

- `standard`: ECMAScript, WHATWG, W3C, WCAG, protocol, or other normative requirement.
- `runtime-contract`: Verified behavior of the installed runtime, framework, SDK, dependency, or platform.
- `measured`: Reproduction, trace, profile, benchmark, RUM, logs, screenshots, or other observable evidence.
- `project-rule`: Explicit repository instruction, public API, migration contract, or project-owned convention.
- `preference`: zhsama's stable engineering preference where multiple correct choices remain.

Use severity only for review findings with a concrete correctness, security, performance, architecture, or maintenance impact. Put pure `preference` comments in a separate non-blocking section. In simplification, use preferences to choose among behaviorally equivalent alternatives rather than as authority to change a contract.

Use `project-rule` only after reading the exact repository instruction or project-owned contract, and cite that source in the finding. Keep a stable personal preference classified as `preference` when no project rule adopts it. When the defect and proposed remedy have different bases, identify both instead of relabeling the remedy as the defect's basis.

## Evidence Discipline

- Read the target and enough surrounding code to identify ownership and existing capabilities.
- Separate observed facts, inferences, assumptions, and recommendations.
- Prefer exact file/line references, diff hunks, API contracts, traces, and command output over generic judgment.
- Do not claim a command, test, screenshot, build, or benchmark passed without seeing or producing its output.
- Treat missing evidence as a validation gap, not automatically as a defect.

## Minimality Pass

Prefer less owned complexity when correctness, security, accessibility, observability, compatibility, and required behavior are preserved.

For each non-trivial mechanism:

1. Ask whether the requirement can be deleted, narrowed, or deferred.
2. Search for an existing repository capability with the same semantics.
3. Compare the language/runtime standard, platform/framework capability, installed dependencies, mature new dependencies, and a direct implementation.
4. Choose by semantic fit, correctness, interoperability, maintenance, security, supply-chain cost, bundle/runtime cost, and support matrix.
5. If new code remains necessary, require the smallest clear implementation that preserves the contract.

Do not stop at the first technically possible option. A platform API, installed dependency, or shorter implementation is not automatically the best total-cost choice.

## Complexity Tags

| Tag | Use when |
| --- | --- |
| `delete` | A behavior, branch, wrapper, compatibility path, or config does not need to exist. |
| `reuse` | The repository already owns the same semantic capability. |
| `platform` | A verified language, runtime, browser, framework, database, OS, or native capability is the better owner. |
| `dependency` | A maintained dependency or official SDK removes fragile owned behavior at acceptable cost. |
| `yagni` | A mechanism serves only a hypothetical future and owns no present contract or volatile boundary. |
| `shrink` | Required behavior can be expressed with fewer concepts or states without losing clarity. |
| `contract` | A fallback, duplicate rule, adapter, cast, or normalizer hides a violated invariant. |

## Contracts and Recovery

- Define trust by runtime boundary, validation, and versioned contract, not by whether a system is internally owned.
- Validate untrusted input at the owning boundary, then keep the validated internal contract strict.
- Flag fallbacks that make invalid required data look valid.
- Accept deliberate product defaults, cache misses, feature detection, graceful degradation, retries, migrations, and external recovery when their semantics are explicit.
- Catch errors where code can shape a response, retry, cancel, clean up, add operational context, or translate an external failure.
- Do not catch errors merely to log and return `null`, `undefined`, an empty collection, placeholder success, or stale data without declared semantics.

## Severity

- `Critical`: security compromise, data loss, destructive behavior, or a release/core workflow blocker.
- `High`: likely user-facing bug, broken invariant, incorrect API contract, severe boundary violation, or major measured regression.
- `Medium`: meaningful maintainability risk, unclear ownership, risky dependency, weak validation strategy, or probable non-happy-path failure.
- `Low`: contained cleanup, naming, local consistency, documentation, or minor maintainability issue with a concrete impact.

Do not increase severity because a choice is personally disliked.
