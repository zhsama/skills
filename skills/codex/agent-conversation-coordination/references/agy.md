# Antigravity CLI (agy)

## Identify the conversation

Check `agy --version` and `agy --help`. In 1.5.17, `agy agents` lists agent
profiles. Get the conversation UUID from its resume command, a prior JSON result,
or the user's target. For a title, the local CLI cache at
`~/.gemini/antigravity-cli/cache/conversation_metadata.json` maps IDs under
`conversations` to summaries. The sibling `last_conversations.json` gives a
workspace's most recent ID. Treat either lookup as a candidate and confirm the
requested context against recent user and model turns in its transcript.

The local transcript in 1.5.17 is under the CLI data directory. Record the last
complete step index before sending. Use the actual data directory if customized.

```sh
transcript="$HOME/.gemini/antigravity-cli/brain/$conversation_id/.system_generated/logs/transcript.jsonl"
```

## Send once

If the target has no open window, resolve its UUID from the evidence above
and check for a live owner across terminals and background processes. Once
the conversation is free, resume it headlessly by default from its verified
workspace without asking the user to open a window or confirm the transport. Pass the exact UUID and a quoted prompt containing the fresh marker.
For example, for a read-only discussion:

```sh
agy --conversation "$conversation_id" --mode plan --output-format json \
  --print "$handoff"
```

Use a permission mode appropriate to the authorized task. Avoid `--continue`
for addressed handoffs because the latest conversation can change. A headless
resume starts a new process. Reserve it for a conversation known to be free.

For a live CLI, use its existing terminal. Match its current conversation and
workspace to the transcript, and verify the foreground agy PID and TTY.
The original launch arguments can be stale after an in-session switch.
In macOS Ghostty the [adapter](../scripts/ghostty-message.applescript) accepts
`locate TTY PID`, `paste TTY PID PANE MESSAGE_FILE`, and `submit TTY PID PANE`.
Inspect the empty prompt, paste one marked line, inspect the exact draft, then
submit once. Leave user drafts, trust prompts, and approvals intact. If you
cannot establish which conversation a live pane owns, resolve that before
sending or starting another writer.

For a live agy pane in tmux, identify the server socket and pane ID. On 1.5.18
the agy process held an open `presence/<conversation_id>.lock` in the CLI data
directory. Check the open file with `lsof -a -p "$agy_pid" "$lock_path"`,
compare the pane history with the target transcript, and recheck PID, TTY and
foreground process before each input. A leftover lock file alone proves nothing.

```sh
tmux -S "$socket" display-message -p -t "$pane" '#{pane_pid} #{pane_tty}'
tmux -S "$socket" capture-pane -p -t "$pane"
# After inspecting the empty prompt, paste a single line of plain text.
tmux -S "$socket" send-keys -l -t "$pane" "$handoff"
tmux -S "$socket" capture-pane -p -J -t "$pane"
# After verifying the entire draft and rechecking identity, submit once.
tmux -S "$socket" send-keys -t "$pane" Enter
```

## Verify the turn

Read complete records in step order from the original transcript after the
saved step. The following filter projects the relevant messages from a stable
snapshot. If the last line is still being written, reread once complete.

```sh
jq -c --argjson after "$last_step" '
  select(.step_index > $after and .status == "DONE") |
  if .source == "USER_EXPLICIT" and .type == "USER_INPUT" then
    {step_index, user: (.content | split("</USER_REQUEST>")[0])}
  elif .source == "MODEL" and .type == "PLANNER_RESPONSE" then
    {step_index, reply: .content}
  else empty end
' "$transcript"
```

Match the marker and full handoff inside the new user request (plan mode can
prefix it with `/plan`). Follow that turn to its substantive model answer
before the next user turn. For headless delivery also check exit status,
`status == "SUCCESS"`, exact `conversation_id`, and agreement between the
JSON `response` and transcript answer after trimming surrounding whitespace.
For live delivery confirm the turn has finished in the pane. If the user also
asked to test a specific terminal, report which transport actually delivered
the message. Inspect claimed
changes or tests independently. After a timeout, missing record or ambiguous
result, inspect the original turn before deciding whether a retry is needed.
Report receipt, reply and independently verified work separately.

See Google's [headless mode](https://antigravity.google/docs/cli/headless/)
and [resume command](https://antigravity.google/docs/cli/commands/resume/).
