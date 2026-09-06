# Performance

## Evidence Contract

Do not accept an optimization claim without:

1. A user, runtime, or developer-workflow scenario.
2. Representative device, runtime, network, and data scale.
3. A baseline and target metric.
4. A trace, profile, benchmark, RUM sample, bundle report, or reproducible measurement.
5. A bottleneck hypothesis tied to the measured layer.
6. Before/after results using the same method.
7. Correctness, memory, cache, cancellation, and stability regression checks.

Distinguish field from lab data, cold from warm behavior, and average from tail latency. Prefer percentiles for user-facing and service latency.

## Review Layers

| Layer | Inspect |
| --- | --- |
| Web UX | LCP, INP, CLS, real-user p75, navigation, input responsiveness, visual stability. |
| Browser | Request waterfalls, transfer, parse/execute, long tasks, style/layout/paint, DOM scale, memory, workers, resource priority. |
| React | Scheduler/Component tracks, Profiler commits, state/context scope, subscriptions, effect churn, Suspense, compiler coverage. |
| Node | Throughput, p50/p95/p99 latency, event-loop delay/utilization, CPU profiles, heap/GC, I/O concurrency, backpressure. |
| TypeScript | Cold/warm typecheck, declaration emit, editor latency, memory, lint timing, compiler traces, project loading. |
| Build/bundle | Cold/warm build, cache hit/correctness, entry/route chunks, duplicate dependencies, dead code, source maps. |

## General Findings

- Flag optimization without a measured bottleneck or user-visible/developer-visible goal.
- Flag changes that improve one metric while regressing correctness, memory, responsiveness, accessibility, cache invalidation, or stream semantics.
- Prefer algorithmic, data-flow, query, I/O, render-scope, and payload improvements before local syntax micro-optimizations.
- Treat cache, preload, speculative work, and memoization as state with invalidation and memory costs.
- Keep instrumentation at the lifecycle or boundary that owns the measured cost. Avoid high-cardinality or misleading metrics.

## Browser and React

- Use field Web Vitals where available; lab tools diagnose but do not replace real-user behavior.
- Investigate long main-thread tasks, layout thrashing, oversized DOM, late-discovered critical resources, and unnecessary JavaScript before adding scheduling workarounds.
- Use dynamic imports selectively: static imports support stronger analysis and initial dependency loading, while dynamic imports help genuinely deferred code.
- Do not use render counts as a performance result. Measure commit cost and interaction impact.

## Node and Streaming

- Keep request callbacks and event-loop work bounded. Investigate input-dependent CPU work and synchronous APIs on hot paths.
- Use worker threads for CPU-intensive JavaScript when measurement justifies the transfer and coordination cost; do not use them as an I/O default.
- Preserve stream backpressure, cancellation, error propagation, cleanup, and bounded buffering.
- Inspect event-loop delay/utilization, CPU, heap, GC, throughput, and tail latency together before assigning a bottleneck.

## Tooling

- Compare lint time with typecheck time before blaming individual typed rules.
- Use compiler diagnostics/traces to locate slow types rather than guessing from syntax.
- Narrow source inclusion and global types before adding project boundaries.
- Add project references, incremental work, concurrency, or caching only when the dependency graph and measurements support them.
