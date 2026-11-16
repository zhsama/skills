# Pull Requests

## Establish the Comparison

Read the repository's PR template, contribution rules, current status, remotes, and existing PRs for the branch. Determine the actual target branch and record the base/head revisions. For a stacked PR, target the parent layer and describe only this layer's diff.

Read the complete comparison, distinguishing source from generated files, lockfiles, and snapshots. Follow changed behavior to its callers and public boundaries. Review evidence against the final head; results from an older head cover only unchanged relevant content.

## Write for the Reviewer

Start with the concrete problem and resulting behavior. Explain why the approach fits when that is not obvious. Scale detail to the change: a small fix needs a few sentences, while a cross-module change may need a boundary diagram or migration notes.

Include:

- A typed title such as `fix/avoid duplicate submissions` or `feat/add project setup skills`.
- Linked issues with accurate semantics: `fixes`/`closes` only when the PR completes the issue, otherwise `refs`.
- Exact verification commands and observed outcomes, with assumptions and unverified behavior stated separately.
- The parent PR for a stack layer and any real rollout, compatibility, or review dependency.

Keep the repository template. Add sections only when they help explain the final implementation. Rewrite stale titles and descriptions when the scope changes. Omit abandoned approaches and conversational history unless they explain a material tradeoff.

For a bug, show the failing and repaired behavior under the same input when practical. For performance, compare the same workload and environment. For visible UI changes, capture appropriate before/after evidence from the real base and final head using sanitized data. Put evidence in ignored temporary storage and attach it through a supported upload mechanism; local filesystem links are not usable GitHub attachments.

Never fabricate screenshots or validation. Do not claim that a passing check covers behavior it never exercised. Describe agent assistance or human review status when the repository requires it, and never imply a human has reviewed a diff without evidence.

## Publish and Verify

Opening a PR includes the necessary authorized commit and push work. A description-only request stops at the draft text. If the user requests a draft PR, create it as a draft and leave it there until asked to mark it ready.

Use structured tool arguments for title and body. With CLI commands, write the exact body into an ignored temporary file and pass `--body-file`; avoid multiline shell interpolation. Reuse an existing PR instead of creating a duplicate.

After creation or update, read back the title, base, head, draft state, rendered description, and linked evidence. Report the PR URL, commit hash, validation, and remaining checks. Handling later review comments, merging, or enabling auto-merge are separate operations governed by the requested scope.
