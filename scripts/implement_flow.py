from __future__ import annotations

import argparse
import json
from pathlib import Path

from conductor_fs import (
    find_first_incomplete_task,
    find_in_progress_task,
    load_metadata,
    parse_plan,
    read_text,
    require_canonical_workspace,
    resolve_track_dir,
)


def build_task_summary(track_dir: Path) -> dict[str, object]:
    metadata = load_metadata(track_dir)
    plan_path = track_dir / "plan.md"
    current = find_in_progress_task(plan_path)
    next_task = current or find_first_incomplete_task(plan_path)
    phases = parse_plan(plan_path)
    workflow_text = read_text(track_dir.parents[1] / "workflow.md")
    return {
        "track": {
            "track_id": metadata["track_id"],
            "title": metadata.get("title", metadata["description"]),
            "status": metadata["status"],
            "path": str(track_dir).replace("\\", "/"),
        },
        "current_task": current,
        "next_task": next_task,
        "workflow": {
            "requires_git_notes": "git notes" in workflow_text.lower(),
            "requires_phase_checkpoints": "Phase Completion Verification and Checkpointing Protocol" in workflow_text,
            "coverage_target": next((line.split(":", 1)[1].strip() for line in workflow_text.splitlines() if "Coverage target:" in line), "unspecified"),
        },
        "phases": [
            {
                "name": phase["name"],
                "checkpoint": phase["checkpoint"],
                "remaining_tasks": sum(1 for task in phase["tasks"] if task["marker"] != "x"),
            }
            for phase in phases
        ],
        "checkpoints": [
            "Select or confirm the active track.",
            "Mark the next task [~] before code changes begin.",
            "Run the workflow-required test/verification loop.",
            "Commit code for the task and record the short SHA in plan.md.",
            "Attach git notes if workflow.md requires them.",
            "If the phase is complete, run the checkpoint protocol and append the phase checkpoint SHA.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--track")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    conductor_dir = repo / "conductor"
    require_canonical_workspace(conductor_dir)
    track_dir = resolve_track_dir(conductor_dir, args.track)
    print(json.dumps(build_task_summary(track_dir), indent=2))


if __name__ == "__main__":
    main()
