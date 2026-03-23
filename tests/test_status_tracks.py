from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


class StatusTracksTests(unittest.TestCase):
    def test_status_surfaces_verification_and_done_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            conductor = repo / "conductor"
            track_dir = conductor / "tracks" / "sample_20260323"
            track_dir.mkdir(parents=True)
            (conductor / "index.md").write_text("# Index\n", encoding="utf-8")
            (conductor / "product.md").write_text("# Product\n", encoding="utf-8")
            (conductor / "product-guidelines.md").write_text("# Guidelines\n", encoding="utf-8")
            (conductor / "tech-stack.md").write_text("# Tech Stack\n", encoding="utf-8")
            (conductor / "workflow.md").write_text(
                "# Workflow\n\n## Testing Requirements\n\n### Integration Testing\n- Test complete user flows\n- Verify database transactions\n\n## Definition of Done\n\nA task is complete when:\n1. Documentation complete (if applicable)\n5. Code passes all configured linting and static analysis checks\n",
                encoding="utf-8",
            )
            (conductor / "tracks.md").write_text(
                "---\n\n- [~] **Track: Sample Track**\n  *Link: [./tracks/sample_20260323/](./tracks/sample_20260323/)*\n",
                encoding="utf-8",
            )
            (track_dir / "metadata.json").write_text(
                '{"track_id":"sample_20260323","type":"feature","status":"in_progress","created_at":"2026-03-23T00:00:00Z","updated_at":"2026-03-23T00:00:00Z","description":"Sample Track","title":"Sample Track"}',
                encoding="utf-8",
            )
            (track_dir / "index.md").write_text("- [Plan](./plan.md)\n", encoding="utf-8")
            (track_dir / "plan.md").write_text(
                "## Phase: Phase 1\n- [~] Task: Implement API\n",
                encoding="utf-8",
            )
            (track_dir / "review.md").write_text("# Review\n", encoding="utf-8")
            (track_dir / "verify.md").write_text("# Verify\n", encoding="utf-8")
            result = subprocess.run(
                ["python", str(ROOT / "scripts" / "status_tracks.py"), "--repo", str(repo)],
                cwd=repo,
                text=True,
                capture_output=True,
                check=True,
            )

            self.assertIn("Unmet Verification Expectations: integration tests, documentation, static analysis", result.stdout)


if __name__ == "__main__":
    unittest.main()
