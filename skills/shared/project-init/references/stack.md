# Stack Choices

Treat these preferences as starting points, not mandatory templates. Add conditional dependencies only when the product requires the capability they own.

## Defaults and Conditional Choices

| Area | Preferred starting point | Decision boundary |
| --- | --- | --- |
| Runtime | A current supported Node.js release; TypeScript and ESM | Verify compatibility across the chosen packages and deployment target. Do not inherit another project's exact version range. |
| Web UI | React with Vite+ | A browser application can start as an SPA. Select SSR or a full-stack framework when rendering, routing, SEO, or deployment requirements justify it. Existing Next.js usage is not a greenfield default. |
| UI primitives | Base UI when accessible complex controls are needed | Reuse the existing design system first. A button or static page does not require a component framework. |
| Styling | Tailwind CSS for utility-based UI; StyleX for a design system that benefits from compiled typed styles | Choose one primary styling system for the new surface. |
| Server state | TanStack Query when shared caching and asynchronous request state are needed | Do not duplicate query data in a second client store. Small local UI state stays in React until a wider state owner is justified. |
| Navigation and URL state | React Router for an SPA; nuqs for typed URL state when useful | Confirm the router adapter and runtime support. Do not install URL-state infrastructure for a page with no URL-state contract. |
| Runtime type validation | Validate untrusted inputs at their owning boundary and derive types from the schema when possible | No default schema library. Choose a compatible maintained solution, or use the project's existing one. Do not install competing schema libraries for the same contract. |
| Forms | React Hook Form for forms needing substantial field state and validation | Use the selected schema's supported integration. A simple native form may need no form library. |
| Persistence | Drizzle for a typed SQL layer when a database is needed | PostgreSQL fits shared service data; SQLite fits local or single-instance storage. Choose from the persistence contract, not the starter checklist. |
| Node HTTP | A maintained server framework matching the service (such as Hono or Fastify) | Choose from the service contract; do not turn every frontend into a separate API service. |
| Auth | An established identity integration with a clear owner (such as Better Auth or Ory) | Choose from the required identity and protocol contract; avoid scaffolding both or inventing authentication. |
| AI features | A maintained provider SDK or AI SDK when model calls are part of the product | Keep provider secrets on the appropriate server/native boundary. Do not install AI dependencies for an ordinary application. |
| Icons, motion, and i18n | Existing design tokens; Lucide or the established icon set; platform CSS for simple motion; a maintained i18n integration | Add Motion or an i18n framework when the product needs it. Preserve the chosen renderer and localization ownership. |
| Desktop and mobile | Electron or Expo/React Native when those targets are explicitly requested | Native integration and platform-native capabilities take priority over a web workaround. Do not create unused platform packages. |
| Tests | `vp test`; Testing Library, MSW, and Playwright where their behavior boundary is needed | Unit tests cover logic; DOM tests cover ordinary interactions; real browsers cover layout, focus, and browser contracts. Avoid testing the same scenario in every layer. |

## Project Structure

A single application can start with `src/`, its entrypoint, and feature-local modules. A server entrypoint may live under `src/server/` while the project is small. Split browser and server compiler/runtime contexts even if they share one package.

Use a workspace when applications or shared packages have real separate ownership. The familiar `apps/*` and `packages/*` layout is suitable then. Do not pre-create empty `types`, `constants`, `utils`, `services`, or infrastructure packages.

Use `vp run` for task orchestration first. Existing repositories may retain Turborepo; introduce another task runner only for a concrete unmet need. Avoid parallel runners owning the same task graph.

For a published library, define explicit exports, the supported runtimes, declaration output, and a consumer check. Set `sideEffects: false` only when the package is actually free of import-time side effects. Applications do not need release tooling merely because the library template has it.

## Dependency Decisions

Prefer standard platform capabilities and mature ecosystem packages for parsing, networking, native integration, and protocols. Compare maintenance, adoption, compatibility, installed/runtime cost, and the edge cases the package owns. Do not replace a well-maintained parser with a small custom implementation just to reduce the dependency count.

Keep version-sensitive details in project configuration, not permanent skill rules. For type checking, consider the supported native TypeScript checker or `tsrs` only after checking diagnostics, generated types, declaration needs, and compiler API consumers. A faster checker is not automatically a replacement for the compiler API used by other tools.
