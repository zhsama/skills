# Personal Agent Skills

Agent Skills for zhsama, distributed as standard `SKILL.md` directories.

| Skill | Requirements | Purpose |
| --- | --- | --- |
| [ablation-experiment](skills/ablation-experiment/SKILL.md) | `gpt-5.6-luna`, `max` reasoning effort, and the project's experiment tools | The lead designs an ablation and assigns Luna's work. Execution follows user approval, and the lead checks the raw evidence. |
| [codex-downgrade](skills/codex-downgrade/SKILL.md) | Python 3.11+ and local Codex session data | Check whether the serving model matched the model the user selected. |
| [disk-junk-scan](skills/disk-junk-scan/SKILL.md) | macOS and the Python 3 standard library | Report reclaimable development and agent files by risk tier. Cleanup requires approval after the user sees the table. |
| [issue-brief](skills/issue-brief/SKILL.md) | GitHub access, source inspection, and a way to reproduce the issue | Choose a bug just beyond the user's current experience, reproduce it, and explain the mechanism and repair direction. |
| [issue-review-workflow](skills/issue-review-workflow/SKILL.md) | Independent subagents with fresh contexts | Verify issues, review plans and fixes, and stop for user approval of the findings and repair scope. |
| [ludwig-personal-code-review-preferences](skills/ludwig-personal-code-review-preferences/SKILL.md) | Target code and its toolchain. Review passes can run sequentially when subagents are unavailable. | Review or simplify TypeScript code using Ludwig's engineering preferences and preserve behavior during simplification. |
| [luna-max-subagents](skills/luna-max-subagents/SKILL.md) | A subagent runtime with the specified dispatch parameters, `gpt-5.6-luna`, and `max` effort | Delegate to Luna Max and verify the results. Default to three agents or choose another count that fits the task. |
| [sol-max-subagents](skills/sol-max-subagents/SKILL.md) | A subagent runtime with the specified dispatch parameters, `gpt-6.1-sol`, and `max` effort | Delegate to Sol Max and verify the results. Default to three agents or choose another count that fits the task. |

Model-independent workflows still need their listed capabilities. Compatibility with every agent has not been tested. The downgrade detector inspects Codex data and can be run by any agent with access to it. The disk scanner targets macOS. Installing the Luna or Sol skills does not provision the corresponding model or subagent runtime.

## Installation

This private repository uses the [skills CLI](https://github.com/vercel-labs/skills). You need repository access, Git, GitHub CLI or SSH authentication, and a Node.js version supported by the CLI.

List the available skills with the CLI.

```sh
npx skills@latest add zhsama/skills --list
```

Select skills with `--skill` and the target agent with `--agent`. The CLI does not filter on `compatibility`. Check the requirements above before choosing `--skill '*'` to install everything.

### General-purpose skills

These examples target Codex. For another supported agent, substitute its name, such as `claude-code` or `cursor`.

```sh
npx skills@latest add zhsama/skills --global --agent codex \
  --skill issue-brief --skill ludwig-personal-code-review-preferences
```

### Issue review workflow

```sh
npx skills@latest add zhsama/skills --global --agent codex --skill issue-review-workflow
```

### Codex session audit

Local checks need access to Codex sessions and configuration. An online probe also needs network access and Codex ChatGPT credentials.

```sh
npx skills@latest add zhsama/skills --global --agent codex --skill codex-downgrade
```

### Disk scan

The scanner uses macOS and Python 3. It displays a table first. The user approves cleanup separately after reviewing it.

```sh
npx skills@latest add zhsama/skills --global --agent codex --skill disk-junk-scan
```

### Luna skills

Check that the subagent runtime supports `gpt-5.6-luna`, `max`, and the dispatch parameters documented in the skill. The two skills are independent. Keep only the `--skill` options you want.

```sh
npx skills@latest add zhsama/skills --global --agent codex \
  --skill luna-max-subagents --skill ablation-experiment
```

The Luna skills report unavailable capabilities rather than substituting another model or having the lead run an experiment.

### Sol skill

`sol-max-subagents` works independently of the Luna skills. It requires the documented dispatch parameters and `gpt-6.1-sol` with `max` reasoning effort. It reports missing capabilities instead of substituting a model or executor.

```sh
npx skills@latest add zhsama/skills --global --agent codex --skill sol-max-subagents
```

### Install scope

Omit `--global` to install into the current project. The installer supports symlinks and copies. Pass `--copy` to request a copy. If the skill already exists, check for local edits before replacing it or creating a duplicate. When a project restricts package managers, you can run the global install command from your user directory. Set `DO_NOT_TRACK=1` to disable installer telemetry.

## Usage

In Codex, invoke a skill by name. The examples below can be used in any chat with the required tools.

```text
$ablation-experiment Prepare the experiment design and Luna assignments for this change. Wait for my approval.
$codex-downgrade Check which model served my recent Codex sessions.
$disk-junk-scan Scan for reclaimable development files. Show me the table before deleting anything.
$issue-brief Use my recent contributions to find an issue that develops one specific skill.
$issue-brief https://github.com/owner/repo/issues/123
$issue-review-workflow Verify every issue in <milestone URL>, independently recheck the findings, and bring me the list to confirm.
$ludwig-personal-code-review-preferences Review the current target.
$luna-max-subagents Review the API and tests separately, then summarize the results.
$sol-max-subagents Review the API and tests separately, then summarize the results.
```

`issue-brief` defaults to analysis and repair advice. Review skills use the target code, project toolchain, and appropriate official sources. Configure GitHub credentials, MCP services, and project dependencies separately.

`codex-downgrade` uses Python 3.11+ with no third-party runtime dependencies. It defaults to reading local session records. It can probe the official backend with local ChatGPT credentials when explicitly requested.

`disk-junk-scan` presents a risk-ranked table and waits for explicit cleanup approval.

`ablation-experiment` can be installed without `luna-max-subagents`. The lead presents the experiment design, agent count and assignments, model, permissions, and order of execution. Luna runs the approved work and returns the original calls, variant diffs, logs, and data for the lead to verify.

## Updates

```sh
npx skills@latest update ablation-experiment codex-downgrade disk-junk-scan issue-brief issue-review-workflow luna-max-subagents ludwig-personal-code-review-preferences sol-max-subagents
```

## Maintenance and validation

Maintain each skill under `skills/<skill-name>/`, including every file it references. Write skill instructions, descriptions, references, prompts, examples, and tool messages in English. Preserve any explicit preference for the language used to answer the user.

Declare specific runtime requirements with the [Agent Skills `compatibility` field](https://agentskills.io/specification#compatibility-field). This field describes requirements. The runtime still checks capabilities and grants permissions. General-purpose workflows do not need platform labels.

Optional `agents/openai.yaml` files provide Codex display names and default prompts. Determine compatibility from the models, tools, data, and services the skill uses.

Validate each directory using the Agent Skills reference validator.

```sh
uvx --from skills-ref==0.1.1 agentskills validate skills/ablation-experiment
uvx --from skills-ref==0.1.1 agentskills validate skills/codex-downgrade
uvx --from skills-ref==0.1.1 agentskills validate skills/disk-junk-scan
uvx --from skills-ref==0.1.1 agentskills validate skills/issue-brief
uvx --from skills-ref==0.1.1 agentskills validate skills/issue-review-workflow
uvx --from skills-ref==0.1.1 agentskills validate skills/luna-max-subagents
uvx --from skills-ref==0.1.1 agentskills validate skills/sol-max-subagents
```

GitHub Actions runs the same format checks on pushes and pull requests. Behavioral evaluation is separate. See [PROVENANCE.md](PROVENANCE.md) for origins and maintenance notes.
