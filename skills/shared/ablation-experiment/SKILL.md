---
name: ablation-experiment
description: "Run a controlled ablation when the user asks for experimental evidence that code, a design choice, or a test can be simplified. Propose the experiment, wait for explicit approval, run it, and inspect the raw evidence. Ordinary code review stays outside this workflow."
compatibility: "Requires access to the target project and its experiment tools."
---

# Ablation Experiment

## Design the experiment

Read the relevant code, tests, configuration, versions, and existing evidence. Present the question, the behavior to preserve, and the smallest comparison that can distinguish the possible explanations.

- Pin the baseline revision, environment, and inputs. For each variant, give its ID, exact change, controls, expected observation, decision rule, and stopping condition. Include combinations when mechanisms depend on one another.
- Check that the experiment exercises the target behavior and can detect its failure. When removing a test, introduce the target regression and check whether the remaining tests catch it.
- For performance claims, specify the metric, sampling order, repetitions, noise checks, and acceptable variation. Run measurements serially on a shared machine.
- Identify the isolated work area, permitted writes, execution order, and any planned retries. Keep raw logs, data, and variant diffs in the project's ignored temporary directory.

## Obtain approval

The agent that presents the design runs the experiment. Show the complete plan and wait for explicit approval before creating variants or executing trials. Explain this approval requirement and link to this section when requesting confirmation.

Use the approval already given for that plan. If the scope, write boundaries, method, or acceptance criteria materially change, present the revision for approval. Permanent changes to the target project require their own authorization.

## Run and verify

Inspect each variant diff against the approved design before running it. Record the revision, environment, commands, arguments, exit codes, and locations of the raw results. Check that the controls held and that the observed failure has the expected cause. Distinguish behavioral failures from compilation failures, environment failures, and missing evidence.

For each design element or test, recommend keeping it, simplifying it, or leaving the decision open. Cite the experiment and observation supporting that judgment. Report deviations, validation gaps, and any follow-up needed to distinguish the remaining explanations.
