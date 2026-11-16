# TypeScript Configuration

Use a strict, explicit configuration matched to the actual runtime. Do not apply one browser-bundler configuration to every artifact.

## Common Decisions

- Enable `strict` and keep the package's ESM intent explicit.
- Set `target` and `lib` from supported runtimes. `ESNext` is a decision about the build pipeline and deployment target, not an automatic compatibility promise.
- Scope `include` and global `types` to the project. Browser code should not accidentally obtain Node or test-only globals.
- Use `verbatimModuleSyntax` and explicit type imports when supported by the selected compiler and transform pipeline.
- Use `isolatedModules` for code processed one file at a time. Enable JSON module support only when used.
- For application checks, `skipLibCheck` can avoid repeatedly checking dependency declarations. It does not prove library consumer compatibility; inspect duplicate or conflicting dependency types rather than masking them.

## Runtime Profiles

| Artifact | Configuration direction | Verification |
| --- | --- | --- |
| Bundled React app | Compatible ESM module mode, `moduleResolution: "bundler"`, DOM libs, `jsx: "react-jsx"`, `noEmit: true` | Static checks plus the actual application build. |
| Node service or CLI | The Node module mode and resolution supported by the chosen runtime/compiler; Node types without DOM globals | Run the built output, or the documented direct-TypeScript execution path, in the target Node runtime. |
| Published library | Settings matching the emitted module format and supported consumers; declaration generation as needed | Package exports, declaration output, and consumer imports. Bundler resolution alone does not validate unbundled Node consumers. |
| Mixed browser/Node/test project | A small shared base plus environment-specific configurations | Check each real project and its generated inputs. Add project references only when they model an actual dependency graph. |

Start with the official framework/Vite+ template and adjust these decisions. Do not copy obsolete compiler flags or add a second checker without a coverage gap it solves.

If a framework generates types, generate them before the check that consumes them. Separate type checking, declaration generation, and compiler API compatibility when selecting tools. Do not claim that a successful bundle proves type safety.

## Imports and Aliases

Use explicit imports. Keep nearby imports relative. A single application-root alias is reasonable when it improves navigation; it is not mandatory for a small package.

When an alias exists, give its mapping one authoritative configuration and use supported tooling to consume it across the compiler, bundler, and tests. Verify runtime resolution as well as editor resolution. TypeScript `paths` alone does not make an emitted Node import resolve.

Use package exports and workspace dependencies across package boundaries instead of aliases into another package's private source. Avoid config modules that silently rewrite tsconfig files when imported. If a mapping must be generated, make generation an explicit task.

Keep private types and constants beside their behavior. Extract shared contracts or independently owned concepts when there is a real consumer or responsibility boundary. Derive types from schemas or existing declarations where that preserves the contract; avoid a parallel handwritten copy.

## Authoritative References

- [TypeScript: choosing compiler options](https://www.typescriptlang.org/docs/handbook/modules/guides/choosing-compiler-options.html)
- [Vite+ static checks](https://viteplus.dev/guide/check)
- [Vite+ package management](https://viteplus.dev/guide/package-management)

Read the documentation for the versions being installed before choosing exact flags or integrations.
