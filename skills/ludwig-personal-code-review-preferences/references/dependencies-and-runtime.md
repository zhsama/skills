# Dependencies and Runtime Boundaries

## Capability Choice

For parsing, HTTP, networking, sockets, protocols, native, OS, dates, MIME, semver, XML/HTML, CSV, URL, shell-like syntax, and SDK work:

- Do not hand-roll a standard format or protocol with regexes, string splitting, or an ad hoc state machine when a maintained canonical implementation exists.
- Prefer an official SDK for service-specific contracts when it is current, typed, maintained, and fits the runtime.
- Compare canonical platform APIs with mature dependencies instead of assuming either category always wins.
- Use a dependency when it owns complex compatibility, protocol, security, parsing, retry, pooling, or native behavior better than local code.
- Use a platform API when it fully satisfies the contract and removes dependency, interoperability, or security cost.
- Keep wrappers narrow: translate vendor types, errors, cancellation, retries, or configuration at the boundary rather than copying an entire SDK surface.

## Dependency Review

Evaluate:

- Exact semantic fit and API clarity.
- Maintenance activity, release cadence, issue and security response.
- Real adoption through downloads and dependents; do not use stars as the sole signal.
- Type quality and compatibility with the project's TypeScript, Node, browser, framework, ESM/CJS, and bundler matrix.
- Bundle/runtime cost, tree-shaking, side effects, native requirements, and transitive dependency graph.
- License, advisories, deprecated status, provenance, signatures, and release process.
- Migration guides, changelog quality, breaking changes, and lockfile/catalog/patch implications.

Explain why a new dependency is worth its total cost and why existing or platform capabilities are insufficient.

## Runtime and Package Contracts

- Prefer active LTS runtimes for production unless the project explicitly targets Current or experimental features.
- Verify API stability and deprecation status for the minimum supported runtime, not only the developer machine.
- Align TypeScript module settings with the runtime or bundler actually resolving modules.
- For published packages, inspect `type`, `exports`, conditional exports, declarations, source maps, supported engines, and consumer import behavior.
- Treat introduction or narrowing of package exports as a potential breaking change.
- Use npm provenance, trusted publishing, signatures, and audit information as supply-chain evidence, not as proof that code is safe.
- Keep cancellation, timeouts, retry limits, idempotency, connection lifecycle, and resource cleanup explicit at I/O boundaries.
