from __future__ import annotations

import argparse
import json
from pathlib import Path

from cleanup_flow import build_cleanup_flow
from conductor_fs import (
    find_first_incomplete_task,
    find_in_progress_task,
    load_metadata,
    parse_plan,
    parse_tracks_registry,
    read_text,
    require_canonical_workspace,
    resolve_track_dir,
)
from skills_catalog import installed_skill_names, partition_recommended_skills, recommend_skills
from workflow_policy import parse_workflow_policy


def first_incomplete_track(conductor_dir: Path) -> Path:
    for entry in parse_tracks_registry(conductor_dir / "tracks.md"):
        plan_path = entry["track_dir"] / "plan.md"
        if find_in_progress_task(plan_path) or find_first_incomplete_task(plan_path):
            return entry["track_dir"]
    raise SystemExit("No incomplete track found to implement.")


def build_task_summary(track_dir: Path) -> dict[str, object]:
    repo = track_dir.parents[2]
    metadata = load_metadata(track_dir)
    plan_path = track_dir / "plan.md"
    current = find_in_progress_task(plan_path)
    next_task = current or find_first_incomplete_task(plan_path)
    phases = parse_plan(plan_path)
    workflow_text = read_text(track_dir.parents[1] / "workflow.md")
    workflow_policy = parse_workflow_policy(workflow_text)
    context = "\n".join(
        [
            read_text(track_dir.parents[1] / "tech-stack.md"),
            read_text(track_dir / "spec.md"),
            read_text(plan_path),
        ]
    )
    recommendations = recommend_skills(Path(__file__).resolve().parents[1] / "skills" / "catalog.md", context)
    skill_partition = partition_recommended_skills(recommendations, installed_skill_names(repo))
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
            "requires_git_notes": workflow_policy["requires_git_notes"],
            "requires_phase_checkpoints": workflow_policy["requires_phase_checkpoints"],
            "requires_verification_commit": workflow_policy["requires_verification_commit"],
            "coverage_target": workflow_policy["coverage_target"],
            "daily_development_commands": workflow_policy["daily_development_commands"],
            "before_commit_commands": workflow_policy["before_commit_commands"],
        },
        "skills": {
            "installed_recommendations": skill_partition["installed"],
            "missing_recommendations": skill_partition["missing"],
            "reload_required_if_installed": bool(skill_partition["missing"]),
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


def build_implement_flow(repo: Path, track_ref: str | None) -> dict[str, object]:
    conductor_dir = repo / "conductor"
    track_dir = resolve_track_dir(conductor_dir, track_ref) if track_ref else first_incomplete_track(conductor_dir)
    summary = build_task_summary(track_dir)
    summary["cleanup_options"] = build_cleanup_flow(repo, summary["track"]["track_id"])["options"]
    if track_ref:
        summary["track_confirmation"] = {
            "header": "Confirm Track",
            "question": f"I will continue implementation on '{summary['track']['title']}'. Is this correct?",
            "type": "yesno",
        }
    else:
        summary["track_prompt"] = {
            "header": "Next Track",
            "question": f"The next incomplete track is '{summary['track']['title']}'. Continue with this track?",
            "type": "yesno",
        }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--track")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    conductor_dir = repo / "conductor"
    require_canonical_workspace(conductor_dir)
    print(json.dumps(build_implement_flow(repo, args.track), indent=2))


if __name__ == "__main__":
    main()
