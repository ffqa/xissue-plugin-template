#!/usr/bin/env python3
"""Smoke-test the Python template against local fixtures."""

import json
import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class TemplateTest(unittest.TestCase):
    def test_issue_created_returns_notify(self):
        payload = (ROOT / "fixtures" / "issue_created.json").read_text(encoding="utf-8")
        result = subprocess.run(
            [str(ROOT / "run.py")],
            input=payload,
            text=True,
            capture_output=True,
            timeout=10,
            check=True,
        )
        output = json.loads(result.stdout)
        self.assertEqual(output["actions"][0]["type"], "notify")
        self.assertIn("LOCAL-7", output["actions"][0]["message"])

    def test_unknown_event_returns_no_actions(self):
        result = subprocess.run(
            [str(ROOT / "run.py")],
            input=json.dumps({"event": "unknown"}),
            text=True,
            capture_output=True,
            timeout=10,
            check=True,
        )
        self.assertEqual(result.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
