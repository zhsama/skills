# Provenance

This private repository contains skills created or customized for zhsama with assistance from Codex.

- `ablation-experiment` was created from zhsama's requested ablation workflow: the main agent prepares the experiment design and subagent plan, obtains explicit approval before dispatch, delegates execution to `gpt-5.6-luna` with `max` reasoning effort, and verifies the original evidence. The skill is self-contained and includes no personal conversation transcripts or machine-specific paths.

- `codex-downgrade` preserves the complete previously installed skill, including its instructions, Codex interface metadata, and detector script. The detector is byte-for-byte identical to the file supplied by zhsama on 2026-09-08. Its original author and upstream URL were not supplied. The companion ChatGPT browser userscript is not included.

- `disk-junk-scan` was imported from the installed macOS disk-scan skill. Its instructions, inspection notes, and Python tool messages are now in English. It scans developer and coding-agent leftovers and stays read-only until cleanup is explicitly approved. No machine inventory or personal paths are included.

- `issue-brief` was created from zhsama's issue discovery, reproduction, learning, and contribution workflow. It is not an upstream project policy.
- `issue-review-workflow` records zhsama's process for independent issue verification, user approval of the problem list and repair scope, and review of the resulting changes.
- `luna-max-subagents` was created from zhsama's request to have the main agent delegate user-specified tasks and agent counts to `gpt-5.6-luna` subagents with `max` reasoning effort. Its invocation parameters follow the available collaboration tool schema.
- `sol-max-subagents` follows the same delegation shape for `gpt-6.1-sol` with `max` reasoning effort. It is independent of the Luna skill and does not replace it.
- `ludwig-personal-code-review-preferences` contains zhsama's maintained TypeScript ecosystem review and simplification preferences. Personal preferences are distinguished from project rules and externally verified standards in the skill.

The initial import preserves the complete installed contents of both skills, including their Codex interface metadata and referenced documents. No personal session transcripts, account configuration, or unrelated third-party skill packages are included.

Distribution uses the existing Vercel Labs skills CLI and the Agent Skills directory format. This repository does not publish an npm package.
