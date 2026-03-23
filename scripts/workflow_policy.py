from __future__ import annotations

import re


def extract_command_block(workflow_text: str, heading: str) -> list[str]:
    pattern = re.compile(
        rf"###\s+{re.escape(heading)}\s*```(?:\w+)?\n(?P<body>.*?)```",
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(workflow_text)
    if not match:
        return []
    return [line.strip() for line in match.group("body").splitlines() if line.strip()]


def parse_workflow_policy(workflow_text: str) -> dict[str, object]:
    coverage_match = re.search(r"Coverage target:\s*(.+)", workflow_text, re.IGNORECASE)
    has_phase_protocol = "Phase Completion Verification and Checkpointing Protocol" in workflow_text
    lowered = workflow_text.lower()
    return {
        "coverage_target": coverage_match.group(1).strip() if coverage_match else "unspecified",
        "requires_git_notes": "git notes" in lowered,
        "requires_phase_checkpoints": has_phase_protocol,
        "requires_verification_commit": has_phase_protocol and "create a checkpoint commit" in lowered,
        "daily_development_commands": extract_command_block(workflow_text, "Daily Development"),
        "before_commit_commands": extract_command_block(workflow_text, "Before Committing"),
    }
