---
name: issue-review-workflow
description: "Coordinate independent subagent reviews of a GitHub milestone, issue, or set of audit findings. Stop for the user to confirm the findings before designing fixes and to approve the reviewed plan and scope before implementation. Also supports verification-only requests."
compatibility: "Requires a runtime that can start independent subagents with fresh contexts and access the target revision and its evidence."
---

# Issue Review Workflow

The lead agent divides the work, weighs evidence, designs and implements approved fixes, and verifies the result. Keep investigations and reviews read-only. Run probes in isolated fixtures. Keep interim judgments and side findings in the conversation by default. When resuming, check the target revision and the last confirmed scope. Revisit only what has materially changed.

## Delegation and skill selection

- Start each round with fresh subagents. In Codex, use `fork_turns: "none"`. Give each agent the target, revision, original materials, assigned question, allowed actions, and expected evidence. Collect independent submissions before sharing conclusions. If fresh contexts are unavailable, tell the user which stage is blocked.
- Use each skill's `description` to identify candidates for the current stage. Give every subagent in that stage the same candidate names, descriptions, and locations. The lead assigns areas of responsibility, such as architecture and abstractions, file and function responsibilities, or behavioral regressions. Each subagent decides which skills, if any, to read or combine.

## Verify the issues

1. List every original claim, pin the target revision, and divide the initial investigation along actual call paths. Investigators check the contract, callers, source, and tests. Seek a minimal reproduction and a counterexample. Identify affected users, triggering conditions, observations, and evidence gaps. Distinguish current behavior from a requested policy change.
2. After all investigations report, the lead makes a judgment on each claim. Start a new review team with only the original questions, revision, and source materials. Wait for its independent judgments before sharing the first round's evidence and the lead's summary. Ask the reviewers to challenge omissions, incorrect claims, and overstated conclusions. Resolve disagreements against the underlying evidence.
3. **Stop for the user to confirm the findings.** Report which claims are supported, contradicted, or still lack evidence. Include the impact and distinguish what was reproduced, inferred from source, or reported by the original author. Wait for the user to confirm the list and choose which items enter design. Gather more evidence for disputed items. Verification-only requests end here.

## Design and approval

1. The lead designs fixes only for the items the user chose. State which behaviors are in and out of scope, which callers are affected, and how to verify success.
2. Give the same plan to multiple fresh subagents for independent review from different angles, such as authorization, failure and retry behavior, testability, and complexity. Check the evidence behind objections. Revise and re-review the plan when an objection changes it materially.
3. **Stop for the user to approve implementation.** Present the reviewed plan, repair scope, and acceptance criteria. Lock the scope and start making changes only after the user explicitly approves that plan.

## Implementation, review, and handoff

1. Implement and test the approved changes. When an unrelated problem appears, record its location, impact, and known causal links for the handoff. If it blocks an approved acceptance criterion, pause the affected work and tell the user. Any necessary expansion of scope goes through plan review and user approval again.
2. Give multiple fresh reviewers who did not implement the fix the complete final diff, approved scope, and original failing scenarios. Divide the review across correctness, regressions in related behavior, and the clarity and simplicity of the code. The lead checks the raw results. Rework in-scope failures and repeat the review against the latest diff and the same scenarios.
3. Deliver the fixes, their acceptance evidence, outstanding verification gaps, and deferred findings together. For chains of new issues, distinguish established links from speculation. Let the user choose what to pursue next.
