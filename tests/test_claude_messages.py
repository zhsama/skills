import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/claude-code-coordination/scripts/read_messages.py"
SPEC = importlib.util.spec_from_file_location("claude_messages", SCRIPT)
READER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(READER)


def encode(record):
    return (json.dumps(record, ensure_ascii=False) + "\n").encode("utf-8")


def message(role, content, **fields):
    return dict(type=role, sessionId="test-session", message={"content": content}, **fields)


class ClaudeMessages(unittest.TestCase):
    def setUp(self):
        temp_root = ROOT / ".local"
        temp_root.mkdir(exist_ok=True)
        self.directory = tempfile.TemporaryDirectory(prefix="claude-messages-", dir=temp_root)
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "session.jsonl"

    def test_partial_utf8_record_is_read_once_after_completion(self):
        first = encode(message("user", "Codex handoff test-marker"))
        second = encode(message("assistant", [{"type": "text", "text": "已确认"}]))
        split = second.index("已".encode()) + 1
        self.path.write_bytes(first + second[:split])
        initial = READER.read_messages(self.path)
        self.assertEqual(initial["next_offset"], len(first))
        self.assertEqual([item["role"] for item in initial["messages"]], ["user"])
        with self.path.open("ab") as target:
            target.write(second[split:])
        following = READER.read_messages(self.path, initial["next_offset"])
        self.assertEqual(following["messages"][0]["text"], "已确认")
        self.assertEqual(following["file_id"], initial["file_id"])
        self.assertEqual(following["next_offset"], len(first + second))
        self.assertEqual(READER.read_messages(self.path, following["next_offset"])["messages"], [])

    def test_emits_text_but_not_thinking_tool_results_or_progress(self):
        records = [
            {"type": "progress", "data": {"text": "progress payload"}},
            message("user", [{"type": "tool_result", "content": "tool payload"}]),
            message("assistant", [
                {"type": "thinking", "thinking": "private reasoning"},
                {"type": "tool_use", "name": "Bash", "input": {"command": "command payload"}},
                {"type": "text", "text": "Visible reply"},
            ], uuid="reply-id"),
            message("user", "Internal notification", isMeta=True),
            message("assistant", "Side conversation", isSidechain=True),
        ]
        self.path.write_bytes(b"".join(map(encode, records)))
        result = READER.read_messages(self.path)
        self.assertEqual([item["text"] for item in result["messages"]], [
            "Visible reply", "Internal notification", "Side conversation",
        ])
        self.assertEqual(result["messages"][0]["uuid"], "reply-id")
        self.assertEqual(result["messages"][0]["session_id"], "test-session")
        self.assertTrue(result["messages"][1]["internal"])
        self.assertTrue(result["messages"][2]["sidechain"])

    def test_reports_omission_and_truncation_when_reading_recent_messages(self):
        self.path.write_bytes(b"".join(encode(message("assistant", text)) for text in [
            "old", "middle", "x" * 6001,
        ]))
        result = READER.read_messages(self.path, limit=2)
        self.assertEqual(result["omitted_messages"], 1)
        self.assertEqual(result["messages"][0]["text"], "middle")
        self.assertTrue(result["messages"][1]["truncated"])
        self.assertEqual(len(result["messages"][1]["text"]), 6000)

    def test_rejects_stale_or_misaligned_offsets_and_invalid_complete_records(self):
        self.path.write_bytes(encode(message("user", "message")))
        for offset in [-1, 2, self.path.stat().st_size + 1]:
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                READER.read_messages(self.path, after=offset)
        self.path.write_bytes(b"invalid\n")
        with self.assertRaisesRegex(ValueError, "Invalid JSONL record at byte 0"):
            READER.read_messages(self.path)
        self.path.write_bytes(b"[]\n")
        with self.assertRaisesRegex(ValueError, "Expected an object"):
            READER.read_messages(self.path)


if __name__ == "__main__":
    unittest.main()
