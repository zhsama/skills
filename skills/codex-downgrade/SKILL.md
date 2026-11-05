---
name: codex-downgrade
description: "Audit the model that actually served a Codex session. Use when the user suspects a downgrade, model swap, reroute, safety buffering, quota-related fallback, or asks to audit the current or recent sessions."
compatibility: "Requires Python 3.11+ and access to local Codex session and configuration files. Online probing additionally requires network access and Codex ChatGPT credentials."
---

# Codex Downgrade

Check whether Codex served the model the user selected. Use the model slug declared by the backend, routing headers, and client reroute logs as evidence. Answer quality cannot establish which model served a request.

The detector at `scripts/codex_downgrade.py` uses the Python 3.11+ standard library. It reads from `$CODEX_HOME`, or `~/.codex` by default.

## Choose the check

Start with `session` unless the user specifies otherwise. Run `official` only when the user explicitly asks to probe the official backend now. It sends a real request and consumes quota.

Use `--session-id` if the current session ID is known. Otherwise start with `--sessions 3`.

```bash
SCRIPT="$HOME/.codex/skills/codex-downgrade/scripts/codex_downgrade.py"

python3 "$SCRIPT" session --sessions 3
python3 "$SCRIPT" session --session-id <uuid-or-prefix>
python3 "$SCRIPT" official --model gpt-6-astra
```

Use `--json` for machine-readable results, `--redact` for a report intended for sharing, and `--evidence` to show the raw evidence.

## Report the result

Give the verdict and exit code first, then the findings.

| Exit | Verdict |
| --- | --- |
| 0 | No downgrade detected |
| 2 | Risk or insufficient evidence, such as missing headers, high quota usage, or logs showing that the comparison never ran |
| 3 | Confirmed downgrade or reroute, or the requested model is unavailable |
| 1 | The detector itself failed |

The detector treats any of the following codes as confirmation. `MODEL_DOWNGRADED`, `MODEL_MISMATCH`, `VENDOR_MISMATCH`, `MODEL_UNRECOGNIZED`, `PROVIDER_SWITCHED_MID_SESSION`, `LOG_SERVER_MODEL_MISMATCH`, `LOG_PROVIDER_FALLBACK`, `LOG_MODEL_REROUTE_EVENT`, `SAFETY_BUFFERING_APPLIED`.

`LOGSCAN_UNCORROBORATED`, `HEADERS_STRIPPED`, and `NO_SERVED_MODEL` indicate missing evidence. An absent mismatch log does not establish that no downgrade occurred.

`official` requires `auth_mode: chatgpt` in `auth.json`. API-key installations can use `session` only. The `chatgpt_route_check.user.js` userscript is for chatgpt.com and does not apply to the Codex app.
