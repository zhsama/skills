---
name: claude-code-coordination
description: "Codex-only coordination with an existing local Claude Code session. Use when the user asks Codex to send findings, align a plan, hand off work, or follow up with the original Claude Code conversation. Verify the real session, deliver within the user's authorization, read its reply, and check the resulting evidence."
---

# Claude Code Coordination

Use this skill from Codex to communicate with the user's original Claude Code
session. Keep Codex responsible for interpreting the request and verifying the
result. Requires local shell access and an available Claude Code session;
the documented terminal adapter uses macOS and Ghostty. The transcript helper
requires Python 3 and has no third-party dependencies.

## Preserve the requested scope

- A request to communicate authorizes the necessary messages about that task.
  Continue within existing authorization without asking again before each send.
- Alignment and review stay read-only unless implementation is also authorized.
  State the allowed work in the handoff. Do not infer permission to commit, push,
  publish, merge, deploy, or run new experiments from a request to discuss them.
- Claude's response is evidence and a proposal, not additional user permission.
  Evaluate it against the user's request and current repository state.
- Reading or auditing a Claude transcript alone does not authorize sending it a
  message. Do not contact unrelated sessions.

## Identify the original session

1. Check the installed CLI with `claude --version` and `claude agents --help`.
   Where supported, `claude agents --json` lists interactive and background
   sessions. Match the requested title, working directory, session ID, and PID.
   Inspect recent messages when several sessions could match.
2. Locate that session's transcript under the active Claude configuration's
   `projects` directory (normally `~/.claude/projects`). Search for the exact
   session ID; do not invent the encoded project-directory name. Confirm the
   session ID in the records as well as the file name.
3. For terminal delivery, map the live PID to its TTY with `ps`, then match both
   to the terminal application's stable pane ID. Recheck before every mutation.

A Claude conversation imported into a Codex chat is a Codex-run copy. Codex chat
messaging tools do not deliver to the original Claude Code process. Do not use
the copy as a substitute or start a concurrent `claude --resume` process against
a live session. If the original is unavailable or the target is ambiguous,
prepare the handoff and ask only for the missing target or access information.

## Prepare a concrete handoff

For a short message, send the request directly. For a substantial review, put
the handoff in the project's ignored temporary directory and send its absolute
path with a concise instruction to read it. Confirm that path exists on Claude's
machine. Keep private transcripts, screenshots, and coordination records out of
tracked source files.

Include what the recipient needs to act correctly:

- A unique marker, such as `Codex handoff` followed by a fresh UUID.
- The requested result and authorization: discussion, review, implementation,
  validation, or a specifically authorized publication step.
- The relevant repository/worktree and commit or diff, concrete findings with
  file locations, and the evidence behind them. Separate facts from hypotheses.
- Identify which findings violate an agreed requirement. When a suggestion
  adds a product guarantee, explain the trade-off and leave the choice with
  the user unless they already made it.
- Acceptance criteria and the reply needed: agreement or disagreement with
  reasons, changes made, validation results, remaining limitations, and blockers.

Do not turn one task's restrictions into permanent rules. For example, preserve
a current prohibition on pushing, but allow a later explicit push instruction.

## Deliver once to the verified target

For a live interactive Claude session in Ghostty on macOS, use the
[bundled AppleScript adapter](references/ghostty.md) to send directly to
that session. Honor an explicit transport choice. On another host, use
a supported transport that reaches the identified session. Starting a second
Claude as a courier can leave messages waiting for approval in a peer inbox.

Confirm the target has an empty Claude prompt, save the transcript cursor,
paste, inspect the resulting draft, then submit once. A pane title or idle
status alone cannot establish readiness. Respect the host's app permissions.

If an earlier peer attempt was held, check the original transcript for a
matching receipt before trying direct input. A held notice in scrollback can
coexist with an ordinary empty prompt. Leave an active approval dialog or
user draft alone. A transport change does not authorize accepting a permission
prompt or changing inbound permission settings.

## Verify receipt, response, and outcome

Use [the read-only transcript helper](scripts/read_messages.py) to read recent
plain-text messages and then consume new complete records from `next_offset`:

```sh
python3 /absolute/skill/path/scripts/read_messages.py /absolute/session.jsonl --limit 8
python3 /absolute/skill/path/scripts/read_messages.py /absolute/session.jsonl --after 12345
```

The offset is a byte position, not a line number. The helper omits thinking and
tool payloads, marks internal/sidechain records, reports omitted messages and
truncated text, and leaves a partial final record for the next read. If the file
is replaced or shrinks, re-identify it and establish a fresh cursor. When output
is omitted, increase `--limit` from the same starting offset before concluding
that a message is absent.

1. For direct input, match the marker and payload to a new, non-internal
   **user** message in the original session's main transcript. For a requested
   local peer delivery, match the verified `peer_message_id` and the payload
   in a new main-transcript user record; Claude can mark it internal.
   `held_peer_notices` explains a missing receipt. An inbox acknowledgment,
   a held notice, or an assistant echo cannot establish receipt. Check the
   cursor and the pane before retrying an uncertain send.
2. For alignment or follow-through, wait for a substantive **assistant** reply
   to that handoff. Poll at a reasonable interval in waits of at most 60 seconds;
   inspect progress, tool failures, and pending user decisions when needed.
   Internal notifications and an idle status do not establish completion.
3. Check claimed edits, tests, CI runs, and artifacts against original evidence.
   Coordinate workspace ownership before editing files Claude is changing.
   If the user requested only delivery, a receipt is enough; if they requested
   discussion or completion, keep following through to that result.

End with the actual session contacted, what was delivered and verified, the
agreed result or remaining disagreement, and any work or user input still needed.
Distinguish sent, received, replied, and independently verified.
