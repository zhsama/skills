---
name: engineering-practices
description: Guide design, implementation, and review of JavaScript and TypeScript changes involving module contracts, UI state and styling, data access, or asynchronous side effects. Use when deciding where behavior belongs, how it can fail, and how to verify it.
---

# Engineering practices

Start with a real caller or user action. Trace it through the project's existing modules to the code that owns its state or side effects. Check nearby tests and project instructions for promises that callers already rely on.

| Decision in this change | Read |
| --- | --- |
| Where a rule lives, what a caller can assume, or how failures reach the caller | [General practices](references/general.md) |
| Which component owns a draft, how requests interact, or where a style takes effect | [Frontend practices](references/frontend.md) |
| How much work a request creates, which writes commit together, or how a worker recovers | [Backend practices](references/backend.md) |

Read the sections that affect the change. For example, a themed dialog usually needs the frontend styling section alone. A dialog that submits a retryable payment also needs the general outcome contract and the backend guidance on duplicate writes.

**During design**, settle the choices that would be expensive to reverse. Identify who enforces the rule, which outcomes callers can observe, how work grows with input, and one scenario that could disprove the design. A short explanation alongside the proposed change is usually enough.

**During implementation**, follow the contract through its real entry points. Match the approach to the repository's runtime, libraries, and existing public interfaces. Check version-sensitive behavior against the installed version and its official documentation.

**During review**, use the same scenario against the actual call path. Describe the input or sequence of events, the observable consequence, and the evidence. Keep a proposed fix within the requested scope.
