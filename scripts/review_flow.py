from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from conductor_fs import load_metadata, require_canonical_workspace
from review_track import build_review_report, detect_scope
from skills_catalog import installed_skill_names, partition_recommended_skills, recommend_skills
from workflow_policy import parse_workflow_policy


def load_styleguide_context(conductor_dir: Path) -> dict[str, object]:
    styleguide_dir = conductor_dir / "code_styleguides"
    if not styleguide_dir.exists():
        return {"mode": "none", "files": [], "content": []}
    files = sorted(path for path in styleguide_dir.glob("*.md") if path.is_file())
    return {
        "mode": "law" if files else "none",
        "files": [path.name for path in files],
        "content": [path.read_text(encoding="utf-8") for path in files],
    }


def classify_diff_strategy(shortstat: str) -> dict[str, object]:
    numbers = [int(chunk.split()[0]) for chunk in shortstat.split(",") if chunk.strip() and chunk.strip()[0].isdigit()]
    total_lines = sum(numbers[1:3]) if len(numbers) >= 3 else sum(numbers[1:]) if len(numbers) > 1 else 0
    iterative = total_lines > 300
    return {
        "mode": "iterative" if iterative else "full",
        "line_estimate": total_lines,
        "requires_confirmation": iterative,
    }


def infer_test_command(repo: Path) -> str:
    if (repo / "pyproject.toml").exists() or (repo / "pytest.ini").exists():
        return "pytest"
    if (repo / "package.json").exists():
        return "npm test"
    if (repo / "go.mod").exists():
        return "go test ./..."
    if list(repo.glob("*.sln")):
        return "dotnet test"
    return "manual"


def execute_test_command(repo: Path, command: str) -> dict[str, object]:
    if command == "manual":
        return {
            "command": command,
            "status": "manual",
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "skipped": True,
        }
    result = subprocess.run(command.split(), cwd=repo, text=True, capture_output=True, check=False)
    return {
        "command": command,
        "status": "passed" if result.returncode == 0 else "failed",
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "skipped": False,
    }


def build_review_flow(repo: Path, track_ref: str | None, run_tests: bool = False) -> dict[str, object]:
    conductor_dir = repo / "conductor"
    track_dir = detect_scope(conductor_dir, track_ref)
    report = build_review_report(track_dir, repo)
    metadata = load_metadata(track_dir)
    workflow_policy = parse_workflow_policy(
        (conductor_dir / "workflow.md").read_text(encoding="utf-8") if (conductor_dir / "workflow.md").exists() else ""
    )
    strategy = classify_diff_strategy(report["shortstat"])
    test_command = infer_test_command(repo)
    test_execution = execute_test_command(repo, test_command) if run_tests else None
    styleguides = load_styleguide_context(conductor_dir)
    context = "\n".join(
        [
            (repo / "AGENTS.md").read_text(encoding="utf-8") if (repo / "AGENTS.md").exists() else "",
            (conductor_dir / "product-guidelines.md").read_text(encoding="utf-8") if (conductor_dir / "product-guidelines.md").exists() else "",
            (track_dir.parents[1] / "tech-stack.md").read_text(encoding="utf-8") if (track_dir.parents[1] / "tech-stack.md").exists() else "",
            (track_dir / "spec.md").read_text(encoding="utf-8") if (track_dir / "spec.md").exists() else "",
            (track_dir / "plan.md").read_text(encoding="utf-8") if (track_dir / "plan.md").exists() else "",
            *styleguides["content"],
        ]
    )
    recommendations = recommend_skills(Path(__file__).resolve().parents[1] / "skills" / "catalog.md", context)
    skill_partition = partition_recommended_skills(recommendations, installed_skill_names(repo))
    return {
        "track": {
            "track_id": metadata["track_id"],
            "title": metadata.get("title", metadata["description"]),
            "path": str(track_dir).replace("\\", "/"),
        },
        "scope": report,
        "diff_strategy": strategy,
        "styleguides": {
            "mode": styleguides["mode"],
            "files": styleguides["files"],
        },
        "workflow": {
            "required_test_categories": workflow_policy["required_test_categories"],
            "definition_of_done": workflow_policy["definition_of_done"],
            "requires_manual_verification": workflow_policy["requires_manual_verification"],
            "requires_static_analysis": workflow_policy["requires_static_analysis"],
            "requires_security_review": workflow_policy["requires_security_review"],
            "requires_documentation_updates": workflow_policy["requires_documentation_updates"],
        },
        "test_command": test_command,
        "test_execution": test_execution,
        "skills": {
            "installed_recommendations": skill_partition["installed"],
            "missing_recommendations": skill_partition["missing"],
            "reload_required_if_installed": bool(skill_partition["missing"]),
        },
        "scope_confirmation": {
            "header": "Confirm Scope",
            "question": f"I will review '{metadata.get('title', metadata['description'])}'. Is this correct?",
            "type": "yesno",
        },
        "large_review_confirmation": {
            "header": "Large Review",
            "question": "This review involves more than 300 changed lines. Proceed with iterative review mode?",
            "type": "yesno",
        }
        if strategy["requires_confirmation"]
        else None,
        "decision_question": {
            "header": "Decision",
            "question": "How would you like to proceed with the findings?",
            "type": "choice",
            "multiSelect": False,
            "options": [
                {"label": "Apply Fixes", "description": "Apply the suggested fixes automatically."},
                {"label": "Manual Fix", "description": "Stop so the user can address findings manually."},
                {"label": "Complete Track", "description": "Proceed without applying the suggested fixes."},
            ],
        },
        "checkpoints": [
            "Review against spec.md, plan.md, workflow.md, and AGENTS.md.",
            "Check the workflow-defined testing requirements and definition of done before finalizing findings.",
            "Confirm the diff range is correct before reviewing findings.",
            "Record findings first, then risks, open gaps, and decision in review.md.",
            "If fixes are required, append a review-fix task before resuming implementation.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--track")
    parser.add_argument("--run-tests", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    require_canonical_workspace(repo / "conductor")
    print(json.dumps(build_review_flow(repo, args.track, run_tests=args.run_tests), indent=2))


if __name__ == "__main__":
    main()
