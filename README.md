# Skills

My agent skills and coding preferences. Codex-only workflows are marked below.

| Skill | Agent scope | Purpose |
| --- | --- | --- |
| [project-init](skills/shared/project-init/SKILL.md) | Cross-agent | Start JavaScript and TypeScript projects with my preferred tools. |
| [simplified](skills/shared/simplified/SKILL.md) | Cross-agent | Review and simplify TypeScript code. |
| [git-workflow](skills/shared/git-workflow/SKILL.md) | Cross-agent | Handle issues, commits, pull requests, and stacks. |
| [issue-brief](skills/shared/issue-brief/SKILL.md) | Cross-agent | Find and explain an open-source bug worth working on. |
| [issue-review-workflow](skills/shared/issue-review-workflow/SKILL.md) | Cross-agent | Coordinate independent reviews of issues and fixes. |
| [ablation-experiment](skills/shared/ablation-experiment/SKILL.md) | Cross-agent | Test whether code or a design choice is necessary. |
| [node-modules-inspector](skills/shared/node-modules-inspector/SKILL.md) | Cross-agent | Inspect dependency duplicates, sizes, and maintenance opportunities. |
| [disk-junk-scan](skills/shared/disk-junk-scan/SKILL.md) | Cross-agent | Find reclaimable development files on macOS. |
| [codex-downgrade](skills/codex/codex-downgrade/SKILL.md) | Codex only | Audit the serving model using local Codex sessions and routing evidence. |
| [claude-code-coordination](skills/codex/claude-code-coordination/SKILL.md) | Codex only | Send scoped handoffs from Codex to an original Claude Code session and verify the reply. |
| [sol-max-subagents](skills/codex/sol-max-subagents/SKILL.md) | Codex only | Dispatch and coordinate Sol Max workers through Codex's subagent tools. |
| [anime-infuse](skills/shared/anime-infuse/SKILL.md) | Cross-agent | Download anime with bilingual Chinese/Japanese subtitles into an Infuse library. |

Cross-agent skills still require the tools and platform described in each skill.
Sources live in `skills/shared/` and `skills/codex/`; skill names and invocation
commands stay the same.

## Install

Install all skills globally for Codex:

```sh
npx skills add zhsama/skills -g -a codex --skill '*'
```

Or choose individual skills:

```sh
npx skills add zhsama/skills -g -a codex --skill git-workflow simplified
```

For another agent, select shared skills by name or install only the shared group:

```sh
npx skills add https://github.com/zhsama/skills/tree/main/skills/shared -g -a claude-code --skill '*'
```

For a Codex-only installation from a persistent local checkout, link each selected
leaf skill directory into `${CODEX_HOME:-$HOME/.codex}/skills`. The CLI's `-a codex`
destination is shared with other agents; see [AGENTS.md](AGENTS.md) for installation
and migration details.

## Usage

```text
$simplified Review the current diff.
$git-workflow Create a draft pull request.
```

## For agents

See [AGENTS.md](AGENTS.md) for installation options, updates, and maintenance.
My global instructions live in [rules/AGENTS.md](rules/AGENTS.md).

Some workflows were informed by [Anthony Fu's skills](https://github.com/antfu/skills).
