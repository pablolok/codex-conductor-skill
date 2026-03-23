from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from conductor_fs import collect_revert_candidates, latest_recorded_sha, parse_plan, require_canonical_workspace, resolve_track_dir


def run_git(repo: Path, args: list[str]) -> str:
    result = subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, check=True)
    return result.stdout.strip()


def try_git_subject(repo: Path, sha: str) -> str:
    result = subprocess.run(["git", "log", "-1", "--format=%s", sha], cwd=repo, text=True, capture_output=True)
    if result.returncode != 0:
        return "commit not found"
    return result.stdout.strip() or "commit not found"


def build_revert_plan(repo: Path, track_dir: Path, target_task: str | None) -> dict:
    plan_path = track_dir / "plan.md"
    plan = parse_plan(plan_path)
    commits: list[dict[str, str]] = []
    selected_task = None
    for phase in plan:
        for task in phase["tasks"]:
            if target_task and task["title"].lower() != target_task.lower():
                continue
            if task["sha"]:
                subject = try_git_subject(repo, task["sha"])
                commits.append({"sha": task["sha"], "subject": subject, "kind": "task"})
                selected_task = task["title"]
                if target_task:
                    break
        if target_task and selected_task:
            break
        if phase["checkpoint"]:
            subject = try_git_subject(repo, phase["checkpoint"])
            commits.append({"sha": phase["checkpoint"], "subject": subject, "kind": "checkpoint"})
    return {
        "track_id": track_dir.name,
        "target": selected_task or "track",
        "latest_recorded_sha": latest_recorded_sha(plan_path),
        "commits": commits,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--track")
    parser.add_argument("--task")
    parser.add_argument("--candidates", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    conductor_dir = repo / "conductor"
    require_canonical_workspace(conductor_dir)

    if args.candidates:
        print(json.dumps(collect_revert_candidates(conductor_dir), indent=2))
        return

    track_dir = resolve_track_dir(conductor_dir, args.track)
    plan = build_revert_plan(repo, track_dir, args.task)
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
