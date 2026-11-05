# Commits

## Prepare the Exact Change

Read status, the staged and unstaged diffs, relevant untracked files, and the recent commit convention. Identify the authorized change before staging. Stage explicit paths or hunks when other work is present; do not sweep unrelated files into the commit.

Keep each commit coherent and independently reviewable. Separate unrelated fixes and dependency changes. Keep the production change, its regression test, and required documentation together when they establish one behavior. Split or reorder unpublished commits only when organizing history is in scope; do not silently rewrite published commits.

## Validate and Commit

Run the checks required by the repository and the focused checks that exercise the changed behavior. Inspect the final staged diff and run `git diff --cached --check`. Do not disable hooks or weaken checks to get a commit through.

When formatting or hooks change files, inspect those changes, preserve any unstaged work, and ensure the relevant validation covers the final staged content. Reuse valid observations for unchanged content instead of repeating every expensive check without cause.

Use a concise message explaining the change and its reason, following the repository's convention. After committing, inspect the commit's changed paths and worktree status. Report the hash and the actual validation performed. A commit request alone does not authorize a push.

## Push

Check the target remote and branch and whether a PR already exists. Use a normal push for new commits. If the remote has advanced, inspect the divergence and report the reconciliation needed; do not discard remote work or force a rejected push.

For a stack, read [Stacks](stacks.md) before publishing. Some `gh stack` commands use force-with-lease internally even when their names sound like an ordinary push or sync.
