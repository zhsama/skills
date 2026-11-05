# Personal Agent Skills

Agent Skills for zhsama, distributed as standard `SKILL.md` directories.

| Skill | Requirements | Purpose |
| --- | --- | --- |
| [ablation-experiment](skills/ablation-experiment/SKILL.md) | Access to the project and its experiment tools | Design an ablation, run it after user approval, and verify the raw evidence. |
| [codex-downgrade](skills/codex-downgrade/SKILL.md) | Python 3.11+ and local Codex session data | Check whether the serving model matched the model the user selected. |
| [disk-junk-scan](skills/disk-junk-scan/SKILL.md) | macOS and the Python 3 standard library | Report reclaimable development and agent files by risk tier. Cleanup requires approval after the user sees the table. |
| [git-workflow](skills/git-workflow/SKILL.md) | Git, repository access for GitHub operations, and gh stack for stacks | Handle issues, commits, PRs, reviews, and stacks through references loaded for the requested operation. |
| [issue-brief](skills/issue-brief/SKILL.md) | GitHub access, source inspection, and a way to reproduce the issue | Choose a bug just beyond the user's current experience, reproduce it, and explain the mechanism and repair direction. |
| [issue-review-workflow](skills/issue-review-workflow/SKILL.md) | Independent subagents with fresh contexts | Verify issues, review plans and fixes, and stop for user approval of the findings and repair scope. |
| [node-modules-inspector](skills/node-modules-inspector/SKILL.md) | Node.js, installed pnpm/npm/bun dependencies, and the inspector CLI or MCP server | Report duplicate versions, installed sizes, and maintenance opportunities. Reports are read-only and written in Chinese. |
| [project-init](skills/project-init/SKILL.md) | The target project, current toolchain documentation, and a supported runtime for execution | Initialize a focused TypeScript/Vite+ project with conditional stack choices and runtime-specific configuration. |
| [simplified](skills/simplified/SKILL.md) | Target code and its toolchain | Review or simplify TypeScript using zhsama's preferences. Inspect diff candidates and source organization; use focused checks for local edits and four passes for comprehensive work. |
| [sol-max-subagents](skills/sol-max-subagents/SKILL.md) | A subagent runtime with the specified dispatch parameters, `gpt-6.1-sol`, and `max` effort | Delegate to Sol Max and verify the results. Default to three agents or choose another count that fits the task. |

Model-independent workflows still need their listed capabilities. Compatibility with every agent has not been tested. The downgrade detector inspects Codex data and can be run by any agent with access to it. The disk scanner targets macOS.

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
  --skill project-init --skill git-workflow --skill simplified
```

`simplified` replaces the former `ludwig-personal-code-review-preferences` skill. Existing installations need an explicit rename migration: install `simplified`, verify it, and remove the old installed entry after preserving any local customization. Updating the old name alone does not install the new one. The repository keeps only the new entrypoint.

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

### Dependency inspection

```sh
npx skills@latest add zhsama/skills --global --agent codex --skill node-modules-inspector
```

Use the project's installed inspector CLI or an on-demand `npx node-modules-inspector report` command. The skill documents the three reports and the optional MCP interface.

### Ablation experiments

```sh
npx skills@latest add zhsama/skills --global --agent codex --skill ablation-experiment
```

### Sol skill

`sol-max-subagents` requires the documented dispatch parameters and `gpt-6.1-sol` with `max` reasoning effort. It reports missing capabilities instead of substituting a model or executor.

```sh
npx skills@latest add zhsama/skills --global --agent codex --skill sol-max-subagents
```

### Install scope

Omit `--global` to install into the current project. The installer supports symlinks and copies. Pass `--copy` to request a copy. If the skill already exists, check for local edits before replacing it or creating a duplicate. When a project restricts package managers, you can run the global install command from your user directory. Set `DO_NOT_TRACK=1` to disable installer telemetry.

## Usage

In Codex, invoke a skill by name. The examples below can be used in any chat with the required tools.

```text
$ablation-experiment Design a controlled experiment for this change. Wait for my approval before running it.
$codex-downgrade Check which model served my recent Codex sessions.
$disk-junk-scan Scan for reclaimable development files. Show me the table before deleting anything.
$git-workflow Open a draft PR for the current change. Use gh stack if it belongs to a stack.
$issue-brief Use my recent contributions to find an issue that develops one specific skill.
$issue-brief https://github.com/owner/repo/issues/123
$issue-review-workflow Verify every issue in <milestone URL>, independently recheck the findings, and bring me the list to confirm.
$node-modules-inspector Find duplicated versions and the largest installed dependencies in this project.
$project-init Initialize a React application using my preferred stack and verify its first working feature.
$simplified Simplify the current diff while preserving its observable behavior.
$simplified Review the current PR without changing files.
$sol-max-subagents Review the API and tests separately, then summarize the results.
```

`issue-brief` defaults to analysis and repair advice. Review skills use the target code, project toolchain, and appropriate official sources. Configure GitHub credentials, MCP services, and project dependencies separately.

`project-init` separates default tools from conditional product dependencies. `git-workflow` owns Git/GitHub operation boundaries and loads only the needed reference; it can use `simplified` for code review when installed. These skills do not require access to the projects from which the preferences were distilled.

`codex-downgrade` uses Python 3.11+ with no third-party runtime dependencies. It defaults to reading local session records. It can probe the official backend with local ChatGPT credentials when explicitly requested.

`disk-junk-scan` presents a risk-ranked table and waits for explicit cleanup approval.

`ablation-experiment` presents the baseline, variants, permitted writes, and decision criteria for approval. The same agent then runs the experiment and checks the diffs, commands, logs, and data.

## Updates

```sh
npx skills@latest update ablation-experiment codex-downgrade disk-junk-scan git-workflow issue-brief issue-review-workflow node-modules-inspector project-init simplified sol-max-subagents
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
uvx --from skills-ref==0.1.1 agentskills validate skills/git-workflow
uvx --from skills-ref==0.1.1 agentskills validate skills/issue-brief
uvx --from skills-ref==0.1.1 agentskills validate skills/issue-review-workflow
uvx --from skills-ref==0.1.1 agentskills validate skills/node-modules-inspector
uvx --from skills-ref==0.1.1 agentskills validate skills/project-init
uvx --from skills-ref==0.1.1 agentskills validate skills/simplified
uvx --from skills-ref==0.1.1 agentskills validate skills/sol-max-subagents
```

GitHub Actions runs the same format checks on pushes and pull requests. Behavioral evaluation is separate. See [PROVENANCE.md](PROVENANCE.md) for origins and maintenance notes.
