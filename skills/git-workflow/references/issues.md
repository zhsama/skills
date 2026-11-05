# Issues

Choose between investigating one issue, implementing an authorized repair, and triaging a backlog. Do not turn a targeted issue request into a full repository audit.

## Investigate or Solve an Issue

Read the issue, comments, linked PRs, current code, and relevant history. Verify whether the reported behavior still exists at the target revision. A matching title or an open fix PR is not proof that the issue is resolved.

Identify the affected behavior, triggering input, owning boundary, and evidence gap. Reproduce the failure or explain the source-based inference. Find the smallest owner-level correction that covers the real case and related boundaries.

With analysis-only scope, deliver the finding and repair direction. With implementation scope, make the repair and an appropriate regression check. Keep unrelated behavior changes separate, even when discovered while adding tests. Commit and PR delivery follow the user's authorization rather than being automatic consequences of fixing an issue.

## Triage a Backlog

Resolve the repository and requested range, then fetch issues, PRs, labels, and relevant timelines. Paginate to cover that range. For an unbounded large backlog, choose a clearly reported bounded initial pass or ask when the limit would materially affect the requested outcome.

Group linked items by the underlying symptom or request. Check:

- **Already fixed:** verify the current implementation and the merged fix; identify a release only when supported by tags or release evidence. Partial fixes stay open.
- **Duplicate:** compare the mechanism, reproduction, and requested behavior. Choose a canonical issue with useful evidence or active maintenance; wording alone is insufficient.
- **Spam:** require clear off-topic or abusive promotional evidence. A terse report, unfamiliar language, or missing template is not enough.
- **Labels and priority:** reuse existing labels and explain concrete impact. Reaction counts can describe demand but do not override severity or maintainer decisions.
- **Active work:** preserve ongoing discussion and linked open fixes. Do not close items merely because they are old.

Present proposed changes as a compact table: item, finding, supporting link, proposed action, and the exact comment when one is proposed. Keep the report in the conversation. Create a digest issue or tracking document only when requested.

Apply only authorized actions. If the user has already approved specific items and actions, use that approval without asking again. Otherwise obtain approval for the concrete proposed mutations before commenting, labeling, closing, or creating labels.

Comments should be short, specific, and supported by a canonical issue, fix, or release link. Follow the repository's language and automation-disclosure rules. Verify each mutation's result before continuing; on an API failure, report completed and remaining actions instead of blindly retrying a batch.
