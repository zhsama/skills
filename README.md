# Skills

My agent skills and coding preferences.

| Skill | Purpose |
| --- | --- |
| [project-init](skills/project-init/SKILL.md) | Start JavaScript and TypeScript projects with my preferred tools. |
| [simplified](skills/simplified/SKILL.md) | Review and simplify TypeScript code. |
| [git-workflow](skills/git-workflow/SKILL.md) | Handle issues, commits, pull requests, and stacks. |
| [issue-brief](skills/issue-brief/SKILL.md) | Find and explain an open-source bug worth working on. |
| [issue-review-workflow](skills/issue-review-workflow/SKILL.md) | Coordinate independent reviews of issues and fixes. |
| [ablation-experiment](skills/ablation-experiment/SKILL.md) | Test whether code or a design choice is necessary. |
| [node-modules-inspector](skills/node-modules-inspector/SKILL.md) | Inspect dependency duplicates, sizes, and maintenance opportunities. |
| [disk-junk-scan](skills/disk-junk-scan/SKILL.md) | Find reclaimable development files on macOS. |
| [codex-downgrade](skills/codex-downgrade/SKILL.md) | Audit which model served a Codex session. |
| [claude-code-coordination](skills/claude-code-coordination/SKILL.md) | Let Codex coordinate with an original Claude Code session and verify the reply. |
| [sol-max-subagents](skills/sol-max-subagents/SKILL.md) | Delegate work to Sol Max subagents. |
| [anime-infuse](skills/anime-infuse/SKILL.md) | Download anime with bilingual Chinese/Japanese subtitles into an Infuse library. |

## Install

Install all skills globally for Codex:

```sh
npx skills add zhsama/skills -g -a codex --skill '*'
```

Or choose individual skills:

```sh
npx skills add zhsama/skills -g -a codex --skill git-workflow simplified
```

`claude-code-coordination` is for Codex. For a Codex-only installation from a
persistent local checkout, link its directory into `${CODEX_HOME:-$HOME/.codex}/skills`.
The CLI's `-a codex` destination is shared with other agents; see
[AGENTS.md](AGENTS.md) before choosing that installation method.

## Usage

```text
$simplified Review the current diff.
$git-workflow Create a draft pull request.
```

## For agents

See [AGENTS.md](AGENTS.md) for installation options, updates, and maintenance.
My global instructions live in [rules/AGENTS.md](rules/AGENTS.md).

Some workflows were informed by [Anthony Fu's skills](https://github.com/antfu/skills).
