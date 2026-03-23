from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from cleanup_flow import build_cleanup_flow
from conductor_fs import require_canonical_workspace
from review_flow import build_review_flow


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


def advance_review_runtime(repo: Path, track_ref: str | None, action: str) -> dict[str, object]:
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
        if not track_ref:
            raise SystemExit("A track is required to complete review cleanup.")
        return {
            "stage": "cleanup",
            "cleanup": build_cleanup_flow(repo, track_ref),
        }

    raise SystemExit(f"Unsupported review runtime action '{action}'.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--track")
    parser.add_argument("--action", choices=["start", "apply_fixes", "manual_fix", "complete"], required=True)
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    print(json.dumps(advance_review_runtime(repo, args.track, args.action), indent=2))


if __name__ == "__main__":
    main()
