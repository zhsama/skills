import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


APPLY = Path(__file__).resolve().parents[1] / "skills/disk-junk-scan/scripts/apply.py"


class CleanupSelection(unittest.TestCase):
    def test_only_selected_commands_run(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            log = root / "calls"
            for name in ("pnpm", "row-cleanup"):
                stub = root / name
                stub.write_text('#!/bin/sh\nprintf "%s %s\\n" "${0##*/}" "$*" >> "$CALL_LOG"\n')
                stub.chmod(0o755)
            plan = root / "plan.json"
            plan.write_text(json.dumps([{
                "id": 4, "tier": "A", "size_kib": 1, "members": [],
                "command": ["row-cleanup", "4"], "path": "fixture://4",
            }]))
            env = {**os.environ, "PATH": str(root) + os.pathsep + os.environ["PATH"],
                   "CALL_LOG": str(log)}

            cases = [
                (["--rows", "4", "--execute"], ["row-cleanup 4"]),
                (["--tier", "A", "--execute"], ["row-cleanup 4"]),
                (["--prune-pnpm"], []),
                (["--prune-pnpm", "--execute"], ["pnpm store prune"]),
            ]
            for args, expected in cases:
                with self.subTest(args=args):
                    log.write_text("")
                    result = subprocess.run([sys.executable, str(APPLY), str(plan), *args],
                                            env=env, capture_output=True, text=True, check=True)
                    self.assertEqual(log.read_text().splitlines(), expected)
                    if "--execute" not in args:
                        self.assertIn("pnpm store prune", result.stdout)
