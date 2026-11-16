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
- Acceptance criteria and the reply needed: agreement or disagreement with
  reasons, changes made, validation results, remaining limitations, and blockers.

Do not turn one task's restrictions into permanent rules. For example, preserve
a current prohibition on pushing, but allow a later explicit push instruction.

## Deliver once to the verified target

Use an available supported messaging API when it reaches the original session.
Otherwise use the verified terminal adapter; read
[Ghostty delivery](references/ghostty.md) before using that path. Follow any
app-access requirements in the environment, including the `computer-use` skill
when applicable. Do not bypass a denied app permission through another tool.

Before pasting, establish that Claude is accepting a message and that its input
is empty. A CLI status alone does not prove this. Do not paste into a shell,
approval dialog, active user draft, or an unverified busy session. Wait for the
appropriate prompt; keep preparing or checking independent evidence meanwhile.

Save the transcript read position before sending. Paste and submit as separate
operations, revalidating the target and checking the input between them. A
successful terminal command proves only that the input operation ran.

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

1. Find the unique handoff marker in a new **user** message of the expected
   session, with neither the internal nor sidechain flag set. Check its text or
   handoff path. An assistant echo or tool result is
   not delivery evidence. If receipt is uncertain, inspect the prompt and new
   records before retrying; do not blindly resend or press Enter twice.
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
