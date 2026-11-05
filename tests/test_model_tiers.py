import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


DETECTOR = Path(__file__).resolve().parents[1] / "skills/codex-downgrade/scripts/codex_downgrade.py"


def audit_events(events, ranks=None):
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        sessions = root / "sessions"
        sessions.mkdir()
        records = [{"type": "session_meta", "payload": {"id": "example"}}]
        records.extend({"type": "event_msg", "payload": event} for event in events)
        (sessions / "rollout-example.jsonl").write_text("\n".join(map(json.dumps, records)))
        catalog = {"models": [{"slug": "gpt-6-astra", "priority": 10},
                              {"slug": "gpt-99-mini", "priority": 1}]}
        (root / "models_cache.json").write_text(json.dumps(catalog))
        command = [sys.executable, str(DETECTOR), "session", "--codex-home", str(root),
                   "--session-id", "example", "--no-log-scan", "--json"]
        if ranks is not None:
            path = root / "ranks.json"
            path.write_text(json.dumps(ranks))
            command.extend(["--tier-map", str(path)])
        result = subprocess.run(command, text=True, capture_output=True)
        return result.returncode, json.loads(result.stdout)


class ModelTiers(unittest.TestCase):
    def test_reroutes_preserve_identity_and_rank_each_observed_pair(self):
        cases = [
            ("gpt-6-astra", "gpt-6.1-sol", "MODEL_DOWNGRADED"),
            ("gpt-6.1-sol", "gpt-6-astra", "MODEL_UPGRADED"),
            ("gpt-6-sol", "gpt-6.1-sol", "MODEL_SAME_TIER"),
            ("gpt-6-astra", "gpt-99-mini", "MODEL_MISMATCH"),
            ("gpt-6-astra", "gpt-6-astra-preview", "MODEL_MISMATCH"),
            ("gpt-5.4", "gpt-5.4-mini", "MODEL_DOWNGRADED"),
            ("gpt-6-astra", "gpt-6-astra-2026-09-08", "MODEL_VARIANT"),
        ]
        events = [dict(type="model_reroute", from_model=source, to_model=target)
                  for source, target, _ in cases]
        code, report = audit_events(events)
        self.assertEqual(code, 3)
        compared = [(f["evidence"]["event"]["from_model"], f["evidence"]["event"]["to_model"],
                     f["code"]) for f in report["findings"] if f["code"].startswith("MODEL_")]
        self.assertEqual(compared, cases)

    def test_user_tiers_override_builtin_ranks(self):
        event = dict(type="model_reroute", from_model="gpt-6-astra", to_model="gpt-6.1-sol")
        code, report = audit_events([event], {"gpt-6.1-sol": 100})
        self.assertEqual(code, 3)
        self.assertIn("MODEL_SAME_TIER", [f["code"] for f in report["findings"]])
        self.assertNotIn("DOWNGRADE", report["verdict"])

    def test_buffering_offer_alone_does_not_establish_a_switch(self):
        code, report = audit_events([dict(type="safety_buffering", model="gpt-6-astra",
                                          faster_model="gpt-6-luna")])
        self.assertEqual(code, 2)
        self.assertIn("SAFETY_BUFFERING_APPLIED", [f["code"] for f in report["findings"]])
