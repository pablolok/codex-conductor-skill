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

    def test_implement_flow_surfaces_additional_workflow_quality_rules(self) -> None:
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
                "# Workflow\n\n## Guiding Principles\n\n3. **Test-Driven Development:** Write unit tests before implementing functionality\n6. **Non-Interactive & CI-Aware:** Prefer non-interactive commands. Use `CI=true` for watch-mode tools.\n\n## Phase Completion Verification and Checkpointing Protocol\n\n4. Propose a Detailed, Actionable Manual Verification Plan\n5. Await Explicit User Feedback\n\n### Setup\n```bash\nnpm install\n```\n\n### Quality Gates\n- [ ] Type safety is enforced\n- [ ] No linting or static analysis errors\n- [ ] Documentation updated if needed\n- [ ] No security vulnerabilities introduced\n",
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

            flow = build_implement_flow(repo, "sample_20260323")

            self.assertTrue(flow["workflow"]["requires_tdd"])
            self.assertTrue(flow["workflow"]["requires_manual_verification"])
            self.assertTrue(flow["workflow"]["ci_aware_commands"])
            self.assertTrue(flow["workflow"]["requires_type_safety"])
            self.assertTrue(flow["workflow"]["requires_static_analysis"])
            self.assertTrue(flow["workflow"]["requires_documentation_updates"])
            self.assertTrue(flow["workflow"]["requires_security_review"])
            self.assertEqual(flow["workflow"]["setup_commands"], ["npm install"])

    def test_implement_flow_surfaces_testing_requirements_and_done_criteria(self) -> None:
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
                "# Workflow\n\n## Testing Requirements\n\n### Unit Testing\n- Every module must have corresponding tests.\n\n### Integration Testing\n- Test complete user flows\n\n## Definition of Done\n\nA task is complete when:\n1. Unit tests written and passing\n2. Documentation complete (if applicable)\n3. Code passes all configured linting and static analysis checks\n",
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

            flow = build_implement_flow(repo, "sample_20260323")

            self.assertEqual(flow["workflow"]["required_test_categories"], ["unit", "integration"])
            self.assertTrue(flow["workflow"]["definition_of_done"]["tests"])
            self.assertTrue(flow["workflow"]["definition_of_done"]["documentation"])
            self.assertTrue(flow["workflow"]["definition_of_done"]["static_analysis"])


if __name__ == "__main__":
    unittest.main()
