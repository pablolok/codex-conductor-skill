from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from cleanup_flow import build_cleanup_flow
from conductor_fs import (
    find_first_incomplete_task,
    find_in_progress_task,
    load_metadata,
    parse_plan,
    refresh_portfolio_indexes,
    refresh_track_index,
    require_canonical_workspace,
    resolve_track_dir,
    update_phase_checkpoint,
    update_registry_entry_status,
    update_task_marker,
    read_text,
    write_metadata,
)
from implement_flow import build_implement_flow
from sync_project_docs import apply_sync_payload, build_sync_payload


def template_base() -> Path:
    return Path(__file__).resolve().parents[1]


def sync_indexes(conductor_dir: Path, track_dir: Path) -> None:
    refresh_track_index(track_dir, template_base())
    refresh_portfolio_indexes(conductor_dir, template_base())


def mark_track_status(repo: Path, track_dir: Path, status: str) -> dict:
    conductor_dir = repo / "conductor"
    metadata = load_metadata(track_dir)
    metadata["status"] = status
    write_metadata(track_dir, metadata)
    update_registry_entry_status(conductor_dir, template_base(), metadata["track_id"], status)
    sync_indexes(conductor_dir, track_dir)
    return metadata


def current_or_next_task(track_dir: Path) -> dict | None:
    plan_path = track_dir / "plan.md"
    return find_in_progress_task(plan_path) or find_first_incomplete_task(plan_path)


def workflow_requires_phase_checkpoint(track_dir: Path) -> bool:
    workflow_text = read_text(track_dir.parents[1] / "workflow.md")
    return "Phase Completion Verification and Checkpointing Protocol" in workflow_text


def workflow_requires_git_notes(track_dir: Path) -> bool:
    workflow_text = read_text(track_dir.parents[1] / "workflow.md")
    return "git notes" in workflow_text.lower()


def phase_has_remaining_tasks(track_dir: Path, phase_name: str) -> bool:
    for phase in parse_plan(track_dir / "plan.md"):
        if phase["name"] == phase_name:
            return any(task["marker"] != "x" for task in phase["tasks"])
    raise SystemExit(f"Phase '{phase_name}' not found in plan.")


def find_phase_line(track_dir: Path, phase_name: str) -> int:
    for phase in parse_plan(track_dir / "plan.md"):
        if phase["name"] == phase_name:
            return phase["line_number"]
    raise SystemExit(f"Phase '{phase_name}' not found in plan.")


def find_pending_checkpoint_phase(track_dir: Path) -> str | None:
    for phase in parse_plan(track_dir / "plan.md"):
        if phase["checkpoint"]:
            continue
        if phase["tasks"] and all(task["marker"] == "x" for task in phase["tasks"]):
            return phase["name"]
    return None


def active_task(track_dir: Path) -> dict:
    task = find_in_progress_task(track_dir / "plan.md")
    if task is None:
        raise SystemExit("No in-progress task found.")
    return task


def phase_will_complete_after_current(track_dir: Path, phase_name: str) -> bool:
    for phase in parse_plan(track_dir / "plan.md"):
        if phase["name"] != phase_name:
            continue
        remaining = [task for task in phase["tasks"] if task["marker"] != "x"]
        return len(remaining) == 1 and remaining[0]["marker"] == "~"
    raise SystemExit(f"Phase '{phase_name}' not found in plan.")


def start_task(track_dir: Path) -> dict:
    plan_path = track_dir / "plan.md"
    task = find_in_progress_task(plan_path)
    if task is None:
        task = find_first_incomplete_task(plan_path)
        if task is None:
            raise SystemExit("No incomplete tasks remain in the selected plan.")
        update_task_marker(plan_path, task["line_number"], "~")
        task = find_in_progress_task(plan_path) or task
    return task


def complete_task(track_dir: Path, sha: str | None, activate_next: bool = True) -> tuple[dict, dict | None]:
    plan_path = track_dir / "plan.md"
    task = find_in_progress_task(plan_path)
    if task is None:
        raise SystemExit("No in-progress task found to complete.")
    update_task_marker(plan_path, task["line_number"], "x", sha=sha)
    next_task = find_first_incomplete_task(plan_path)
    if next_task is None:
        return task, None
    if activate_next:
        update_task_marker(plan_path, next_task["line_number"], "~")
        next_task = find_in_progress_task(plan_path) or next_task
    return task, next_task


def build_phase_checkpoint_state(repo: Path, track_dir: Path, completed_task: dict, next_task: dict | None) -> dict[str, object]:
    metadata = load_metadata(track_dir)
    return {
        "stage": "phase_checkpoint",
        "track": {
            "track_id": metadata["track_id"],
            "title": metadata.get("title", metadata["description"]),
            "status": metadata["status"],
        },
        "phase": {
            "name": completed_task["phase"],
            "requires_git_notes": workflow_requires_git_notes(track_dir),
        },
        "completed_task": completed_task,
        "next_task": next_task,
        "checkpoint_question": {
            "header": "Checkpoint Phase",
            "question": f"Phase '{completed_task['phase']}' is complete. Run verification and record a checkpoint before continuing?",
            "type": "yesno",
        },
    }


def run_commit_task(
    repo: Path,
    track_ref: str,
    code_message: str,
    plan_message: str,
    note_summary: str | None,
    phase_checkpoint: str | None,
    verify_message: str | None,
    paths: list[str] | None,
) -> dict[str, object]:
    command = [
        "python",
        str(Path(__file__).resolve().parent / "commit_task.py"),
        "--repo",
        str(repo),
        "--track",
        track_ref,
        "--code-message",
        code_message,
        "--plan-message",
        plan_message,
    ]
    if note_summary:
        command.extend(["--note-summary", note_summary])
    if phase_checkpoint:
        command.extend(["--phase-checkpoint", phase_checkpoint])
    if verify_message:
        command.extend(["--verify-message", verify_message])
    if paths:
        command.extend(["--paths", *paths])
    result = subprocess.run(command, cwd=repo, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise SystemExit(result.stderr.strip() or result.stdout.strip() or "commit_task.py failed")
    output = result.stdout.strip()
    json_start = output.rfind("{")
    if json_start == -1:
        raise SystemExit("commit_task.py did not return a JSON payload.")
    return json.loads(output[json_start:])


def advance_implement_runtime(
    repo: Path,
    track_ref: str | None,
    action: str,
    sha: str | None = None,
    code_message: str | None = None,
    plan_message: str | None = None,
    note_summary: str | None = None,
    verify_message: str | None = None,
    paths: list[str] | None = None,
    approved_paths: list[str] | None = None,
) -> dict[str, object]:
    conductor_dir = repo / "conductor"
    require_canonical_workspace(conductor_dir)
    track_dir = resolve_track_dir(conductor_dir, track_ref)

    if action == "start":
        metadata = mark_track_status(repo, track_dir, "in_progress")
        task = start_task(track_dir)
        sync_indexes(conductor_dir, track_dir)
        return {
            "stage": "task_execution",
            "track": {
                "track_id": metadata["track_id"],
                "title": metadata.get("title", metadata["description"]),
                "status": metadata["status"],
            },
            "current_task": task,
            "flow": build_implement_flow(repo, metadata["track_id"]),
        }

    if action == "complete_task":
        requires_checkpoint = workflow_requires_phase_checkpoint(track_dir)
        completed_task, next_task = complete_task(track_dir, sha, activate_next=not requires_checkpoint)
        sync_indexes(conductor_dir, track_dir)
        if requires_checkpoint and not phase_has_remaining_tasks(track_dir, completed_task["phase"]):
            return build_phase_checkpoint_state(repo, track_dir, completed_task, next_task)
        if requires_checkpoint and next_task is not None and find_in_progress_task(track_dir / "plan.md") is None:
            update_task_marker(track_dir / "plan.md", next_task["line_number"], "~")
            sync_indexes(conductor_dir, track_dir)
            next_task = find_in_progress_task(track_dir / "plan.md") or next_task
        if next_task is not None:
            metadata = load_metadata(track_dir)
            return {
                "stage": "task_execution",
                "track": {
                    "track_id": metadata["track_id"],
                    "title": metadata.get("title", metadata["description"]),
                    "status": metadata["status"],
                },
                "current_task": next_task,
                "flow": build_implement_flow(repo, metadata["track_id"]),
            }

        metadata = mark_track_status(repo, track_dir, "completed")
        return {
            "stage": "doc_sync",
            "track": {
                "track_id": metadata["track_id"],
                "title": metadata.get("title", metadata["description"]),
                "status": metadata["status"],
            },
            "doc_sync": build_sync_payload(repo, metadata["track_id"]),
            "cleanup_options": build_cleanup_flow(repo, metadata["track_id"])["options"],
        }

    if action == "checkpoint_phase":
        if not sha:
            raise SystemExit("checkpoint_phase requires a checkpoint sha.")
        phase_name = find_pending_checkpoint_phase(track_dir)
        if phase_name is None:
            raise SystemExit("No completed phase is waiting for a checkpoint.")
        update_phase_checkpoint(track_dir / "plan.md", find_phase_line(track_dir, phase_name), sha)
        next_task = find_first_incomplete_task(track_dir / "plan.md")
        if next_task is not None and find_in_progress_task(track_dir / "plan.md") is None:
            update_task_marker(track_dir / "plan.md", next_task["line_number"], "~")
            sync_indexes(conductor_dir, track_dir)
            metadata = load_metadata(track_dir)
            return {
                "stage": "task_execution",
                "track": {
                    "track_id": metadata["track_id"],
                    "title": metadata.get("title", metadata["description"]),
                    "status": metadata["status"],
                },
                "current_task": find_in_progress_task(track_dir / "plan.md") or next_task,
                "flow": build_implement_flow(repo, metadata["track_id"]),
            }
        sync_indexes(conductor_dir, track_dir)
        metadata = mark_track_status(repo, track_dir, "completed")
        return {
            "stage": "doc_sync",
            "track": {
                "track_id": metadata["track_id"],
                "title": metadata.get("title", metadata["description"]),
                "status": metadata["status"],
            },
            "doc_sync": build_sync_payload(repo, metadata["track_id"]),
            "cleanup_options": build_cleanup_flow(repo, metadata["track_id"])["options"],
        }

    if action == "commit_task":
        if not track_ref:
            raise SystemExit("commit_task requires a track.")
        if not code_message or not plan_message:
            raise SystemExit("commit_task requires code_message and plan_message.")
        current = active_task(track_dir)
        auto_phase_checkpoint = None
        if (
            verify_message
            and workflow_requires_phase_checkpoint(track_dir)
            and phase_will_complete_after_current(track_dir, current["phase"])
        ):
            auto_phase_checkpoint = current["phase"]
        result = run_commit_task(
            repo,
            track_ref,
            code_message,
            plan_message,
            note_summary,
            auto_phase_checkpoint,
            verify_message,
            paths,
        )
        sync_indexes(conductor_dir, track_dir)
        pending_phase = find_pending_checkpoint_phase(track_dir)
        if workflow_requires_phase_checkpoint(track_dir) and pending_phase:
            next_task = find_first_incomplete_task(track_dir / "plan.md")
            return build_phase_checkpoint_state(
                repo,
                track_dir,
                {"title": str(result["task"]), "phase": pending_phase},
                next_task,
            )
        next_task = find_first_incomplete_task(track_dir / "plan.md")
        if next_task is not None and find_in_progress_task(track_dir / "plan.md") is None:
            update_task_marker(track_dir / "plan.md", next_task["line_number"], "~")
            sync_indexes(conductor_dir, track_dir)
            metadata = load_metadata(track_dir)
            return {
                "stage": "task_execution",
                "track": {
                    "track_id": metadata["track_id"],
                    "title": metadata.get("title", metadata["description"]),
                    "status": metadata["status"],
                },
                "current_task": find_in_progress_task(track_dir / "plan.md") or next_task,
                "commit_result": result,
                "flow": build_implement_flow(repo, metadata["track_id"]),
            }
        metadata = mark_track_status(repo, track_dir, "completed")
        return {
            "stage": "doc_sync",
            "track": {
                "track_id": metadata["track_id"],
                "title": metadata.get("title", metadata["description"]),
                "status": metadata["status"],
            },
            "commit_result": result,
            "doc_sync": build_sync_payload(repo, metadata["track_id"]),
            "cleanup_options": build_cleanup_flow(repo, metadata["track_id"])["options"],
        }

    if action == "doc_sync_execute":
        if not track_ref:
            raise SystemExit("doc_sync_execute requires a track.")
        payload = build_sync_payload(repo, track_ref)
        apply_sync_payload(payload, approved_paths=set(approved_paths or []))
        metadata = load_metadata(track_dir)
        return {
            "stage": "cleanup",
            "track": {
                "track_id": track_dir.name,
                "title": metadata.get("title", metadata["description"]),
            },
            "cleanup": build_cleanup_flow(repo, track_ref),
        }

    raise SystemExit(f"Unsupported implement runtime action '{action}'.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--track")
    parser.add_argument("--action", choices=["start", "complete_task", "checkpoint_phase", "commit_task", "doc_sync_execute"], required=True)
    parser.add_argument("--sha")
    parser.add_argument("--code-message")
    parser.add_argument("--plan-message")
    parser.add_argument("--note-summary")
    parser.add_argument("--verify-message")
    parser.add_argument("--paths", nargs="*")
    parser.add_argument("--approved-paths", nargs="*")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    print(
        json.dumps(
            advance_implement_runtime(
                repo,
                args.track,
                args.action,
                args.sha,
                args.code_message,
                args.plan_message,
                args.note_summary,
                args.verify_message,
                args.paths,
                args.approved_paths,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
