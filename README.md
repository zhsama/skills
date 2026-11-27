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
| [codex-downgrade](skills/codex/codex-downgrade/SKILL.md) | Codex only | Audit the serving model using local Codex sessions and routing evidence. |
| [agent-conversation-coordination](skills/codex/agent-conversation-coordination/SKILL.md) | Codex only | Coordinate with another agent in its existing conversation and verify its reply. Supports Claude Code and agy. |
| [sol-max-subagents](skills/codex/sol-max-subagents/SKILL.md) | Codex only | Execute a complete implementation or test plan with a Sol Max worker. |

Cross-agent skills still require the tools and platform described in each skill.
Sources live in `skills/shared/` and `skills/codex/`; skill names and invocation
commands stay the same.

## Install

Install all public skills globally for Codex:

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

## Private skills

These workflows are maintained in
[zhsama/skills-private](https://github.com/zhsama/skills-private), which requires
repository access. This public repository contains only these references:

| Skill | Source |
| --- | --- |
| `disk-junk-scan` | [Private skill](https://github.com/zhsama/skills-private/tree/main/skills/disk-junk-scan) |
| `anime-infuse` | [Private skill](https://github.com/zhsama/skills-private/tree/main/skills/anime-infuse) |
| `personal-context` | [Personal defaults](https://github.com/zhsama/skills-private/tree/main/skills/personal-context) |

```sh
npx skills add zhsama/skills-private -g -a codex --skill disk-junk-scan anime-infuse personal-context
```

Markdown references do not install dependencies. Install the private source
separately; installing all public skills does not install these workflows.

## Usage

```text
$simplified Review the current diff.
$git-workflow Create a draft pull request.
```

## For agents

See [AGENTS.md](AGENTS.md) for installation options, updates, and maintenance.
My global instructions live in [rules/AGENTS.md](rules/AGENTS.md).

Some workflows were informed by [Anthony Fu's skills](https://github.com/antfu/skills).

## License

[MIT](LICENSE). Adapted third-party files retain their own copyright notices;
see [PROVENANCE.md](PROVENANCE.md).
