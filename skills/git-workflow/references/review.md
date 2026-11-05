# Review and Feedback

## Review a Diff or PR

Pin the repository, base, head, and scope. For a stack, read [Stacks](stacks.md) and review the requested layer's own change. Read the full relevant diff and trace concrete behavior through its callers, configuration, tests, and contract owners.

Use `simplified` for code-quality review when available. Without it, apply repository rules and report only evidence-backed correctness, security, contract, performance, or maintenance issues. Separate personal preferences from blocking defects. Do not make style findings already enforced reliably by tooling.

Give each finding a precise location, triggering case, impact, evidence or uncertainty, and safe repair direction. Lead with findings and name validation gaps. A request to review stays read-only; experiments or reproductions that need files belong in an isolated, ignored project directory.

Report in the conversation unless a GitHub review or comment was requested. Never approve a PR, request changes remotely, or resolve a thread merely because a local review is complete.

## Address Existing Feedback

Read the current comment, its referenced revision, and the latest code. Check whether the concern is still valid, already fixed, or based on a different contract. Explain disagreements with evidence rather than implementing every suggestion mechanically.

Apply confirmed in-scope fixes when the user requests them. Keep unrelated changes outside the PR and rerun the focused checks plus required repository checks. If the user authorized replying or resolving feedback, publish the relevant commit and verification evidence, then verify the thread state. Do not resolve a thread before its concern is actually addressed.

Preserve the PR's requested draft state. New feedback does not authorize a merge, auto-merge, or rewriting published history.
