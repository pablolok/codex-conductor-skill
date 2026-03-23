from __future__ import annotations

import argparse
import json
from pathlib import Path

from conductor_fs import load_metadata, require_canonical_workspace
from review_track import build_review_report, detect_scope


def build_review_flow(repo: Path, track_ref: str | None) -> dict[str, object]:
    conductor_dir = repo / "conductor"
    track_dir = detect_scope(conductor_dir, track_ref)
    report = build_review_report(track_dir, repo)
    metadata = load_metadata(track_dir)
    return {
        "track": {
            "track_id": metadata["track_id"],
            "title": metadata.get("title", metadata["description"]),
            "path": str(track_dir).replace("\\", "/"),
        },
        "scope": report,
        "checkpoints": [
            "Review against spec.md, plan.md, workflow.md, and AGENTS.md.",
            "Confirm the diff range is correct before reviewing findings.",
            "Record findings first, then risks, open gaps, and decision in review.md.",
            "If fixes are required, append a review-fix task before resuming implementation.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--track")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    require_canonical_workspace(repo / "conductor")
    print(json.dumps(build_review_flow(repo, args.track), indent=2))


if __name__ == "__main__":
    main()
