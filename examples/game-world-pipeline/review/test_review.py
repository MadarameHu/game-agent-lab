"""Isolated temporary fixtures only; never submit a review for a real run."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from server import ReviewStore, write_json, within


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.directory = self.root / "runs" / "test-run"
        self.directory.mkdir(parents=True)
        write_json(self.root / "runs" / "latest.json", {"run_id": "test-run"})
        self.store = ReviewStore(self.root)
        self.checks = {"hard_pass": True, "engine_reward": 1.0, "checks": [
            {"id": key, "pass": True} for key in ("scene_load", "bounds", "no_overlap", "route_exists", "rollout_reaches_goal")
        ]}
        candidates = []
        for candidate_id, origin in (("initial", "fixture"), ("final", "model")):
            p = self.directory / "candidates" / candidate_id
            p.mkdir(parents=True)
            write_json(p / "scene.json", {"brief": "test only", "objects": []})
            write_json(p / "checks.json", self.checks)
            candidates.append({"id": candidate_id, "origin": origin, "spec": f"candidates/{candidate_id}/scene.json", "checks": f"candidates/{candidate_id}/checks.json"})
        self.manifest = {"run_id": "test-run", "brief": "temporary test", "model": {"name": "test-only"}, "status": "awaiting_human", "candidates": candidates, "final_candidate_id": "final", "human_review": None}
        write_json(self.directory / "manifest.json", self.manifest)

    def tearDown(self):
        self.temp.cleanup()

    def test_pending_never_implies_human_reward_or_sft(self):
        self.store.exports(self.directory, self.manifest)
        self.assertEqual((self.directory / "sft.jsonl").read_text(), "")
        rows = [json.loads(x) for x in (self.directory / "rl_transitions.jsonl").read_text().splitlines()]
        self.assertEqual(len(rows), 1)
        self.assertIsNone(rows[0]["combined_reward"])
        self.assertEqual(rows[0]["previous_origin"], "fixture")
        self.assertEqual(rows[0]["previous_scene"]["brief"], "test only")
        self.assertTrue(rows[0]["previous_checks"]["hard_pass"])

    def test_accept_records_real_decision_and_does_not_change_checks(self):
        (self.directory / "actions").mkdir()
        write_json(self.directory / "actions/final.json", {"move": "crate_1"})
        (self.directory / "requests").mkdir()
        messages = [{"role": "system", "content": "Return a move action"}, {"role": "user", "content": "Please repair the blocked room"}]
        write_json(self.directory / "requests/final.json", {"messages": messages})
        check = self.directory / "candidates/final/checks.json"
        original = check.read_bytes()
        self.store.review("test-run", "accept", "人工测试接受")
        self.assertEqual(check.read_bytes(), original)
        sft = json.loads((self.directory / "sft.jsonl").read_text())
        self.assertEqual(sft["origin"], "model")
        self.assertEqual(sft["context"]["previous_origin"], "fixture")
        self.assertEqual(sft["input"], {"messages": messages})
        self.assertNotIn("action", sft["input"])
        self.assertNotIn("crate_1", json.dumps(sft["input"]))
        self.assertEqual(sft["output"], {"move": "crate_1"})
        self.assertEqual(sft["result_scene"]["brief"], "test only")
        row = json.loads((self.directory / "rl_transitions.jsonl").read_text())
        self.assertEqual(row["combined_reward"], 1.0)
        self.assertEqual(json.loads((self.directory / "manifest.json").read_text())["status"], "accepted")
        with self.assertRaises(ValueError):
            self.store.review("test-run", "reject", "duplicate")

    def test_fail_and_forged_hard_pass_cannot_accept(self):
        self.checks["checks"][-1]["pass"] = False
        write_json(self.directory / "candidates/final/checks.json", self.checks)
        self.assertFalse(self.store.view()["can_accept"])
        with self.assertRaises(ValueError):
            self.store.review("test-run", "accept", "")
        self.store.review("test-run", "reject", "failed rollout")
        self.assertEqual((self.directory / "sft.jsonl").read_text(), "")
        self.assertEqual(json.loads((self.directory / "rl_transitions.jsonl").read_text())["combined_reward"], 0.0)

    def test_traversal_and_symlink_escape_rejected(self):
        with self.assertRaises(ValueError):
            self.store.run("../escape")
        with self.assertRaises(ValueError):
            within(self.directory, "../../runtime.json")
        (self.directory / "escape").symlink_to(self.root)
        with self.assertRaises(ValueError):
            within(self.directory, "escape/runtime.json")

    def test_run_listing_limits_to_valid_local_manifests(self):
        (self.root / "runs" / "outside").symlink_to(self.root)
        rows = self.store.list_runs()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["run_id"], "test-run")
        self.assertEqual(rows[0]["mode"], "repair")

    def test_action_path_cannot_escape_run(self):
        self.manifest["candidates"][-1]["action"] = "../../outside.json"
        with self.assertRaises(ValueError):
            self.store.exports(self.directory, self.manifest)

    def test_no_sft_without_authentic_request_and_response(self):
        self.store.review("test-run", "accept", "test")
        self.assertEqual((self.directory / "sft.jsonl").read_text(), "")

    def test_raw_response_fallback_is_output_only(self):
        (self.directory / "requests").mkdir()
        (self.directory / "responses").mkdir()
        write_json(self.directory / "requests/final.json", {"messages": [{"role": "user", "content": "repair"}]})
        write_json(self.directory / "responses/final.json", {"raw_text": '{"moves": []}'})
        self.store.review("test-run", "accept", "test")
        row = json.loads((self.directory / "sft.jsonl").read_text())
        self.assertEqual(row["output"], '{"moves": []}')
        self.assertNotIn("moves", json.dumps(row["input"]))

    def test_play_uses_separate_directory(self):
        (self.root / "engine").mkdir()
        (self.root / "engine/project.godot").write_text("test fixture")
        write_json(self.root / "runtime.json", {"godot": "/fake/godot", "project_root": str(self.root)})
        with patch("server.subprocess.Popen") as popen:
            popen.return_value.pid = 123
            result = self.store.play("test-run")
            self.assertTrue(result["output"].startswith("play_sessions/"))
            command = popen.call_args.args[0]
            self.assertIn("--play", command)
            self.assertNotEqual(command[command.index("--out") + 1], str(self.directory / "candidates/final"))


if __name__ == "__main__":
    unittest.main()
