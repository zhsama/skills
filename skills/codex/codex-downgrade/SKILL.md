---
name: codex-downgrade
description: "Codex-only model audit. Use within Codex when the user suspects a downgrade, model swap, reroute, safety buffering, quota-related fallback, or asks which model actually served the current or recent Codex sessions."
compatibility: "Codex only. Requires Python 3.11+ and access to local Codex session and configuration files. Online probing additionally requires network access and Codex ChatGPT credentials."
---

# Codex Downgrade

Use this skill from Codex to check whether it served the model the user selected. It audits Codex sessions, not the serving models of other agents. Use the model slug declared by the backend, routing headers, and client reroute logs as evidence. Answer quality cannot establish which model served a request.

The detector at `scripts/codex_downgrade.py` uses the Python 3.11+ standard library. It reads from `$CODEX_HOME`, or `~/.codex` by default.

## Choose the check

Start with `session` unless the user specifies otherwise. Run `official` only when the user explicitly asks to probe the official backend now. It sends a real request and consumes quota.

Use `--session-id` if the current session ID is known. Otherwise start with `--sessions 3`.

Resolve the script from this skill's installed directory; the installation may be in Codex's own skill directory or a shared skill directory.

```bash
CODEX_AUDIT_SCRIPT="/absolute/path/to/codex-downgrade/scripts/codex_downgrade.py"

python3 "$CODEX_AUDIT_SCRIPT" session --sessions 3
python3 "$CODEX_AUDIT_SCRIPT" session --session-id <uuid-or-prefix>
python3 "$CODEX_AUDIT_SCRIPT" official --model gpt-6-astra
```

Use `--json` for machine-readable results, `--redact` for a report intended for sharing, and `--evidence` to show the raw evidence.

## Report the result

Give the verdict and exit code first, then the findings.

| Exit | Verdict |
| --- | --- |
| 0 | No downgrade detected |
| 2 | Risk or insufficient evidence, such as missing headers, high quota usage, or logs showing that the comparison never ran |
| 3 | Confirmed model change or reroute (including same-tier and higher-tier substitutions), or the requested model is unavailable |
| 1 | The detector itself failed |

Report the requested and serving model IDs first when both are available. The audit groups named models by product tier in descending order: Astra (100), Sol (90), Terra (65), and Luna (40). Known revisions of the same named tier share a rank. These are audit conventions based on the [OpenAI model catalog](https://developers.openai.com/api/docs/models).

`MODEL_DOWNGRADED`, `MODEL_UPGRADED`, and `MODEL_SAME_TIER` require explicit ranks for both models. A different model with an unknown rank yields `MODEL_MISMATCH` with the direction undetermined. Use `--tier-map` with a JSON object of model IDs and integer ranks to add or override tiers. Version numbers, name fragments, and model picker order do not establish rank.

A reroute event with both model IDs supports the same comparison offline. A routing signal alone establishes no tier direction. Safety buffering can advertise a faster model without switching to it.

`LOGSCAN_UNCORROBORATED`, `HEADERS_STRIPPED`, and `NO_SERVED_MODEL` indicate missing evidence. An absent mismatch log does not establish that no downgrade occurred.

`official` requires `auth_mode: chatgpt` in `auth.json`. API-key installations can use `session` only. The `chatgpt_route_check.user.js` userscript is for chatgpt.com and does not apply to the Codex app.
