# Stacked Pull Requests

Use `gh stack` when the user requests stacked PRs. Do not replace it with a different stack manager or a set of manually connected ordinary PRs. If it is unavailable, explain the missing capability and complete useful local preparation without pretending the stack exists.

## Inspect Before Mutating

Read `gh stack --help` and the relevant subcommand help. Inspect `gh stack view`, the trunk, layer order, local/remote tips, open PRs, and any uncommitted work. Record which layer owns each change and which branches the authorized operation may affect.

For each layer, use its actual parent as the comparison base. Review and describe `merge-base(parent, head)...head`, not the cumulative stack against trunk. Keep shared prerequisites below their consumers.

## Operation Boundaries

| Command | Effect to account for |
| --- | --- |
| `gh stack view` | Inspect the current stack. |
| `gh stack init`, `gh stack add` | Create or register the local stack and its branches. |
| `gh stack submit` | Push branches, create/update PRs, update bases, and link the stack. Inspect all affected layers first. |
| `gh stack rebase` | Rebase layers onto their parents; this can rewrite commits on multiple branches. |
| `gh stack push` | Publish stack branches; the installed version may use force-with-lease and partially succeed. |
| `gh stack sync` | Fetch, rebase, push, and synchronize PR state; it is not a read-only refresh. |
| `gh stack merge` | Merge PRs; requires explicit authorization for the specific PRs or named stack. |

The inspected `gh stack` 0.2.0 uses force-with-lease in `push` and `sync`. A lease protects against an unexpected remote tip; it does not authorize rewriting history. Check the installed version's behavior, and obtain authorization for the specific published branches before any command that would rewrite them. If the command cannot stay within the allowed operation, stop that mutation and explain the limit. Do not work around it with a different force-push command.

## Create or Update a Stack

Create coherent typed branches and commits, then register or extend the stack using `gh stack`. Prepare the title and body for every PR being published. Use the installed command's supported non-interactive or editor flow and verify the resulting draft state rather than assuming a default. If titles/bodies are generated automatically, update them to the reviewed descriptions through supported GitHub operations.

Keep review fixes in the owning layer. Adding a new top layer is appropriate for a genuinely separate change, not to hide an incomplete lower layer. If fixing a lower layer requires rewriting already published descendants, make that consequence and the affected branches explicit before proceeding.

Before rebasing or resolving conflicts, record the affected tips. Preserve valid changes from both sides and check parent/child diffs after resolution. Do not claim a top-layer test proves that each intermediate layer builds independently; verify the layers whose behavior or dependencies changed.

After publication, read back every affected PR's base, head, title, body, draft state, and stack links. Confirm review fixes still appear in the correct layer. Report any partial push/update and the exact layers that remain. Leave merging and auto-merge alone unless separately authorized.
