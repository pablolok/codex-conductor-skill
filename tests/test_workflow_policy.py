from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from workflow_policy import parse_workflow_policy  # noqa: E402


class WorkflowPolicyTests(unittest.TestCase):
    def test_parse_workflow_policy_extracts_core_flags(self) -> None:
        text = """# Workflow

## Quality Workflow

- Coverage target: 95%

## Task Workflow

8. Attach a task summary using `git notes` when supported by the repository workflow.

## Phase Completion Verification and Checkpointing Protocol

3. Run the automated verification command recorded for the track.
6. Create a checkpoint commit for the phase.
7. Attach the verification report to the checkpoint commit using `git notes` when supported.
"""
        policy = parse_workflow_policy(text)

        self.assertEqual(policy["coverage_target"], "95%")
        self.assertTrue(policy["requires_git_notes"])
        self.assertTrue(policy["requires_phase_checkpoints"])
        self.assertTrue(policy["requires_verification_commit"])

    def test_parse_workflow_policy_extracts_command_blocks(self) -> None:
        text = """# Workflow

## Development Commands

### Daily Development
```bash
npm run dev
npm test
```

### Before Committing
```bash
npm run check
```
"""
        policy = parse_workflow_policy(text)

        self.assertEqual(policy["daily_development_commands"], ["npm run dev", "npm test"])
        self.assertEqual(policy["before_commit_commands"], ["npm run check"])


if __name__ == "__main__":
    unittest.main()
