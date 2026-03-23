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


def repo_relative(repo: Path, path: Path | str) -> str:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = (repo / candidate).resolve()
    return candidate.relative_to(repo).as_posix()


def stage_selected_paths(repo: Path, paths: list[str]) -> None:
    if not paths:
        return
    normalized = [repo_relative(repo, path) for path in paths]
    subprocess.run(["git", "add", "--", *normalized], cwd=repo, check=True)


def unstage_paths(repo: Path, paths: list[str]) -> None:
    if not paths:
        return
    subprocess.run(["git", "reset", "HEAD", "--", *paths], cwd=repo, check=True)


def staged_paths(repo: Path) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--relative"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=True,
    )
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def ensure_no_staged_conductor_changes(repo: Path, conductor_dir: Path, allowed: set[str] | None = None) -> None:
    root = repo_relative(repo, conductor_dir)
    allowed = allowed or set()
    blocked = [path for path in staged_paths(repo) if path.startswith(f"{root}/") and path not in allowed]
    if blocked:
        joined = ", ".join(blocked)
        raise SystemExit(f"Review-fix commit contains staged conductor artifacts: {joined}. Stage only implementation files.")


def has_staged_changes(repo: Path) -> bool:
    result = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=repo)
    return result.returncode == 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--track")
    parser.add_argument("--message", required=True)
    parser.add_argument("--plan-message", default="conductor(plan): Mark task 'Apply review suggestions' as complete")
    parser.add_argument("--paths", nargs="*")
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

    stage_selected_paths(repo, args.paths or [])
    unstage_paths(repo, [repo_relative(repo, plan_path)])
    ensure_no_staged_conductor_changes(repo, conductor_dir)
    if not has_staged_changes(repo):
        raise SystemExit("No staged code changes found for the review-fix task.")
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
