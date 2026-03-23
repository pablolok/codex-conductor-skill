from __future__ import annotations

import argparse
import re
from pathlib import Path

from conductor_fs import parse_tracks_registry, read_text, require_canonical_workspace


TASK_PATTERN = re.compile(r"^\s*-\s+\[(?P<marker>[ x~])\]\s+", re.MULTILINE)
PHASE_PATTERN = re.compile(r"^##\s+Phase:", re.MULTILINE)


def summarize_plan(plan_path: Path) -> dict:
    content = read_text(plan_path)
    tasks = TASK_PATTERN.findall(content)
    phases = PHASE_PATTERN.findall(content)
    in_progress = None
    next_pending = None
    blockers = []

    for line in content.splitlines():
        stripped = line.strip()
        task_match = re.match(r"- \[(?P<marker>[ x~])\] (?P<title>.+)$", stripped)
        if task_match:
            title = task_match.group("title")
            marker = task_match.group("marker")
            if marker == "~" and in_progress is None:
                in_progress = title
            if marker == " " and next_pending is None:
                next_pending = title
            if "blocker" in title.lower():
                blockers.append(title)

    completed = sum(1 for marker in tasks if marker == "x")
    progress = f"{completed}/{len(tasks)}" if tasks else "0/0"
    return {
        "phases_total": len(phases),
        "tasks_total": len(tasks),
        "tasks_completed": completed,
        "tasks_in_progress": sum(1 for marker in tasks if marker == "~"),
        "tasks_pending": sum(1 for marker in tasks if marker == " "),
        "current_task": in_progress or "none",
        "next_task": next_pending or "none",
        "blockers": blockers,
        "progress": progress,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    conductor = repo / "conductor"
    require_canonical_workspace(conductor)

    tracks_file = conductor / "tracks.md"
    if not tracks_file.exists():
        raise SystemExit("Missing conductor/tracks.md")

    entries = parse_tracks_registry(tracks_file)
    if not entries:
        print("Timestamp: no active tracks")
        print("Project Status: idle")
        print("Current Phase and Task: none")
        print("Next Action Needed: none")
        print("Blockers: none")
        print("Phases (total): 0")
        print("Tasks (total): 0")
        print("Progress: 0/0 (0%)")
        return

    total_phases = 0
    total_tasks = 0
    completed_tasks = 0
    current_track = "none"
    current_task = "none"
    next_task = "none"
    blockers: list[str] = []

    for entry in entries:
        plan_path = entry["track_dir"] / "plan.md"
        summary = summarize_plan(plan_path)
        total_phases += summary["phases_total"]
        total_tasks += summary["tasks_total"]
        completed_tasks += summary["tasks_completed"]
        if current_task == "none" and summary["current_task"] != "none":
            current_track = entry["title"]
            current_task = summary["current_task"]
        if next_task == "none" and summary["next_task"] != "none":
            next_task = f"{entry['title']}: {summary['next_task']}"
        blockers.extend(f"{entry['title']}: {item}" for item in summary["blockers"])

    percent = int((completed_tasks / total_tasks) * 100) if total_tasks else 0
    project_status = "blocked" if blockers else ("in_progress" if completed_tasks < total_tasks else "complete")

    print("Timestamp: generated from canonical conductor registry")
    print(f"Project Status: {project_status}")
    print(f"Current Phase and Task: {current_track} | {current_task}")
    print(f"Next Action Needed: {next_task}")
    print(f"Blockers: {', '.join(blockers) if blockers else 'none'}")
    print(f"Phases (total): {total_phases}")
    print(f"Tasks (total): {total_tasks}")
    print(f"Progress: {completed_tasks}/{total_tasks} ({percent}%)")


if __name__ == "__main__":
    main()
