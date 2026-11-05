# Provenance

This repository contains skills created or customized for zhsama with assistance from Codex.

- `rules/AGENTS.md` contains zhsama's current global instructions. It replaces the earlier `backups/codex/AGENTS.md` snapshot as the maintained source for restoring those preferences.

- `ablation-experiment` follows zhsama's workflow for proposing a controlled experiment, obtaining approval before execution, and verifying the original evidence.

- `codex-downgrade` is based on the detector zhsama supplied on 2026-09-08. This repository maintains its model tiers and reporting. Its original author and upstream URL were not supplied.

- `disk-junk-scan` was imported from the installed macOS disk-scan skill. Its instructions, inspection notes, and Python tool messages are now in English. It scans developer and coding-agent leftovers and stays read-only until cleanup is explicitly approved. No machine inventory or personal paths are included.

- `issue-brief` was created from zhsama's issue discovery, reproduction, learning, and contribution workflow. It is not an upstream project policy.
- `issue-review-workflow` records zhsama's process for independent issue verification, user approval of the problem list and repair scope, and review of the resulting changes.
- `sol-max-subagents` follows zhsama's requested delegation workflow for `gpt-6.1-sol` with `max` reasoning effort.
- `simplified` is the renamed `ludwig-personal-code-review-preferences`, preserving its review and simplification modes. It contains zhsama's maintained TypeScript ecosystem preferences, distinguished from project rules and externally verified standards. Anthony Fu's [`antfu-simplify`](https://github.com/antfu/skills/blob/f63e9ec7bc85f67364b6596c2d29da87e83ce445/skills/antfu-simplify/SKILL.md) and [`antfu`](https://github.com/antfu/skills/blob/f63e9ec7bc85f67364b6596c2d29da87e83ce445/skills/antfu/SKILL.md) informed the focus on examining the current changes and source organization. The reference is written around zhsama's contract, ownership, validation, and semantic-reuse rules; it does not retain the upstream candidate table.
- `project-init` distills zhsama's explicit preferences and inspected configurations from Echo, ai-gateway, Anchor, and Model Lens as of 2026-11-05. The [`antfu`](https://github.com/antfu/skills/blob/f63e9ec7bc85f67364b6596c2d29da87e83ce445/skills/antfu/SKILL.md) skill provided ideas about deliberate starter and TypeScript configuration choices. The resulting instructions use Vite+, conditional project dependencies, runtime-specific TypeScript configuration, and no prescribed validation library. Project source, private conversation transcripts, and machine-specific paths are not copied into the skill.
- `git-workflow` expresses zhsama's authorization, typed naming, scope, and `gh stack` preferences. [`antfu-create-pr`](https://github.com/antfu/skills/blob/f63e9ec7bc85f67364b6596c2d29da87e83ce445/skills/antfu-create-pr/SKILL.md) and [`antfu-issue-triage`](https://github.com/antfu/skills/blob/f63e9ec7bc85f67364b6596c2d29da87e83ce445/skills/antfu-issue-triage/SKILL.md) informed the emphasis on useful PR evidence and investigation before triage actions. The workflow follows the user's requested scope for publication and approval. Stack side effects were checked against local `gh stack` 0.2.0 help; the skill requires checking the installed version before use.
- `node-modules-inspector` is adapted from [antfu/node-modules-inspector](https://github.com/antfu/node-modules-inspector/tree/602140fc629ce6279ffac18ab88c76f7b1c9cf46/skills/node-modules-inspector) at revision `602140fc629ce6279ffac18ab88c76f7b1c9cf46`. The upstream MIT license is included in its skill directory. Local guidance adds read-only inspection, Chinese reports, installed-size interpretation, and the verified cache location, MCP names, and argument wrapper for version 2.7.0.

The initial import preserves the complete installed contents of both skills, including their Codex interface metadata and referenced documents. No personal session transcripts, account configuration, or unrelated third-party skill packages are included.

The `antfu/skills` references above were reviewed at revision `f63e9ec7bc85f67364b6596c2d29da87e83ce445`. They acknowledge ideas that helped refine these locally written skills. Copied or adapted third-party skill packages, including `node-modules-inspector`, keep their upstream notices with the distributed files.

Distribution uses the existing Vercel Labs skills CLI and the Agent Skills directory format. This repository does not publish an npm package.
