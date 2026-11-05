# Provenance

This private repository contains skills created or customized for zhsama with assistance from Codex.

- `ablation-experiment` follows zhsama's workflow for proposing a controlled experiment, obtaining approval before execution, and verifying the original evidence.

- `codex-downgrade` is based on the detector zhsama supplied on 2026-09-08. This repository maintains its model tiers and reporting. Its original author and upstream URL were not supplied.

- `disk-junk-scan` was imported from the installed macOS disk-scan skill. Its instructions, inspection notes, and Python tool messages are now in English. It scans developer and coding-agent leftovers and stays read-only until cleanup is explicitly approved. No machine inventory or personal paths are included.

- `issue-brief` was created from zhsama's issue discovery, reproduction, learning, and contribution workflow. It is not an upstream project policy.
- `issue-review-workflow` records zhsama's process for independent issue verification, user approval of the problem list and repair scope, and review of the resulting changes.
- `sol-max-subagents` follows zhsama's requested delegation workflow for `gpt-6.1-sol` with `max` reasoning effort.
- `simplified` is the renamed `ludwig-personal-code-review-preferences`, preserving its review and simplification modes. It contains zhsama's maintained TypeScript ecosystem preferences, distinguished from project rules and externally verified standards. The candidate inventory and source-organization checks adapt ideas from Anthony Fu's [`antfu-simplify`](https://github.com/antfu/skills/blob/f63e9ec7bc85f67364b6596c2d29da87e83ce445/skills/antfu-simplify/SKILL.md) and [`antfu`](https://github.com/antfu/skills/blob/f63e9ec7bc85f67364b6596c2d29da87e83ce445/skills/antfu/SKILL.md). Local rules retain behavior evidence, scope-scaled validation, semantic abstraction, and conditional type/constant extraction rather than mechanical file or repetition thresholds.
- `project-init` distills zhsama's explicit preferences and inspected configurations from Echo, ai-gateway, Anchor, and Model Lens as of 2026-11-05. It adapts the configuration and starter approach from [`antfu`](https://github.com/antfu/skills/blob/f63e9ec7bc85f67364b6596c2d29da87e83ce445/skills/antfu/SKILL.md), using Vite+, conditional project dependencies, runtime-specific TypeScript configuration, and no prescribed validation library. Project source, private conversation transcripts, and machine-specific paths are not copied into the skill.
- `git-workflow` adapts [`antfu-create-pr`](https://github.com/antfu/skills/blob/f63e9ec7bc85f67364b6596c2d29da87e83ce445/skills/antfu-create-pr/SKILL.md) and [`antfu-issue-triage`](https://github.com/antfu/skills/blob/f63e9ec7bc85f67364b6596c2d29da87e83ce445/skills/antfu-issue-triage/SKILL.md) to zhsama's authorization, typed naming, scope, and `gh stack` preferences. It preserves evidence-based PR descriptions and triage, without automatic digest issues, publication of reviews, or extra approval rounds when the requested action is already authorized. Stack side effects were checked against local `gh stack` 0.2.0 help; the skill requires checking the installed version before use.
- `node-modules-inspector` is adapted from [antfu/node-modules-inspector](https://github.com/antfu/node-modules-inspector/tree/602140fc629ce6279ffac18ab88c76f7b1c9cf46/skills/node-modules-inspector) at revision `602140fc629ce6279ffac18ab88c76f7b1c9cf46`. The upstream MIT license is included in its skill directory. Local guidance adds read-only inspection, Chinese reports, installed-size interpretation, and the verified cache location, MCP names, and argument wrapper for version 2.7.0.

The initial import preserves the complete installed contents of both skills, including their Codex interface metadata and referenced documents. No personal session transcripts, account configuration, or unrelated third-party skill packages are included.

Material adapted from `antfu/skills` uses revision `f63e9ec7bc85f67364b6596c2d29da87e83ce445`. Its upstream MIT notice is included as `LICENSE.antfu.md` in each affected skill directory. The original PR-writing skill also credits Hugo Richard's [What my pull requests look like now](https://hugorcd.com/writing/what-my-pull-requests-look-like-now) for evidence by change type and honest verification reporting.

Distribution uses the existing Vercel Labs skills CLI and the Agent Skills directory format. This repository does not publish an npm package.
