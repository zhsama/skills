-- Locate a live agent pane, or perform one separately verified input step.
on run argv
  if (count of argv) < 3 then error "Expected operation, full TTY path and agent PID"
  set operation to item 1 of argv
  set expectedTTY to item 2 of argv
  set expectedPID to (item 3 of argv) as integer
  if operation is "locate" and (count of argv) is 3 then
    set expectedID to ""
  else if operation is "paste" and (count of argv) is 5 then
    set expectedID to item 4 of argv
    set messageText to read POSIX file (item 5 of argv) as «class utf8»
    if messageText is "" then error "Empty message"
    repeat with ch in characters of messageText
      set codePoint to id of (contents of ch)
      if codePoint < 32 or (codePoint ≥ 127 and codePoint ≤ 159) then error "Use one line of plain text without control characters"
    end repeat
  else if operation is "submit" and (count of argv) is 4 then
    set expectedID to item 4 of argv
  else
    error "Expected locate TTY PID, paste TTY PID PANE MESSAGE_FILE, or submit TTY PID PANE"
  end if

  tell application "Ghostty"
    set matches to {}
    repeat with w in windows
      repeat with t in terminals of w
        if tty of t is expectedTTY and pid of t is expectedPID then set end of matches to contents of t
      end repeat
    end repeat
    if (count of matches) is not 1 then error "Expected one pane matching the agent PID and TTY"
    set targetPane to item 1 of matches
    if operation is "locate" then return {id of targetPane, name of targetPane}
    if id of targetPane is not expectedID or tty of targetPane is not expectedTTY or pid of targetPane is not expectedPID then error "Terminal identity changed"
    if operation is "paste" then
      input text messageText to targetPane
    else
      send key "enter" to targetPane
    end if
  end tell
end run
