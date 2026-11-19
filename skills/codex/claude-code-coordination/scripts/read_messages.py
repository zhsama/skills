#!/usr/bin/env python3
"""Read plain-text Claude messages without consuming an incomplete JSONL record."""

import argparse
from collections import deque
import json
import os
from pathlib import Path
import sys


def read_messages(path, after=0, limit=20):
    if after < 0 or limit < 1:
        raise ValueError("after must be nonnegative and limit must be positive")
    messages = deque(maxlen=limit)
    held_peer_notices = deque(maxlen=limit)
    total = 0
    with Path(path).open("rb") as source:
        size = source.seek(0, 2)
        if after > size:
            raise ValueError("Transcript shrank or offset exceeds file size; re-identify the file")
        if after:
            source.seek(after - 1)
            if source.read(1) != b"\n":
                raise ValueError("Offset must follow a complete JSONL line")
        source.seek(after)
        next_offset = after
        while True:
            offset = source.tell()
            line = source.readline()
            if not line or not line.endswith(b"\n"):
                break
            try:
                record = json.loads(line)
            except (ValueError, UnicodeDecodeError) as error:
                raise ValueError(f"Invalid JSONL record at byte {offset}") from error
            if not isinstance(record, dict):
                raise ValueError(f"Expected an object at byte {offset}")
            next_offset = source.tell()
            role = record.get("type")
            if role == "system" and record.get("subtype") == "informational":
                notice = record.get("content")
                if isinstance(notice, str) and notice.startswith("Held peer message"):
                    held_peer_notices.append({
                        "offset": offset,
                        "session_id": record.get("sessionId"),
                        "text": notice[:6000],
                    })
                continue
            if role not in ("user", "assistant"):
                continue
            message = record.get("message")
            if not isinstance(message, dict):
                raise ValueError(f"Missing message object at byte {offset}")
            content = message.get("content", [])
            if isinstance(content, str):
                text = content
            elif isinstance(content, list):
                text = "\n".join(
                    block["text"] for block in content
                    if isinstance(block, dict) and block.get("type") == "text"
                    and isinstance(block.get("text"), str)
                )
            else:
                raise ValueError(f"Unexpected message content at byte {offset}")
            if not text:
                continue
            total += 1
            item = {
                "offset": offset,
                "uuid": record.get("uuid"),
                "session_id": record.get("sessionId"),
                "timestamp": record.get("timestamp"),
                "role": role,
                "internal": bool(record.get("isMeta") or record.get("isCompactSummary")),
                "sidechain": bool(record.get("isSidechain")),
                "text": text[:6000],
                "truncated": len(text) > 6000,
            }
            origin = record.get("origin")
            if (role == "user" and isinstance(origin, dict)
                    and origin.get("kind") == "peer" and origin.get("verifiedLocal") is True
                    and isinstance(origin.get("msg_id"), str) and origin["msg_id"]):
                item["peer_message_id"] = origin["msg_id"]
            messages.append(item)
        identity = os.fstat(source.fileno())
    return {
        "file_id": f"{identity.st_dev}:{identity.st_ino}",
        "next_offset": next_offset,
        "omitted_messages": total - len(messages),
        "messages": list(messages),
        "held_peer_notices": list(held_peer_notices),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("transcript", type=Path)
    parser.add_argument("--after", type=int, default=0, help="Byte offset from the previous read")
    parser.add_argument("--limit", type=int, default=20, help="Maximum recent text messages to emit")
    args = parser.parse_args()
    try:
        result = read_messages(args.transcript, args.after, args.limit)
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
