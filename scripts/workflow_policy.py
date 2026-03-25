from __future__ import annotations

import re


def extract_coverage_target(workflow_text: str) -> str:
    explicit_match = re.search(r"Coverage target:\s*(.+)", workflow_text, re.IGNORECASE)
    if explicit_match:
        return explicit_match.group(1).strip()

    high_coverage_match = re.search(r"Aim for\s*(>[0-9]+%)\s*code coverage", workflow_text, re.IGNORECASE)
    if high_coverage_match:
        return high_coverage_match.group(1)

    quality_gate_match = re.search(r"Code coverage meets requirements\s*\(([^)]+)\)", workflow_text, re.IGNORECASE)
    if quality_gate_match:
        return quality_gate_match.group(1).strip()

    checklist_match = re.search(r"Coverage adequate\s*\(([^)]+)\)", workflow_text, re.IGNORECASE)
    if checklist_match:
        return checklist_match.group(1).strip()

    return "unspecified"


def extract_command_block(workflow_text: str, heading: str) -> list[str]:
    pattern = re.compile(
        rf"###\s+{re.escape(heading)}\s*```(?:\w+)?\n(?P<body>.*?)```",
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(workflow_text)
    if not match:
        return []
    return [line.strip() for line in match.group("body").splitlines() if line.strip()]


def has_quality_gate(workflow_text: str, fragment: str) -> bool:
    return fragment.lower() in workflow_text.lower()


def extract_section(workflow_text: str, heading: str) -> str:
    pattern = re.compile(
        rf"##\s+{re.escape(heading)}\s*(?P<body>.*?)(?=\n##\s+|\Z)",
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(workflow_text)
    return match.group("body") if match else ""


def extract_required_test_categories(workflow_text: str) -> list[str]:
    section = extract_section(workflow_text, "Testing Requirements")
    categories: list[str] = []
    for label, name in (
        ("Unit Testing", "unit"),
        ("Integration Testing", "integration"),
        ("Mobile Testing", "mobile"),
    ):
        if re.search(rf"###\s+{re.escape(label)}", section, re.IGNORECASE):
            categories.append(name)
    return categories


def extract_definition_of_done(workflow_text: str) -> dict[str, bool]:
    section = extract_section(workflow_text, "Definition of Done").lower()
    return {
        "tests": "unit tests written and passing" in section or "all tests passing" in section,
        "coverage": "coverage meets" in section or "coverage adequate" in section,
        "documentation": "documentation complete" in section,
        "static_analysis": "linting and static analysis" in section or "linting" in section,
        "mobile": "works beautifully on mobile" in section or "mobile" in section,
        "git_notes": "git note" in section or "git notes" in section,
    }


def parse_workflow_policy(workflow_text: str) -> dict[str, object]:
    has_phase_protocol = "Phase Completion Verification and Checkpointing Protocol" in workflow_text
    lowered = workflow_text.lower()
    return {
        "coverage_target": extract_coverage_target(workflow_text),
        "requires_git_notes": "git notes" in lowered,
        "requires_tdd": "test-driven development" in lowered or "write failing tests" in lowered,
        "requires_manual_verification": has_phase_protocol and "await explicit user feedback" in lowered,
        "requires_phase_checkpoints": has_phase_protocol,
        "requires_verification_commit": has_phase_protocol
        and ("create a checkpoint commit" in lowered or "create checkpoint commit" in lowered),
        "ci_aware_commands": "ci=true" in workflow_text or "non-interactive & ci-aware" in lowered,
        "requires_documentation_updates": has_quality_gate(workflow_text, "documentation updated if needed")
        or has_quality_gate(workflow_text, "all public functions/methods are documented"),
        "requires_type_safety": has_quality_gate(workflow_text, "type safety is enforced"),
        "requires_static_analysis": has_quality_gate(workflow_text, "no linting or static analysis errors"),
        "requires_mobile_verification": has_quality_gate(workflow_text, "works correctly on mobile"),
        "requires_security_review": has_quality_gate(workflow_text, "no security vulnerabilities introduced"),
        "required_test_categories": extract_required_test_categories(workflow_text),
        "definition_of_done": extract_definition_of_done(workflow_text),
        "setup_commands": extract_command_block(workflow_text, "Setup"),
        "daily_development_commands": extract_command_block(workflow_text, "Daily Development"),
        "before_commit_commands": extract_command_block(workflow_text, "Before Committing"),
    }
