---
name: project-init
description: "Initialize a JavaScript/TypeScript app, service, CLI, or library using zhsama's preferred toolchain, or plan its initial structure and dependencies. Use for new projects and explicit starter requests; existing projects keep their conventions unless a migration is requested."
---

# Project Init

Turn the requested product into the smallest runnable project. These are personal defaults, not requirements to replace the user's chosen language, framework, or an existing project's architecture.

## Choose the Shape

1. Establish the target directory, product, runtime, and delivery requested: advice, local implementation, or publication. Inspect existing files before scaffolding into a directory.
2. Identify the real boundaries: browser, server, native app, or published package. Start with one package unless separate runtimes, consumers, or release ownership justify more.
3. Read [stack choices](references/stack.md) for dependency decisions and [TypeScript configuration](references/typescript.md) when setting up compilation or imports. Load only relevant sections.
4. Ask only about choices that materially change the product or architecture. State ordinary implementation assumptions and proceed within the authorized scope.

## Toolchain Defaults

- Use TypeScript and ESM for new JavaScript ecosystem code. Select current stable versions supported by the complete runtime, framework, plugins, and tooling; verify official documentation at initialization time instead of copying old project version pins.
- Use Vite+ as the toolchain entrypoint. Run tests through `vp test`, lint through `vp lint`, formatting through `vp fmt`, and project tasks through `vp run`. Use `vp build` for web applications and `vp pack` for library packaging when supported by the selected template.
- Use `vp install`, `vp add`, and `vp remove` for dependencies. Prefer pnpm underneath for a new project, pin it in `packageManager`, and keep one lockfile. Preserve the package manager of an existing workspace.
- Do not add `ni`, ESLint, Prettier, or a second standalone test CLI to the starter. Vitest APIs, browser providers, and coverage packages required by the selected Vite+ version are still valid dependencies.
- Keep lint, format, and test configuration in the supported Vite+ configuration. Keep TypeScript settings in the appropriate tsconfig files.
- Use `vp check` for static checks only after confirming which checks the selected version and configuration actually enable. Do not assume it covers tests, a production build, framework-generated types, or declarations.

## Initialize

Prefer the current official Vite+ scaffold over a hand-maintained copy of a framework template. Inspect `vp create --help` and the [creation guide](https://viteplus.dev/guide/create) for the installed version. Choose the application, library, or workspace template for the actual artifact, then remove unused example features.

If global `vp` is unavailable, use the documented package-manager bootstrap or the local `vp` binary. A global installation is not a prerequisite for creating a project.

Create only what the first working use case needs:

- A package manifest, one lockfile, runtime version declaration, and tool configuration.
- The real application or library entrypoint and a small initial feature.
- Scripts for development, build or packaging, static checks, and tests that actually exist.
- A concise README explaining the product, setup, commands, and required environment variables. Keep secrets out of examples.
- Ignore rules for generated output and a project-specific temporary directory such as `.local/`.

Keep source files together by feature and runtime. Add `apps/*` and `packages/*` only when the project has those separate owners. Use workspace dependencies and package exports for shared packages. Add catalogs when they remove repeated version ownership; preserve an existing catalog scheme rather than imposing named groups.

For local commit checks, prefer the supported `vp staged` and Vite+ hook setup. Inspect existing hooks first and preserve partially staged work. Follow the [hook guide](https://viteplus.dev/guide/commit-hooks) for the selected version; do not add another hook manager just to wrap Vite+. Inspect generated agent integration before accepting it.

## Verify and Deliver

Run the configured static checks and production build or package check. Exercise the first useful behavior through the appropriate test or smoke check. Add tests for real behavior, boundaries, or regressions; do not generate placeholder assertions to make the starter look tested.

For browser interactions, use a browser when layout, focus, or platform behavior needs verification. For services, verify the actual request path. For libraries, check exports, declarations, and an actual consumer import.

Report the chosen stack and why the conditional dependencies were needed, the files created, exact checks and outcomes, and any unverified runtime. Creating a local project does not authorize commits, remote publication, or deployment.
