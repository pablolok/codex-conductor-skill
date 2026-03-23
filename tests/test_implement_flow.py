from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from implement_flow import build_implement_flow  # noqa: E402


class ImplementFlowTests(unittest.TestCase):
    def test_implement_flow_without_track_prompts_next_incomplete_track(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            conductor_dir = repo / "conductor"
            track_dir = conductor_dir / "tracks" / "sample_20260323"
            track_dir.mkdir(parents=True)
            (conductor_dir / "tech-stack.md").write_text("# Stack\n", encoding="utf-8")
            (conductor_dir / "workflow.md").write_text("# Workflow\n", encoding="utf-8")
            (conductor_dir / "tracks.md").write_text(
                "---\n\n- [ ] **Track: Sample Track**\n  *Link: [./tracks/sample_20260323/](./tracks/sample_20260323/)*\n",
                encoding="utf-8",
            )
            (track_dir / "metadata.json").write_text(
                '{"track_id":"sample_20260323","type":"feature","status":"new","created_at":"2026-03-23T00:00:00Z","updated_at":"2026-03-23T00:00:00Z","description":"Sample Track","title":"Sample Track"}',
                encoding="utf-8",
            )
            (track_dir / "spec.md").write_text("Spec\n", encoding="utf-8")
            (track_dir / "plan.md").write_text("## Phase: Phase 1\n- [ ] Task: Do work\n", encoding="utf-8")
            (track_dir / "index.md").write_text("- [Specification](./spec.md)\n- [Implementation Plan](./plan.md)\n", encoding="utf-8")

            flow = build_implement_flow(repo, None)

            self.assertIn("track_prompt", flow)
            self.assertEqual(flow["track_prompt"]["header"], "Next Track")
            self.assertEqual(flow["track"]["track_id"], "sample_20260323")

    def test_implement_flow_with_track_adds_confirmation_and_cleanup_choices(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            conductor_dir = repo / "conductor"
            track_dir = conductor_dir / "tracks" / "sample_20260323"
            track_dir.mkdir(parents=True)
            (conductor_dir / "tech-stack.md").write_text("# Stack\n", encoding="utf-8")
            (conductor_dir / "workflow.md").write_text("# Workflow\n", encoding="utf-8")
            (conductor_dir / "tracks.md").write_text(
                "---\n\n- [ ] **Track: Sample Track**\n  *Link: [./tracks/sample_20260323/](./tracks/sample_20260323/)*\n",
                encoding="utf-8",
            )
            (track_dir / "metadata.json").write_text(
                '{"track_id":"sample_20260323","type":"feature","status":"new","created_at":"2026-03-23T00:00:00Z","updated_at":"2026-03-23T00:00:00Z","description":"Sample Track","title":"Sample Track"}',
                encoding="utf-8",
            )
            (track_dir / "spec.md").write_text("Spec\n", encoding="utf-8")
            (track_dir / "plan.md").write_text("## Phase: Phase 1\n- [ ] Task: Do work\n", encoding="utf-8")
            (track_dir / "index.md").write_text("- [Specification](./spec.md)\n- [Implementation Plan](./plan.md)\n", encoding="utf-8")

            flow = build_implement_flow(repo, "sample_20260323")

            self.assertIn("track_confirmation", flow)
            self.assertIn("cleanup_options", flow)

    def test_implement_flow_surfaces_workflow_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            conductor_dir = repo / "conductor"
            track_dir = conductor_dir / "tracks" / "sample_20260323"
            track_dir.mkdir(parents=True)
            (conductor_dir / "tracks.md").write_text(
                "---\n\n- [~] **Track: Sample Track**\n  *Link: [./tracks/sample_20260323/](./tracks/sample_20260323/)*\n",
                encoding="utf-8",
            )
            (conductor_dir / "workflow.md").write_text(
                "# Workflow\n\n## Development Commands\n\n### Daily Development\n```bash\nnpm run dev\n```\n\n### Before Committing\n```bash\nnpm run check\n```\n",
                encoding="utf-8",
            )
            (conductor_dir / "tech-stack.md").write_text("# Tech Stack\n", encoding="utf-8")
            (track_dir / "metadata.json").write_text(
                '{"track_id":"sample_20260323","type":"feature","status":"in_progress","created_at":"2026-03-23T00:00:00Z","updated_at":"2026-03-23T00:00:00Z","description":"Sample Track","title":"Sample Track"}',
                encoding="utf-8",
            )
            (track_dir / "spec.md").write_text("# Specification\n", encoding="utf-8")
            (track_dir / "plan.md").write_text("## Phase: Phase 1\n- [~] Task: Do work\n", encoding="utf-8")
            (track_dir / "index.md").write_text("- [Specification](./spec.md)\n- [Implementation Plan](./plan.md)\n", encoding="utf-8")
            (track_dir / "review.md").write_text("# Review\n", encoding="utf-8")
            (track_dir / "verify.md").write_text("# Verify\n", encoding="utf-8")

            flow = build_implement_flow(repo, "sample_20260323")

            self.assertEqual(flow["workflow"]["daily_development_commands"], ["npm run dev"])
            self.assertEqual(flow["workflow"]["before_commit_commands"], ["npm run check"])
            labels = [item["label"] for item in flow["cleanup_options"]]
            self.assertEqual(labels, ["Review", "Archive", "Delete", "Skip"])


if __name__ == "__main__":
    unittest.main()
