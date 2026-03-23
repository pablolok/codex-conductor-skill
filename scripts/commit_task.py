from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from conductor_fs import (
    find_in_progress_task,
    parse_plan,
    refresh_portfolio_indexes,
    refresh_track_index,
    require_canonical_workspace,
    resolve_track_dir,
    update_phase_checkpoint,
    update_task_marker,
)


def run_git(repo: Path, args: list[str]) -> str:
    result = subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, check=True)
    return result.stdout.strip()


def maybe_write_note(repo: Path, sha: str, task: str, summary: str) -> None:
    if not summary:
        return
    note = "\n".join([f"Task: {task}", "", "Summary:", summary])
    subprocess.run(["git", "notes", "add", "-f", "-m", note, sha], cwd=repo, check=True)


def find_phase_line(plan_path: Path, phase_name: str) -> int:
    for phase in parse_plan(plan_path):
        if phase["name"].lower() == phase_name.lower():
            return phase["line_number"]
    raise SystemExit(f"Phase '{phase_name}' not found in plan.")


def stage_code_changes(repo: Path, plan_path: Path, verify_path: Path) -> None:
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "reset", "HEAD", "--", str(plan_path), str(verify_path)], cwd=repo, check=True)


def has_staged_changes(repo: Path) -> bool:
    result = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=repo)
    return result.returncode == 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--track")
    parser.add_argument("--code-message", required=True)
    parser.add_argument("--plan-message", required=True)
    parser.add_argument("--note-summary")
    parser.add_argument("--phase-checkpoint")
    parser.add_argument("--verify-message")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    conductor_dir = repo / "conductor"
    template_base = Path(__file__).resolve().parents[1]
    require_canonical_workspace(conductor_dir)

    track_dir = resolve_track_dir(conductor_dir, args.track)
    plan_path = track_dir / "plan.md"
    verify_path = track_dir / "verify.md"
    task = find_in_progress_task(plan_path)
    if task is None:
        raise SystemExit("No in-progress task found to commit.")

    stage_code_changes(repo, plan_path, verify_path)
    if not has_staged_changes(repo):
        raise SystemExit("No staged code changes found for the active task.")
    subprocess.run(["git", "commit", "-m", args.code_message], cwd=repo, check=True)
    code_sha = run_git(repo, ["rev-parse", "--short", "HEAD"])
    maybe_write_note(repo, code_sha, task["title"], args.note_summary or "")

    update_task_marker(plan_path, task["line_number"], "x", sha=code_sha)
    if args.phase_checkpoint:
        phase_line = find_phase_line(plan_path, args.phase_checkpoint)
        checkpoint_sha = code_sha
        if args.verify_message:
            subprocess.run(["git", "add", str(verify_path)], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", args.verify_message], cwd=repo, check=True)
            checkpoint_sha = run_git(repo, ["rev-parse", "--short", "HEAD"])
        update_phase_checkpoint(plan_path, phase_line, checkpoint_sha)

    refresh_track_index(track_dir, template_base)
    refresh_portfolio_indexes(conductor_dir, template_base)
    subprocess.run(
        [
            "git",
            "add",
            str(plan_path),
            str(verify_path),
            str(track_dir / "index.md"),
            str(conductor_dir / "index.md"),
            str(conductor_dir / "tracks.md"),
        ],
        cwd=repo,
        check=True,
    )
    subprocess.run(["git", "commit", "-m", args.plan_message], cwd=repo, check=True)
    print(
        json.dumps(
            {
                "track": track_dir.name,
                "task": task["title"],
                "code_sha": code_sha,
                "plan_sha": run_git(repo, ["rev-parse", "--short", "HEAD"]),
                "phase_checkpoint": args.phase_checkpoint,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
