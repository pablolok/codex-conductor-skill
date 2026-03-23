from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from conductor_fs import (
    append_review_fix_task,
    find_in_progress_task,
    parse_plan,
    refresh_portfolio_indexes,
    refresh_track_index,
    require_canonical_workspace,
    resolve_track_dir,
    update_task_marker,
)


def run_git(repo: Path, args: list[str]) -> str:
    result = subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, check=True)
    return result.stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--track")
    parser.add_argument("--message", required=True)
    parser.add_argument("--plan-message", default="conductor(plan): Mark task 'Apply review suggestions' as complete")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    conductor_dir = repo / "conductor"
    template_base = Path(__file__).resolve().parents[1]
    require_canonical_workspace(conductor_dir)

    track_dir = resolve_track_dir(conductor_dir, args.track)
    plan_path = track_dir / "plan.md"
    append_review_fix_task(plan_path)

    task = None
    for phase in parse_plan(plan_path):
        if phase["name"] == "Review Fixes":
            for item in phase["tasks"]:
                if item["title"] == "Task: Apply review suggestions":
                    task = dict(item)
                    break
        if task:
            break
    if task is None:
        raise SystemExit("Review fix task was not found in plan.md after appending it.")

    if task["marker"] != "~":
        update_task_marker(plan_path, task["line_number"], "~")

    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "reset", "HEAD", "--", str(plan_path)], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", args.message], cwd=repo, check=True)
    code_sha = run_git(repo, ["rev-parse", "--short", "HEAD"])

    update_task_marker(plan_path, task["line_number"], "x", sha=code_sha)
    refresh_track_index(track_dir, template_base)
    refresh_portfolio_indexes(conductor_dir, template_base)
    subprocess.run(
        ["git", "add", str(plan_path), str(track_dir / "index.md"), str(conductor_dir / "index.md"), str(conductor_dir / "tracks.md")],
        cwd=repo,
        check=True,
    )
    subprocess.run(["git", "commit", "-m", args.plan_message], cwd=repo, check=True)
    print(json.dumps({"track": track_dir.name, "review_fix_sha": code_sha}, indent=2))


if __name__ == "__main__":
    main()
