from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from flow_runtime import advance_flow, current_checkpoint_payload  # noqa: E402


class FlowRuntimeTests(unittest.TestCase):
    def test_setup_flow_revise_keeps_same_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "README.md").write_text("# Sample\n", encoding="utf-8")
            (repo / "AGENTS.md").write_text("### Main Technologies\n- Python\n", encoding="utf-8")

            initial = advance_flow(repo, "setup")
            revised = advance_flow(repo, "setup", session_path=Path(initial["session"]["alias_path"]), decision="Suggest changes")

            self.assertEqual(revised["checkpoint_index"], 0)
            self.assertFalse(revised["completed"])

    def test_setup_flow_approve_advances_to_next_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "README.md").write_text("# Sample\n", encoding="utf-8")
            (repo / "AGENTS.md").write_text("### Main Technologies\n- Python\n", encoding="utf-8")

            initial = advance_flow(repo, "setup")
            advanced = advance_flow(repo, "setup", session_path=Path(initial["session"]["alias_path"]), decision="Approve")

            self.assertEqual(advanced["checkpoint_index"], 1)
            self.assertIsNotNone(advanced["checkpoint"])

    def test_new_track_flow_completes_after_last_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            conductor_dir = repo / "conductor"
            (conductor_dir / "tracks").mkdir(parents=True)
            (conductor_dir / "product.md").write_text("# Product\n", encoding="utf-8")
            (conductor_dir / "product-guidelines.md").write_text("# Guidelines\n", encoding="utf-8")
            (conductor_dir / "tech-stack.md").write_text("# Stack\n", encoding="utf-8")
            (conductor_dir / "workflow.md").write_text("# Workflow\n", encoding="utf-8")
            (conductor_dir / "tracks.md").write_text("# Tracks\n\n---\n\nNo active tracks.\n", encoding="utf-8")

            state = advance_flow(repo, "newTrack", target="Implement auth")
            for _ in range(10):
                if state["completed"]:
                    break
                state = advance_flow(repo, "newTrack", target="Implement auth", session_path=Path(state["session"]["alias_path"]), decision="Approve")

            self.assertTrue(state["completed"])

    def test_current_checkpoint_payload_reads_existing_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "README.md").write_text("# Sample\n", encoding="utf-8")
            (repo / "AGENTS.md").write_text("### Main Technologies\n- Python\n", encoding="utf-8")

            state = advance_flow(repo, "setup")
            checkpoint = current_checkpoint_payload(repo, "setup", Path(state["session"]["alias_path"]))

            self.assertEqual(checkpoint["kind"], state["checkpoint"]["kind"])


if __name__ == "__main__":
    unittest.main()
