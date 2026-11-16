# Ghostty delivery on macOS

The discovery command was checked with Claude Code 2.1.325. Ghostty's installed
AppleScript dictionary is authoritative for its current commands and properties.
Inspect both before relying on these examples:

```sh
claude --version
claude agents --help
claude agents --json
sdef /Applications/Ghostty.app
```

These examples use Ghostty's `input text` (paste) and `send key` commands. They
do not read or replace the system clipboard. Use only where native app scripting
is permitted; a denied app-control permission is not a reason to try another
input mechanism. Do not write to `/dev/tty*`: writing there is not a supported
way to send a prompt to the foreground application.

## Correlate the process and pane

Get the PID from the selected Claude session, then inspect it:

```sh
ps -p 12345 -o pid=,tty=,stat=,command=
```

Replace the example PID with the observed PID. List panes without focusing them:

```applescript
tell application "Ghostty"
  set rows to {}
  repeat with w in windows
    repeat with t in terminals of w
      set end of rows to {id of t, name of t, tty of t, pid of t}
    end repeat
  end repeat
  return rows
end tell
```

Match the live Claude PID and full TTY path to exactly one stable terminal ID.
Titles and window indexes alone are insufficient. The terminal's `pid` property
is the foreground process, so a mismatch is a reason to re-inspect rather than
weaken the check. If the CLI, transcript, process, and pane disagree, do not send.

Inspect the selected pane through a permitted native readback or computer-use
tool to establish an empty Claude message prompt. Do not interrupt Claude or
erase user input to create one. If the pane cannot be inspected, ask the user to
leave the original session at an empty message prompt before delivery.

## Paste, inspect, then submit

Save the following adapter in the project's ignored temporary directory as
`ghostty-message.applescript`. Pass identity and paths as arguments; never embed
handoff text into shell or AppleScript source. Use a UTF-8 plain-text message file
without terminal control sequences.

```applescript
on run argv
  if (count of argv) is not 5 then error "Expected mode, terminal ID, TTY, PID, message path"
  set operation to item 1 of argv
  if operation is not "paste" and operation is not "submit" then error "Invalid operation"
  set terminalID to item 2 of argv
  set expectedTTY to item 3 of argv
  set expectedPID to (item 4 of argv) as integer
  set messagePath to item 5 of argv
  if operation is "paste" then
    set messageText to read POSIX file messagePath as «class utf8»
    if messageText is "" then error "Empty message"
  end if
  tell application "Ghostty"
    repeat with w in windows
      repeat with t in terminals of w
        if id of t is terminalID then
          if tty of t is not expectedTTY or pid of t is not expectedPID then error "Terminal identity changed"
          if operation is "paste" then
            input text messageText to t
          else
            send key "enter" to t
          end if
          return operation & " issued to the verified pane"
        end if
      end repeat
    end repeat
  end tell
  error "Original Claude terminal not found"
end run
```

Set these task-specific variables from the freshly verified identity, then call:

```sh
osascript "$adapter_path" paste "$terminal_id" "$claude_tty" "$claude_pid" "$message_path"
```

Inspect the pane again. Confirm that the intended message was pasted into Claude
and has not been submitted, truncated, or mixed with a draft. Recheck the live
session identity, then submit once:

```sh
osascript "$adapter_path" submit "$terminal_id" "$claude_tty" "$claude_pid" "$message_path"
```

If paste or submit fails, inspect the current pane and transcript before doing
anything further. The operation may have partially succeeded. Never rerun the
whole pair just because the reply has not arrived.

## Read the original response

Locate the transcript by its verified session ID, then use `read_messages.py`
from the skill's `scripts` directory. Record its `file_id` and `next_offset`
before dispatch. Supply that offset on each incremental read and compare the
file identity; do not treat a new file as continuation of an old cursor.

Delivery requires a new user message containing the marker and intended content
in the expected session. Follow the assistant's reply and inspect original
artifacts as required by the parent skill. A terminal return value, elapsed time,
or a busy-to-idle transition alone does not establish delivery or completion.
