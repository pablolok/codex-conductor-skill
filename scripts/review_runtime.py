from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from cleanup_flow import build_cleanup_flow
from cleanup_track import execute_cleanup_action
from commit_review_changes import commit_review_changes
from conductor_fs import require_canonical_workspace
from review_flow import build_review_flow


def has_worktree_changes(repo: Path) -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=True,
    )
    return bool(result.stdout.strip())


def run_review_track(repo: Path, track_ref: str, prepare: bool = False) -> dict[str, object]:
    command = [
        "python",
        str(Path(__file__).resolve().parent / "review_track.py"),
        "--repo",
        str(repo),
        "--track",
        track_ref,
    ]
    if prepare:
        command.append("--prepare")
    result = subprocess.run(command, cwd=repo, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise SystemExit(result.stderr.strip() or result.stdout.strip() or "review_track.py failed")
    return json.loads(result.stdout)


def advance_review_runtime(
    repo: Path,
    track_ref: str | None,
    action: str,
    cleanup_action: str | None = None,
    confirmed: bool = False,
) -> dict[str, object]:
    require_canonical_workspace(repo / "conductor")

    if action == "start":
        return {
            "stage": "review",
            "flow": build_review_flow(repo, track_ref, run_tests=True),
        }

    if action == "apply_fixes":
        if not track_ref:
            raise SystemExit("A track is required to prepare review fixes.")
        report = run_review_track(repo, track_ref, prepare=True)
        return {
            "stage": "review_fix",
            "report": report,
            "commit_tracking_confirmation": {
                "header": "Commit & Track",
                "question": "I've detected review changes. Should I commit them and update the track plan?",
                "type": "yesno",
            },
            "cleanup_options": build_cleanup_flow(repo, track_ref)["options"],
        }

    if action == "manual_fix":
        return {
            "stage": "manual_fix",
            "message": "Review halted so the findings can be addressed manually before cleanup.",
        }

    if action == "complete":
        if has_worktree_changes(repo):
            if track_ref:
                return {
                    "stage": "commit_review_changes",
                    "commit_tracking_confirmation": {
                        "header": "Commit & Track",
                        "question": "I've detected uncommitted changes from the review process. Should I commit these and update the track plan?",
                        "type": "yesno",
                    },
                }
            return {
                "stage": "commit_review_changes",
                "commit_confirmation": {
                    "header": "Commit Changes",
                    "question": "I've detected uncommitted changes. Should I commit them?",
                    "type": "yesno",
                },
            }
        if not track_ref:
            return {
                "stage": "completed",
                "message": "Review complete with no remaining cleanup because no specific track was in scope.",
            }
        return {
            "stage": "cleanup",
            "cleanup": build_cleanup_flow(repo, track_ref),
        }

    if action == "cleanup_execute":
        if not track_ref:
            raise SystemExit("A track is required to execute review cleanup.")
        if cleanup_action not in {"archive", "delete", "skip"}:
            raise SystemExit("cleanup_execute requires --cleanup-action archive|delete|skip.")
        if cleanup_action == "delete" and not confirmed:
            return {
                "stage": "confirm_delete",
                "confirmation": {
                    "header": "Confirm",
                    "question": "WARNING: This is an irreversible deletion. Do you want to proceed?",
                    "type": "yesno",
                },
            }
        result = execute_cleanup_action(repo, track_ref, cleanup_action, commit_changes=cleanup_action != "skip")
        return {
            "stage": "completed",
            "cleanup_result": result,
        }

    if action == "commit_changes_execute":
        if track_ref:
            raise SystemExit("commit_changes_execute is only for non-track review changes.")
        return {
            "stage": "completed",
            "commit_result": commit_review_changes(repo),
        }

    raise SystemExit(f"Unsupported review runtime action '{action}'.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--track")
    parser.add_argument(
        "--action",
        choices=["start", "apply_fixes", "manual_fix", "complete", "cleanup_execute", "commit_changes_execute"],
        required=True,
    )
    parser.add_argument("--cleanup-action", choices=["archive", "delete", "skip"])
    parser.add_argument("--confirmed", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    print(json.dumps(advance_review_runtime(repo, args.track, args.action, args.cleanup_action, args.confirmed), indent=2))


if __name__ == "__main__":
    main()
