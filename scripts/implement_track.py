from __future__ import annotations

import argparse
import json
from pathlib import Path

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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--track")
    parser.add_argument("--start", action="store_true")
    parser.add_argument("--complete-task")
    parser.add_argument("--sha")
    parser.add_argument("--complete-track", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    conductor_dir = repo / "conductor"
    template_base = Path(__file__).resolve().parents[1]
    require_canonical_workspace(conductor_dir)

    track_dir = resolve_track_dir(conductor_dir, args.track)
    metadata = load_metadata(track_dir)
    plan_path = track_dir / "plan.md"
    result: dict[str, str | None] = {
        "track_id": metadata["track_id"],
        "track_title": metadata.get("title", metadata["description"]),
        "action": None,
        "task": None,
        "phase": None,
    }

    if args.complete_track:
        metadata["status"] = "completed"
        write_metadata(track_dir, metadata)
        update_registry_entry_status(conductor_dir, template_base, metadata["track_id"], "completed")
        refresh_track_index(track_dir, template_base)
        refresh_portfolio_indexes(conductor_dir, template_base)
        result["action"] = "complete_track"
        print(json.dumps(result, indent=2))
        return

    if args.complete_task:
        current = find_in_progress_task(plan_path)
        if current is None:
            raise SystemExit("No in-progress task found to complete.")
        update_task_marker(plan_path, current["line_number"], "x", sha=args.sha)
        result["action"] = "complete_task"
        result["task"] = current["title"]
        result["phase"] = current["phase"]
    else:
        task = find_in_progress_task(plan_path)
        if task is None:
            task = find_first_incomplete_task(plan_path)
            if task is None:
                raise SystemExit("No incomplete tasks remain in the selected plan.")
            update_task_marker(plan_path, task["line_number"], "~")
        metadata["status"] = "in_progress"
        write_metadata(track_dir, metadata)
        update_registry_entry_status(conductor_dir, template_base, metadata["track_id"], "in_progress")
        result["action"] = "start_task"
        result["task"] = task["title"]
        result["phase"] = task["phase"]

    refresh_track_index(track_dir, template_base)
    refresh_portfolio_indexes(conductor_dir, template_base)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
