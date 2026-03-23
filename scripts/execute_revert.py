from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from conductor_fs import (
    find_in_progress_task,
    find_first_incomplete_task,
    load_metadata,
    refresh_portfolio_indexes,
    refresh_track_index,
    require_canonical_workspace,
    resolve_track_dir,
    update_registry_entry_status,
    write_metadata,
)
from revert_track import build_revert_plan


def try_revert(repo: Path, sha: str) -> dict[str, str]:
    result = subprocess.run(["git", "revert", "--no-edit", sha], cwd=repo, text=True, capture_output=True)
    return {
        "sha": sha,
        "returncode": str(result.returncode),
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def abort_revert(repo: Path) -> None:
    subprocess.run(["git", "revert", "--abort"], cwd=repo, capture_output=True, text=True, check=False)


def infer_reset_status(track_dir: Path) -> str:
    plan_path = track_dir / "plan.md"
    current = find_in_progress_task(plan_path)
    if current:
        return "in_progress"
    pending = find_first_incomplete_task(plan_path)
    if pending:
        return "new"
    return "completed"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--track")
    parser.add_argument("--task")
    parser.add_argument("--repair-state", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    conductor_dir = repo / "conductor"
    template_base = Path(__file__).resolve().parents[1]
    require_canonical_workspace(conductor_dir)

    track_dir = resolve_track_dir(conductor_dir, args.track)
    plan = build_revert_plan(repo, track_dir, args.task)
    commits = list(reversed(plan["commits"]))
    results = []
    for commit in commits:
        result = try_revert(repo, commit["sha"])
        results.append(result)
        if result["returncode"] != "0":
            abort_revert(repo)
            print(json.dumps({"track": track_dir.name, "results": results, "conflict": True}, indent=2))
            return

    repaired_status = None
    if args.repair_state:
        metadata = load_metadata(track_dir)
        repaired_status = infer_reset_status(track_dir)
        metadata["status"] = repaired_status
        write_metadata(track_dir, metadata)
        update_registry_entry_status(conductor_dir, template_base, metadata["track_id"], repaired_status)
        refresh_track_index(track_dir, template_base)
        refresh_portfolio_indexes(conductor_dir, template_base)

    print(json.dumps({"track": track_dir.name, "results": results, "repaired_status": repaired_status}, indent=2))


if __name__ == "__main__":
    main()
