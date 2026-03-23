from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from revert_flow import build_flow  # noqa: E402


class RevertFlowTests(unittest.TestCase):
    def test_revert_flow_without_target_builds_guided_selection_menu(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            conductor_dir = repo / "conductor"
            track_dir = conductor_dir / "tracks" / "sample_20260323"
            track_dir.mkdir(parents=True)
            (conductor_dir / "tracks.md").write_text(
                "---\n\n- [~] **Track: Sample**\n  *Link: [./tracks/sample_20260323/](./tracks/sample_20260323/)*\n",
                encoding="utf-8",
            )
            (track_dir / "plan.md").write_text("## Phase: Phase 1\n- [~] Task: Active task\n", encoding="utf-8")
            (track_dir / "metadata.json").write_text(
                '{"track_id":"sample_20260323","type":"feature","status":"in_progress","created_at":"2026-03-23T00:00:00Z","updated_at":"2026-03-23T00:00:00Z","description":"Sample","title":"Sample"}',
                encoding="utf-8",
            )
            (track_dir / "index.md").write_text("- [Implementation Plan](./plan.md)\n", encoding="utf-8")

            flow = build_flow(repo, None, None, False)

            self.assertIn("selection_menu", flow)
            self.assertLessEqual(len(flow["selection_menu"]["options"]), 4)
            self.assertEqual(flow["selection_menu"]["options"][0]["label"], "[Task] Active task")

    def test_revert_flow_with_target_builds_confirmation_and_plan_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            conductor_dir = repo / "conductor"
            track_dir = conductor_dir / "tracks" / "sample_20260323"
            track_dir.mkdir(parents=True)
            (conductor_dir / "tracks.md").write_text(
                "---\n\n- [~] **Track: Sample**\n  *Link: [./tracks/sample_20260323/](./tracks/sample_20260323/)*\n",
                encoding="utf-8",
            )
            (track_dir / "plan.md").write_text("## Phase: Phase 1\n- [x] Task: Done task abc1234\n", encoding="utf-8")
            (track_dir / "metadata.json").write_text(
                '{"track_id":"sample_20260323","type":"feature","status":"in_progress","created_at":"2026-03-23T00:00:00Z","updated_at":"2026-03-23T00:00:00Z","description":"Sample","title":"Sample"}',
                encoding="utf-8",
            )
            (track_dir / "index.md").write_text("- [Implementation Plan](./plan.md)\n", encoding="utf-8")

            flow = build_flow(repo, "sample_20260323", "Done task", False)

            self.assertIn("target_confirmation", flow)
            self.assertIn("plan_confirmation", flow)
            self.assertIn("revise_prompt", flow["plan_confirmation"])


if __name__ == "__main__":
    unittest.main()
