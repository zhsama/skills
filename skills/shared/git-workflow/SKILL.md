---
name: git-workflow
description: "Handle Git and GitHub issues, commits, pull requests, review delivery, and stacked PRs using zhsama's workflow. Use gh stack for stacks and load only the reference for the requested operation. Analysis and description drafts stay read-only."
compatibility: "Local operations require Git. GitHub operations require repository access through GitHub CLI or a connector; stacked PR operations require gh stack."
---

# Git Workflow

Select the requested operation and its permission independently. A request to review, investigate, or propose does not authorize implementation or publication. Continue through already authorized work without asking again for routine steps.

## Inspect the Target

Confirm the repository, remotes, current branch, target base, worktree status, and relevant repository instructions. Include staged, unstaged, and untracked target files when reviewing local work. Preserve unrelated changes.

Prefix new branches, worktree names, and PR titles with a clear type such as `feat/`, `fix/`, `perf/`, `refactor/`, or `chore/`. Commit messages follow the repository's established convention.

Use the available GitHub connector for supported remote operations and GitHub CLI when the connector cannot perform them. The user's explicit `gh stack` preference takes precedence for stack operations. Check installed command help before relying on version-specific behavior.

## Load on Demand

| Request | Read |
| --- | --- |
| Investigate or solve an issue; triage issues or PRs | [Issues](references/issues.md) |
| Stage, commit, or organize local commits | [Commits](references/commits.md) |
| Prepare, open, or update a PR | [Pull requests](references/pull-requests.md) |
| Create, inspect, repair, or publish a PR stack | [Stacks](references/stacks.md), plus the commit/PR reference when needed |
| Review a diff or PR; handle review feedback | [Review](references/review.md) |

Do not load every reference for a single operation. Code-quality review may use `simplified` when it is available; the review reference also works without that skill. Use `issue-brief` for a requested learning-oriented issue selection and `issue-review-workflow` when the user requests that independent review and approval process, not for every ordinary issue.

## Authorization and Completion

- A request for a PR description produces text. A request to open a PR authorizes the necessary scoped commits and branch push unless the user restricts them. Preserve an explicitly requested draft state.
- Commit, push, label, close, comment, resolve a review thread, and submit a formal GitHub review only within the requested operation or an established authorization. A review in chat does not publish a review.
- Never merge or enable auto-merge without authorization for the specific PRs. Passing checks and approval do not supply it.
- Never force-push without explicit authorization to rewrite the published history of the specific branches, including force operations hidden inside a stack command. Report a rejected normal push instead of forcing it.
- Keep PR bodies, validation logs, patches, and screenshots in an ignored project-specific temporary directory. Do not commit PR-only evidence or use `~/Downloads` by default.
- Finish with the concrete result, commit/PR links when created, observed validation, remaining work, and any required user decision. Do not claim completion from commands that have not finished.
