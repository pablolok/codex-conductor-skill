from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sync_project_docs import build_sync_payload  # noqa: E402


class SyncProjectDocsTests(unittest.TestCase):
    def test_sync_payload_includes_approval_questions_with_diff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            conductor_dir = repo / "conductor"
            track_dir = conductor_dir / "tracks" / "sample_20260323"
            track_dir.mkdir(parents=True)
            (conductor_dir / "index.md").write_text(
                "- [Product Definition](./product.md)\n- [Tech Stack](./tech-stack.md)\n- [Product Guidelines](./product-guidelines.md)\n",
                encoding="utf-8",
            )
            (conductor_dir / "tracks.md").write_text(
                "---\n\n- [x] **Track: Sample Track**\n  *Link: [./tracks/sample_20260323/](./tracks/sample_20260323/)*\n",
                encoding="utf-8",
            )
            (conductor_dir / "product.md").write_text("# Product\n\nCurrent product.\n", encoding="utf-8")
            (conductor_dir / "tech-stack.md").write_text("# Tech Stack\n\nCurrent stack.\n", encoding="utf-8")
            (conductor_dir / "product-guidelines.md").write_text("# Product Guidelines\n\nCurrent guidelines.\n", encoding="utf-8")
            (track_dir / "index.md").write_text("- [Specification](./spec.md)\n", encoding="utf-8")
            (track_dir / "spec.md").write_text(
                "# Specification\n\n## Goal\n\nAdd API support for synced auth state.\n",
                encoding="utf-8",
            )

            payload = build_sync_payload(repo, "sample_20260323")

            self.assertIn("approval_questions", payload)
            self.assertEqual(payload["approval_questions"][0]["header"], "Product")
            self.assertIn("---", payload["approval_questions"][0]["question"])
            self.assertIn("+## Latest Track Sync", payload["approval_questions"][0]["question"])

    def test_sync_payload_skips_questions_when_no_meaningful_change_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            conductor_dir = repo / "conductor"
            track_dir = conductor_dir / "tracks" / "sample_20260323"
            track_dir.mkdir(parents=True)
            (conductor_dir / "index.md").write_text(
                "- [Product Definition](./product.md)\n- [Tech Stack](./tech-stack.md)\n- [Product Guidelines](./product-guidelines.md)\n",
                encoding="utf-8",
            )
            (conductor_dir / "tracks.md").write_text(
                "---\n\n- [x] **Track: Sample Track**\n  *Link: [./tracks/sample_20260323/](./tracks/sample_20260323/)*\n",
                encoding="utf-8",
            )
            (conductor_dir / "product.md").write_text("# Product\n\nCurrent product.\n", encoding="utf-8")
            (conductor_dir / "tech-stack.md").write_text("# Tech Stack\n\nCurrent stack.\n", encoding="utf-8")
            (conductor_dir / "product-guidelines.md").write_text("# Product Guidelines\n\nCurrent guidelines.\n", encoding="utf-8")
            (track_dir / "index.md").write_text("- [Specification](./spec.md)\n", encoding="utf-8")
            (track_dir / "spec.md").write_text("# Specification\n\n## Goal\n\nFix a typo in a help page.\n", encoding="utf-8")

            payload = build_sync_payload(repo, "sample_20260323")

            self.assertEqual(payload["approval_questions"], [])
            self.assertEqual(payload["summary"]["product_definition"], "no_change")
            self.assertEqual(payload["summary"]["tech_stack"], "no_change")
            self.assertEqual(payload["summary"]["product_guidelines"], "no_change")


if __name__ == "__main__":
    unittest.main()
