"""Behavior and CLI tests for the offline Python example."""

from dataclasses import FrozenInstanceError
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from read_state import load_states


SCRIPT = Path(__file__).with_name("read_state.py").resolve()
SAMPLE = SCRIPT.with_name("joint_state.json")


class StateTests(unittest.TestCase):
    def test_sample_is_typed_and_immutable(self):
        states = load_states(SAMPLE)
        self.assertIsInstance(states, tuple)
        self.assertEqual(states[0].name, "demo_joint_1")
        self.assertAlmostEqual(states[0].position_rad, 0.25)
        with self.assertRaises(FrozenInstanceError):
            states[0].position_rad = 0.0

    def test_invalid_schema_and_numbers(self):
        valid = {"name": "demo_joint", "position_rad": 1, "velocity_rad_s": 0}
        documents = [
            [],
            {},
            {"joints": []},
            {"joints": "bad"},
            {"joints": [valid], "unknown": 0},
            {"joints": [valid, valid]},
            {"joints": [{"name": "demo_joint"}]},
            {"joints": [{**valid, "extra": 0}]},
        ]
        documents.extend(
            {"joints": [{**valid, "position_rad": value}]}
            for value in (True, "1.0", None, float("nan"), float("inf"), 10**400)
        )
        documents.extend(
            {"joints": [{**valid, "name": value}]} for value in ("", "  ", " joint ", 5)
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            for document in documents:
                with self.subTest(document=document):
                    path.write_text(json.dumps(document), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        load_states(path)

    def test_duplicate_fields_and_malformed_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            for text in (
                '{"joints": [], "joints": []}',
                '{"joints":',
                '{"joints":[{"name":"a","position_rad":1e999,"velocity_rad_s":0}]}',
            ):
                with self.subTest(text=text):
                    path.write_text(text, encoding="utf-8")
                    with self.assertRaises(ValueError):
                        load_states(path)

    def test_cli_from_unrelated_directory_and_failure_channels(self):
        with tempfile.TemporaryDirectory() as directory:
            successful = subprocess.run(
                [sys.executable, str(SCRIPT)],
                cwd=directory,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(successful.returncode, 0, successful.stderr)
            self.assertEqual(successful.stderr, "")
            self.assertEqual(len(json.loads(successful.stdout)["joints"]), 2)
            invalid = Path(directory) / "invalid.json"
            invalid.write_text('{"joints": []}', encoding="utf-8")
            for argument, expected in ((str(invalid), 2), ("missing.json", 3)):
                result = subprocess.run(
                    [sys.executable, str(SCRIPT), argument],
                    cwd=directory,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, expected)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr)
            invalid.write_bytes(b"\xff")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(invalid)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 3)
            self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
