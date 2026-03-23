from __future__ import annotations

import argparse
import json
from pathlib import Path

from cleanup_flow import build_cleanup_flow
from conductor_fs import (
    find_first_incomplete_task,
    find_in_progress_task,
    load_metadata,
    refresh_portfolio_indexes,
    refresh_track_index,
    require_canonical_workspace,
    resolve_track_dir,
    update_registry_entry_status,
    update_task_marker,
    write_metadata,
)
from implement_flow import build_implement_flow
from sync_project_docs import build_sync_payload


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


def complete_task(track_dir: Path, sha: str | None) -> dict | None:
    plan_path = track_dir / "plan.md"
    task = find_in_progress_task(plan_path)
    if task is None:
        raise SystemExit("No in-progress task found to complete.")
    update_task_marker(plan_path, task["line_number"], "x", sha=sha)
    next_task = find_first_incomplete_task(plan_path)
    if next_task is None:
        return None
    update_task_marker(plan_path, next_task["line_number"], "~")
    return find_in_progress_task(plan_path) or next_task


def advance_implement_runtime(repo: Path, track_ref: str | None, action: str, sha: str | None = None) -> dict[str, object]:
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
        next_task = complete_task(track_dir, sha)
        sync_indexes(conductor_dir, track_dir)
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

    raise SystemExit(f"Unsupported implement runtime action '{action}'.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--track")
    parser.add_argument("--action", choices=["start", "complete_task"], required=True)
    parser.add_argument("--sha")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    print(json.dumps(advance_implement_runtime(repo, args.track, args.action, args.sha), indent=2))


if __name__ == "__main__":
    main()
