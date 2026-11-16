# Agent guide

This repository contains zhsama's skills and global preferences. Use this guide when asked to install, update, or maintain them. The human-facing catalog is [README.md](README.md).

## Installation

Use the [skills CLI](https://github.com/vercel-labs/skills). The commands below were checked with version 1.9.0, which requires Node.js 22.20 or later, and Git for repository sources. Inspect the installed CLI's help if its version differs.

Read the requested skills' `compatibility` fields and instructions before installing. Installation provides instructions and bundled scripts; it does not provision the models, tools, credentials, or services they use.

Use the catalog's agent scope when selecting skills. Codex-only entries are intended to run from Codex; select cross-agent entries for other agents. A Codex example or `agents/openai.yaml` file alone does not make an otherwise portable skill Codex-only.

Sources are grouped as `skills/codex/<name>/` and `skills/shared/<name>/`. Both CLI 1.7.6 and 1.9.0 discover these nested sources without `--full-depth`. Keep each skill's `name` unchanged when moving it; installation and invocation still use that name. Install or link each leaf skill directory into the agent's skill root, rather than linking the whole category directory.

List the available skills:

```sh
npx skills add zhsama/skills --list
```

Install all public skills globally for Codex:

```sh
npx skills add zhsama/skills -g -a codex --skill '*' -y
```

Select individual skills and agents:

```sh
npx skills add zhsama/skills -g -a codex cursor --skill git-workflow simplified -y
```

- Use the scope and agents requested by the user. Omit `-g` for a project installation and run the command from that project's root.
- Use `--skill '*'` only when every skill supports the selected agents. This source includes Codex-only skills, so select skills by name when targeting other agents. `--all` also selects every agent, so it is unsuitable when the user named only some agents.
- `-a` selects destinations, not an access boundary. In CLI 1.9.0, Codex installs into the canonical `~/.agents/skills` directory, even with `--copy`; other agents can share its contents through their own discovery or links. For a Codex-only installation, copy or link each selected leaf directory into `${CODEX_HOME:-$HOME/.codex}/skills`. Category names and descriptions do not enforce installation filtering.
- Before replacing an existing skill, compare its files and recorded source with the requested version. Preserve local customizations in an ignored project-scoped backup and resolve substantive differences before overwriting them. Reinstalling an unchanged upstream copy needs no additional confirmation.
- Keep downloads, backups, and verification logs in an ignored `.local/` directory in the working checkout. Do not add them to the distributed skills.

The [CLI reference](https://github.com/vercel-labs/skills/blob/main/docs/commands.md) and [agent directory table](https://github.com/vercel-labs/skills/blob/main/docs/agents.md) describe other supported targets.

## Private workflows

`disk-junk-scan`, `anime-infuse`, and `personal-context` are maintained entirely
in [zhsama/skills-private](https://github.com/zhsama/skills-private). The public
catalog contains references only. When these skills are requested, install them
from the private repository using an account with access:

```sh
npx skills add zhsama/skills-private -g -a codex --skill disk-junk-scan anime-infuse personal-context
```

Keep the private workflows and their context in the same installation scope.
For existing installations, preserve local modifications, reinstall the selected
names from the private source, and verify their source records before restoring
local modifications. See the private repository's installation guide.

A Markdown reference does not make the CLI fetch a dependency. Do not add public
placeholder skills with the same names: installing them could replace a complete
private installation. Installations and updates of the public source cover only
the skills distributed here.

## Global instructions

[rules/AGENTS.md](rules/AGENTS.md) is the file to restore. This root guide describes repository operations and must not replace the user's global preferences.

Restore global instructions when the user asks for them or for a full setup that explicitly includes them. A request to install selected skills alone does not change global rules.

For Codex:

1. Read `rules/AGENTS.md` from the same repository revision used for the skill installation.
2. Resolve the destination to `AGENTS.md` inside `CODEX_HOME`, or `~/.codex/AGENTS.md` when `CODEX_HOME` is unset. Read the destination and check for `AGENTS.override.md`, which takes precedence.
3. If the destination already matches, leave it alone. Otherwise preserve any existing file in the checkout's ignored `.local/` directory and reconcile local changes with the requested restore. Do not silently discard custom rules or delete an override file.
4. Copy the resolved content to the destination and compare the result. Use a copy if the checkout is temporary; a link to a deleted checkout would break future sessions.
5. Report any active override and start a new session to verify the effective instructions.

See [Codex instruction discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md#how-codex-discovers-guidance). For another agent, check its official global-instruction format and location before adapting these preferences; installing a skill with `-a` does not install global rules for that agent.

## Updates and migration

Use named updates to keep the operation within the requested scope:

```sh
npx skills update -g git-workflow simplified
```

For a complete refresh of this source, rerun its scoped `add` command. Do not run an unrestricted global update as a substitute: it also affects skills installed from unrelated sources. Refresh global instructions separately by comparing `rules/AGENTS.md` with the installed file.

When a source directory moves, update README links, tests, CI paths, and any local links pointing into the checkout. Existing installed copies continue to work. If an older installation record cannot resolve the new source path, reinstall only the affected skill by name from the repository root.

`simplified` replaces `ludwig-personal-code-review-preferences`. If the old name is installed, preserve its customizations, install and verify `simplified`, then remove the old entry from the intended scope and agents. An update of the old name does not install the replacement. Check shared directories before removing a skill used by another agent.

## Verification

```sh
npx skills list -g -a codex
```

For project installs, omit `-g`. Confirm that the requested skill files and referenced resources exist, links resolve, and the CLI's installation records point to the intended source. Check actual destinations as well as the listing; shared-directory entries can be visible under more than one agent.

Report which skills, scope, and agents were installed, whether global rules were restored, and any missing runtime capabilities. A successful file installation does not establish that an external service is configured.

## Maintenance

- Keep each skill under `skills/codex/<name>/` or `skills/shared/<name>/` with every resource it references. Do not put a `SKILL.md` at a category root: the CLI treats that directory as a skill and stops discovering its descendants. Write instructions, descriptions, examples, and tool messages in English; preserve explicit response-language preferences.
- Keep README concise: purpose, catalog, basic installation, and a few examples. Put detailed operations in this guide and origins in [PROVENANCE.md](PROVENANCE.md).
- Maintain `rules/AGENTS.md` as the global preference source. Changes to the current local rules should be reconciled here rather than stored as another tracked backup.
- Preserve upstream notices with copied or adapted third-party files. Keep private session data, account configuration, and machine-specific paths out of tracked content.
- After skill changes, run the reference validator and existing regression suite. For documentation changes, check links and any installation commands affected by the change.

```sh
for skill in skills/*/*/; do
  uvx --from skills-ref==0.1.1 agentskills validate "$skill" || exit 1
done
python3 -m unittest discover -s tests
git diff --check
```

GitHub Actions runs the repository's existing skill and regression checks. Behavioral experiments are separate and should match the change being evaluated.
