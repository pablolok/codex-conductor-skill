from __future__ import annotations

import argparse
import json
from pathlib import Path

from conductor_fs import collect_revert_candidates, require_canonical_workspace, resolve_track_dir
from revert_track import build_revert_plan


def build_flow(repo: Path, track_ref: str | None, task: str | None, candidates_only: bool) -> dict[str, object]:
    conductor_dir = repo / "conductor"
    if candidates_only:
        return {
            "candidates": collect_revert_candidates(conductor_dir),
            "checkpoints": [
                "Pick the smallest safe revert scope first.",
                "Prefer reverting the most recent recorded task or phase checkpoint.",
                "Repair plan.md, metadata.json, and review/verify artifacts after rollback.",
            ],
        }
    track_dir = resolve_track_dir(conductor_dir, track_ref)
    plan = build_revert_plan(repo, track_dir, task)
    plan["checkpoints"] = [
        "Confirm the target task or phase before mutating git history.",
        "Revert associated implementation commits before plan-update commits.",
        "Realign plan.md markers, metadata status, and indexes after the revert.",
    ]
    return plan


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--track")
    parser.add_argument("--task")
    parser.add_argument("--candidates", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    require_canonical_workspace(repo / "conductor")
    print(json.dumps(build_flow(repo, args.track, args.task, args.candidates), indent=2))


if __name__ == "__main__":
    main()
