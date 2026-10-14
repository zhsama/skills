---
name: codex-downgrade
description: "检查 Codex 实际服务模型是否低于所选模型。用于用户问是否被降级、换模型、reroute、safety buffering、配额导致 fallback，或要求审计当前/最近 session。"
compatibility: "Requires Python 3.11+ and access to local Codex session and configuration files. Online probing additionally requires network access and Codex ChatGPT credentials."
---

# Codex Downgrade

判断 Codex 实际服务的模型是不是用户选的那个。只采信服务端自己声明的 model slug / 路由头 / 客户端 reroute 日志，不看回答质量。

脚本：`scripts/codex_downgrade.py`（Python 3.11+，标准库）。默认读 `$CODEX_HOME` 或 `~/.codex`。

## 何时跑哪种检查

用户没指定时，先跑 `session`。只有用户明确要求「现在去官方后端探测一下」时才跑 `official`（会发一条真实请求、消耗额度）。

当前会话 ID 若已知，优先 `--session-id`；否则 `--sessions 3`。

```bash
SCRIPT="$HOME/.codex/skills/codex-downgrade/scripts/codex_downgrade.py"

python3 "$SCRIPT" session --sessions 3
python3 "$SCRIPT" session --session-id <uuid-or-prefix>
python3 "$SCRIPT" official --model gpt-6-astra
```

`--json` 给机器读；`--redact` 给要贴出去的报告；`--evidence` 展开原始证据。

## 怎么报结果

先报 verdict 和 exit code，再列 findings。

| Exit | Verdict |
|---|---|
| 0 | 没发现降级 |
| 2 | 有风险或证据不足（header 被剥、配额高、日志里比对根本没跑过） |
| 3 | 确认降级 / reroute，或模型不可用 |
| 1 | 工具自己失败 |

证明级代码（任一即降级）：`MODEL_DOWNGRADED`、`MODEL_MISMATCH`、`VENDOR_MISMATCH`、`MODEL_UNRECOGNIZED`、`PROVIDER_SWITCHED_MID_SESSION`、`LOG_SERVER_MODEL_MISMATCH`、`LOG_PROVIDER_FALLBACK`、`LOG_MODEL_REROUTE_EVENT`、`SAFETY_BUFFERING_APPLIED`。

`LOGSCAN_UNCORROBORATED` / `HEADERS_STRIPPED` / `NO_SERVED_MODEL` 是缺证据，不是通过。不要把「没找到 mismatch 日志」说成「没有降级」。

`official` 需要 `auth.json` 里 `auth_mode: chatgpt`。API-key 安装只能用 `session`。

不要用 `chatgpt_route_check.user.js`；那是 chatgpt.com 网页脚本，和 Codex App 无关。
