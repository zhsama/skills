# Direct delivery to Claude Code in Ghostty

Use Ghostty's native AppleScript interface when the host permits it. The
[bundled adapter](../scripts/ghostty-message.applescript) addresses one pane
by its stable ID, full TTY and foreground PID without taking focus or changing
the clipboard. Use the installed Ghostty dictionary (`sdef /Applications/Ghostty.app`)
to diagnose an unsupported command.

## Identify and inspect the prompt

Match the original session ID and working directory in `claude agents --json`.
Use `ps -p "$claude_pid" -o tty=,stat=,command=` to confirm a live Claude
process. Supply the full device path (for example `/dev/ttys005`) and run:

```sh
adapter="$skill_dir/scripts/ghostty-message.applescript"
osascript "$adapter" locate "$claude_tty" "$claude_pid"
```

Keep the returned pane ID. Inspect that pane through permitted native readback
or computer use. If it is visible, a window-scoped screenshot can distinguish
an editable draft from Claude's dim prompt suggestion: the suggestion starts
at the empty prompt's cursor and disappears when text is pasted. Plain-text
readback loses that distinction. A held-message warning can sit in scrollback,
and a background shell can remain after Claude has returned to the prompt.
Inspect the current input area. Leave it intact while Claude is still working
in the foreground, a dialog has focus, or a user draft is present.

## Paste, inspect, submit

Record the transcript's file identity and byte cursor using
[read_messages.py](../scripts/read_messages.py). Put the short UTF-8 prompt
in a local file, including its marker and any absolute handoff path. Use a
single line without a trailing newline or terminal control sequences.
Pass the path as an argument so quotes or shell syntax in the message stay
literal.

```sh
osascript "$adapter" paste "$claude_tty" "$claude_pid" "$terminal_id" "$message_path"
```

Inspect the prompt again. Verify the complete intended draft and that no
pre-existing text was included. Recheck the live session identity and submit:

```sh
osascript "$adapter" submit "$claude_tty" "$claude_pid" "$terminal_id"
```

Read the original transcript from the saved cursor and verify the matching
user message. After an uncertain input operation, inspect the pane and
transcript before retrying. Follow the original session to the completion
condition the user requested.
