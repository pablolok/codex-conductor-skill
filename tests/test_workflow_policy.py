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

    def test_parse_workflow_policy_extracts_execution_and_quality_rules(self) -> None:
        text = """# Workflow

## Guiding Principles

3. **Test-Driven Development:** Write unit tests before implementing functionality
6. **Non-Interactive & CI-Aware:** Prefer non-interactive commands. Use `CI=true` for watch-mode tools (tests, linters) to ensure single execution.

### Setup
```bash
npm install
```

## Phase Completion Verification and Checkpointing Protocol

4. Propose a Detailed, Actionable Manual Verification Plan
5. Await Explicit User Feedback

### Quality Gates

- [ ] All public functions/methods are documented
- [ ] Type safety is enforced
- [ ] No linting or static analysis errors
- [ ] Works correctly on mobile (if applicable)
- [ ] Documentation updated if needed
- [ ] No security vulnerabilities introduced
"""
        policy = parse_workflow_policy(text)

        self.assertTrue(policy["requires_tdd"])
        self.assertTrue(policy["requires_manual_verification"])
        self.assertTrue(policy["ci_aware_commands"])
        self.assertTrue(policy["requires_documentation_updates"])
        self.assertTrue(policy["requires_type_safety"])
        self.assertTrue(policy["requires_static_analysis"])
        self.assertTrue(policy["requires_mobile_verification"])
        self.assertTrue(policy["requires_security_review"])
        self.assertEqual(policy["setup_commands"], ["npm install"])

    def test_parse_workflow_policy_extracts_testing_requirements_and_definition_of_done(self) -> None:
        text = """# Workflow

## Testing Requirements

### Unit Testing
- Every module must have corresponding tests.

### Integration Testing
- Test complete user flows
- Verify database transactions

### Mobile Testing
- Test on actual iPhone when possible

## Definition of Done

A task is complete when:

1. Unit tests written and passing
2. Code coverage meets project requirements
3. Documentation complete (if applicable)
4. Code passes all configured linting and static analysis checks
5. Works beautifully on mobile (if applicable)
6. Git note with task summary attached to the commit
"""
        policy = parse_workflow_policy(text)

        self.assertEqual(policy["required_test_categories"], ["unit", "integration", "mobile"])
        self.assertTrue(policy["definition_of_done"]["tests"])
        self.assertTrue(policy["definition_of_done"]["coverage"])
        self.assertTrue(policy["definition_of_done"]["documentation"])
        self.assertTrue(policy["definition_of_done"]["static_analysis"])
        self.assertTrue(policy["definition_of_done"]["mobile"])
        self.assertTrue(policy["definition_of_done"]["git_notes"])


if __name__ == "__main__":
    unittest.main()
