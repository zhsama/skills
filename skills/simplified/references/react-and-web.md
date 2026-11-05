# React and Web

## React State and Effects

- Keep components and hooks pure during render. Do not mutate props, state, or non-local values while rendering.
- Derive render data directly from props and state instead of mirroring it into state.
- Handle user-caused actions in event handlers rather than effects.
- Use effects to synchronize React with external systems. Do not ban a valid external synchronization effect or use effects as a default business-flow mechanism.
- Keep state near its unique owner. Lift it to the closest common owner only when multiple consumers must coordinate.
- Use keys deliberately when identity should reset or preserve state.
- Use custom hooks to share or encapsulate stateful React logic, not as a destination for every non-trivial function.
- Use the framework or project data layer for server state, caching, cancellation, retries, and deduplication instead of rebuilding them inside components.

## React Performance

- Check whether React Compiler is enabled before recommending `memo`, `useMemo`, or `useCallback`.
- Do not require memoization merely because an object or function identity changes during render.
- Require Profiler, React Performance Tracks, trace, or a clear dependency semantic before treating manual memoization as a fix.
- Use `useTransition` or `useDeferredValue` to prioritize non-blocking updates when appropriate; do not claim they make the underlying computation faster.
- Review state/context scope, subscription granularity, effect churn, component identity, Suspense boundaries, and code/data waterfalls before micro-optimizing JSX.
- Lazy-load at meaningful route or feature boundaries when measurement shows initial transfer or execution cost; avoid fragmentation that creates extra waterfalls.

## Web Platform

- Verify browser APIs, CSS, HTML, and JavaScript behavior against current MDN/specification material and the project's browser/WebView support matrix.
- Use MDN Baseline as a compatibility signal, not a substitute for the actual supported runtimes, accessibility, performance, or device testing.
- Prefer semantic HTML and native controls before ARIA or JavaScript replicas.
- Review keyboard operation, focus order/restoration, labels, names, status announcements, contrast, target size, reduced motion, zoom, dynamic content, and overflow when relevant.
- Treat WCAG 2.2 as the default current accessibility reference unless the project declares another conformance target.
- Verify rendered output for meaningful UI changes across realistic content, viewport, interaction, and platform states.
