---
name: ablation-experiment
description: "Run ablation experiments when the user asks to test whether code, a design choice, or a test is necessary, or whether it can be simplified. The lead proposes an experiment and a Luna team, waits for explicit approval, then checks the evidence returned by gpt-5.6-luna. An ordinary code review does not start an experiment."
compatibility: "Requires a subagent runtime supporting gpt-5.6-luna, max reasoning effort, and the documented dispatch parameters, plus the target project's experiment tools."
---

# Ablation Experiment

The lead owns experiment design, coordination, validation criteria, exceptions, and the final judgment. Luna prepares the approved variants, writes the execution scripts, runs tests and measurements, and preserves the evidence.

## 1. Prepare the experiment and staffing plans

Read the relevant code, tests, configuration, versions, and existing experiment records. At this stage, prepare plans and execution instructions only. Wait for approval before starting the experiment, creating or resuming a subagent for it, or sending work to an existing agent. This applies to preliminary research delegated as part of the experiment and to runs by the lead.

Present both plans together, with a recommendation and the reason for it.

| Plan | What the user needs to decide |
| --- | --- |
| Experiment | Question, baseline, variants, controls, tests, performance metrics where relevant, decision criteria, and stopping conditions |
| Subagents | Number of Luna agents, assignments, model and reasoning effort, read/write boundaries, dependencies, order, and deliverables |

### Experiment design

- Identify the behavior contract and the source of complexity. Choose the design, code, or test to remove, replace, or combine. Give each variant a specific question. When mechanisms depend on one another, include the combinations needed to distinguish their effects.
- Pin the baseline, target version, inputs, and relevant environment. Give each experiment an ID, exact change, steps, expected observation, decision rule, and stopping condition. The executor should be able to run it without redesigning it.
- Check that the tests can detect the target failure. When ablating a test, check whether the remaining tests still catch the named regression. A green suite after removing production logic may indicate a coverage gap.
- For performance experiments, specify metrics, noise checks, repetition count, sampling order, and acceptable variation. Run measurements serially on a shared machine, away from unrelated builds and load tests. Add performance work only when it bears on the question.
- Separate a failure of the target behavior from a compilation failure, environment failure, or lack of evidence. Only a behavioral failure establishes that the removed mechanism was needed for that behavior.

### Subagent plan

- Follow the user's requested agent count. Otherwise, three is the default and the lead may choose another count that fits the experiment. State the concurrency limit, how many agents will run together, and the order of any batches.
- The default executor is `gpt-5.6-luna` with `max` reasoning effort. The lead keeps its current model.
- Give each executor its experiment IDs, inputs, permitted paths, isolation arrangements, dependencies, run order, and output locations. Prevent agents from overwriting shared files or results.
- Specify exception handling, permitted retries, and stopping conditions. Distinguish isolated variants from changes to the main workspace or permanent simplifications that require separate authorization.

## 2. Obtain approval before dispatch

**Wait for explicit approval of both the current experiment design and the subagent plan before dispatching any work or starting an experiment.**

- Show both plans, ask the user to confirm them, and wait for a reply. Explain that this skill requires the pause and link to this section.
- A general request for an ablation experiment, silence, a timeout, or agreement with just one plan leaves approval outstanding. Explicit agreement with the complete plan just presented is sufficient.
- If the user requests changes, revise the affected design or assignments and present the revision for approval. Keep track of which version and conditions the user approved.
- Obtain fresh approval for additional agents, a wider scope, a model change, a material change in method, read/write boundaries, or acceptance criteria. Continue ordinary execution and planned retries within the approved scope.

## 3. Dispatch and run the approved experiments

Follow the approved count and assignments. This skill contains the full dispatch procedure and can be used on its own.

- Use the runtime's subagent tool. Keep the work within the current chat. Pass `model: "gpt-5.6-luna"`, `reasoning_effort: "max"`, and `fork_turns: "none"` explicitly. Include the necessary context and the approved execution instructions in each task.
- If the subagent tool, model, or reasoning effort is unavailable, report the limitation. Do not substitute another model or run the experiment as the lead.
- Luna may write variants and scripts. Before they run, the lead verifies that they implement the approved design faithfully. The lead identifies any correction, and Luna applies it.
- Luna works within its assignment and does not create more agents or change the goal, controls, test semantics, sampling method, or decision criteria. For an unplanned condition, preserve evidence and return the question to the lead. The lead decides whether the plan needs revision and whether section 2 requires new approval.
- The lead coordinates dependencies and run order. Luna executes the commands and any authorized supplemental experiments. Subagent permissions remain bounded by the approved scope.

## 4. Review the evidence and decide

Require Luna to return the following evidence for each experiment ID.

- The actual revision, environment, and variant diff.
- The exact commands or tool calls, arguments, exit codes, and locations of raw logs and data.
- The observations, whether the stopping condition was met, deviations from the plan, and unfinished steps.

Long output can stay in files. Give precise locations and distinguish plans, actual calls, observed results, and inferences. The lead inspects key diffs, calls, and raw results. Check that the experiment exercised the target path, failures had the expected cause, controls held, and the tests could detect the regression. If evidence is missing, design a follow-up and assign it to Luna within the approved scope.

For each design element or test, state whether to keep it, simplify it, or leave the decision open. Cite the experiment, remaining risks, unfinished work, and decisions needed from the user. Passing ordinary tests, a review recommendation, or an unexecuted plan is insufficient evidence of completed ablation.
