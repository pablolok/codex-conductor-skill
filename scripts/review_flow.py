from __future__ import annotations

import argparse
import json
from pathlib import Path

from conductor_fs import load_metadata, require_canonical_workspace
from review_track import build_review_report, detect_scope


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


def build_review_flow(repo: Path, track_ref: str | None) -> dict[str, object]:
    conductor_dir = repo / "conductor"
    track_dir = detect_scope(conductor_dir, track_ref)
    report = build_review_report(track_dir, repo)
    metadata = load_metadata(track_dir)
    strategy = classify_diff_strategy(report["shortstat"])
    return {
        "track": {
            "track_id": metadata["track_id"],
            "title": metadata.get("title", metadata["description"]),
            "path": str(track_dir).replace("\\", "/"),
        },
        "scope": report,
        "diff_strategy": strategy,
        "test_command": infer_test_command(repo),
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
            "Confirm the diff range is correct before reviewing findings.",
            "Record findings first, then risks, open gaps, and decision in review.md.",
            "If fixes are required, append a review-fix task before resuming implementation.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--track")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    require_canonical_workspace(repo / "conductor")
    print(json.dumps(build_review_flow(repo, args.track), indent=2))


if __name__ == "__main__":
    main()
