---
name: issue-brief
description: "Choose a public project bug just beyond the user's demonstrated experience. Target one growth area in mechanism understanding, causal diagnosis, design judgment, or verification. Check whether the issue is already claimed, try to reproduce it, and explain the mechanism and repair direction. Also use for an in-depth look at a specific issue. Default to analysis and advice."
---

# Issue Brief

## Scope

Recommend an issue the user could complete with limited support, just beyond what they can currently do independently. Give a self-contained explanation in Chinese. Assume programming experience but no prior knowledge of the issue or its terminology. The user should be able to explain the problem, weigh the evidence, and discuss a fix.

By default, stop at understanding the problem and suggesting a repair. Use an isolated directory or worktree for reproduction and retain the necessary commands and results. Preserve the user's working tree. Claiming an issue, changing labels, posting comments, committing code, or opening a PR requires separate authorization. Follow any explicit authorization in the current request.

## Choose the research scope

Choose the first applicable scope in this order.

1. If the user supplies an issue, analyze it directly. If already resolved, explain the cause and resolution.
2. Respect any repository, version, or topic the user specifies.
3. If the chat or working directory points to a public repository, prefer its upstream. Check the remote and fork relationship.
4. Otherwise, choose from public projects to which the user has recently submitted PRs.

Use the available GitHub tools or `gh` for identity and current state. Read the repository and version from the task and Git remote rather than hardcoding them. Ask one short question only if the remaining ambiguity would change the result. If access fails, identify the missing evidence and distinguish historical records from current status.

## Select an issue

Read the changes, tests, and review feedback in the user's relevant recent PRs. Use their demonstrated understanding to identify what they can already do and where they might need support. Reuse evidence from this chat. Consult a specific past session only when needed. State uncertainty about experience and ask about it only when it would change the choice.

### Choose a manageable stretch

Use the zone of proximal development as a selection guide. Pick a task that the user could advance independently after a short explanation, a code entry point, or a diagnostic hint. The following examples are practical guides informed by programming and systems courses, not a universal difficulty scale.

| Growth area | Example of a next step |
| --- | --- |
| Mechanism understanding | Go from calling an API to explaining its internal state transitions. |
| Causal diagnosis | Go from tracing one execution path to explaining how two operations interleave. |
| Design judgment | Go from changing local logic to assigning module responsibilities and preserving a cross-module contract. |
| Verification | Go from input/output checks to controlled scheduling, fault injection, or a performance comparison. |

Choose one primary growth area. Look for evidence that the other prerequisites are already in place or can be supplied by existing tools and a short explanation. Set aside candidates that require substantial study in two or more areas. Judge the mechanism or invariant involved rather than counting unfamiliar terms or changed files. A broad subject like distributed systems is too large to count as one missing skill.

With the intended support, the user should be able to propose the next hypothesis or experiment and advance the fix. If they would need to copy a complete solution step by step, narrow the challenge or support the prerequisite first. Prefer candidates with a workable build, defined requirements, and adequate observability unless the learning objective is the tooling or method itself.

### Screen candidates

Prefer a real defect with clear expected behavior, an identifiable code entry point, an observable acceptance condition, and an existing or reasonably inexpensive reproduction. Be able to explain what the user would learn beyond their previous work. Check whether another contributor is working on a substantive fix or an existing PR already covers it.

Consider the effort needed to understand the problem, prepare the test environment, follow cross-module effects, and resolve design disputes. Changed lines and `good first issue` labels alone are poor measures. Participation in one PR does not establish mastery of an entire area. Ease alone does not justify recommending a documentation move.

Compare a few strong candidates internally. Recommend one by default, or the number the user explicitly requests. Independent searches can run in parallel. Stay within the chosen scope, and exclude work the user is already doing unless they ask to continue it.

Read the issue body, comments, assignees, linked PRs, cross-references, and current code. An unassigned issue can already be claimed. A closed issue or PR is not proof that the current behavior was fixed. Check whether maintainers are still debating the expected behavior.

Recheck ownership before recommending a candidate. Qualify the result, for example, "I found no public claim or active fix." If no candidate fits, explain why. Leave out unrelated or already claimed issues.

## Build the evidence

Identify the environment, trigger, expected result, and observed result. Try the smallest reproduction that exercises the reported behavior.

- Work in isolation. Record the key versions, source revision, platform, and configuration.
- Start with the reported version, then compare with the current main branch or a relevant release when needed.
- Verify that the reproduction exercises the target code path. Configuration changes can bypass the original fault.
- Check observable behavior and output as well as the exit code.
- Use a control that distinguishes competing explanations when needed.

Keep build and environment work proportional to the issue. If the platform or a reasonable blocker prevents reproduction, record the limitation, completed investigation, and runnable reproduction steps. Label simulations, source-level reasoning, and the author's report accurately. Prefer an equally suitable candidate with direct evidence over an unverified hypothesis.

Trace the actual input and configuration through processing and intermediate state to output or error. Establish expected behavior from project documentation, existing tests, historical fixes, and relevant stable versions or implementations. For third-party behavior, use primary sources matching the project's version. Using the newest version is not an automatic reason to change the current contract.

Separate what you ran from what an author or maintainer reported and what you inferred from code. Include history only when it explains the current issue. If the introducing commit is unknown, leave it unknown. If the cause is uncertain, identify the last verified step and an experiment that could distinguish the remaining explanations.

## Explain the result

Organize the explanation in the following reading order. Combine adjacent parts when useful.

1. **Recommendation.** Link the issue and describe the user's problem in one sentence. Give evidence of the user's existing foundation, the primary growth area, the new challenge, the support needed, and the ownership status and check date. For a specified issue, introduce the problem directly without grading its suitability.
2. **Scenario.** Pick one concrete example and use it throughout. Identify the caller, command or operation, configuration, environment, and visible impact.
3. **Expected behavior.** Explain the feature's purpose and normal flow. Introduce only the terms the reader needs, as each becomes relevant.
4. **Failure and cause.** Use the same example to show where behavior diverges and how the effect reaches the user. Then name the relevant functions, fields, and source locations. Distinguish the trigger, root cause, and final error site.
5. **Reproduction evidence.** Give the key environment, minimal steps, expected and observed results, and any useful control. Say what you ran personally. Identify what is still unknown if the run failed or the evidence is incomplete.
6. **Repair direction.** Identify the layer that owns the behavior and explain why. Use a short sketch or suggested diff if useful. Look for existing facilities before introducing a special case. Describe relevant compatibility and performance boundaries, and identify unmeasured performance claims.
7. **Validation.** Choose a few discriminating checks for the original failure, nearby normal behavior, and key boundaries. Suggest ablation or a controlled comparison only for a concrete complexity dispute. Keep implementation, repository-wide testing, and performance engineering within the user's requested scope.

For a recommendation, give an observable sign of mastery. Examples include explaining a tradeoff, predicting a neighboring case, or designing an experiment that distinguishes two causes. Provide the requested explanation and advice without turning it into a compulsory quiz.

## Recalibrate with experience

As the user discusses or works on an issue, update your judgment from the actual sticking points, hints needed, and independent reasoning. Reading an explanation, participating in a PR, or getting it merged does not by itself show mastery. A method applied independently to a neighboring problem can support the next recommendation. Keep practicing areas that still require repeated prompts. Advance on evidence rather than the number of past recommendations.

## Language and presentation

- Write clear, direct Chinese for a programmer new to the module's terminology.
- Explain what an object does before naming its fields. Explain the normal flow before the failure and the cause before the supporting code.
- Keep the example, object names, and paths consistent. Each paragraph should make clear who reads, compares, changes, or stores what.
- Explain terms in context. Omit unrelated background, long strings of identifiers, and repeated conclusions.
- Use a short table for a comparison. Prefer a simple text sketch for a flow. Use Figma or a more complex diagram only when called for.
- Put links near the claims they support. Deliver an explanation the user can read on its own without pausing after each step to ask whether to continue.

For follow-up questions, identify the specific part the user is checking and reuse the original example. If the user restates the mechanism, identify what is correct and correct any errors. Supply an omitted step directly without restarting the whole explanation or introducing unrelated implementation details.
