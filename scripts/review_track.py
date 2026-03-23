from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from conductor_fs import (
    append_review_fix_task,
    latest_recorded_sha,
    load_metadata,
    parse_tracks_registry,
    read_text,
    require_canonical_workspace,
    resolve_track_dir,
    write_text,
)


def run_git(repo: Path, args: list[str]) -> str:
    result = subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, check=True)
    return result.stdout.strip()


def try_git(repo: Path, args: list[str]) -> str | None:
    result = subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def detect_scope(conductor_dir: Path, track_ref: str | None) -> Path:
    if track_ref:
        return resolve_track_dir(conductor_dir, track_ref)
    for entry in parse_tracks_registry(conductor_dir / "tracks.md"):
        if entry["status"] == "in_progress":
            return entry["track_dir"]
    raise SystemExit("No in-progress track found and no review scope was provided.")


def build_review_report(track_dir: Path, repo: Path) -> dict:
    metadata = load_metadata(track_dir)
    plan_path = track_dir / "plan.md"
    start_sha = latest_recorded_sha(plan_path)
    if start_sha:
        revision_range = f"{start_sha}..HEAD"
    else:
        revision_range = "HEAD"

    if revision_range != "HEAD":
        shortstat = try_git(repo, ["diff", "--shortstat", revision_range])
        changed_files = try_git(repo, ["diff", "--name-only", revision_range])
    else:
        shortstat = try_git(repo, ["diff", "--shortstat"])
        changed_files = try_git(repo, ["diff", "--name-only"])
    if shortstat is None:
        shortstat = "revision range unavailable"
    files = [line for line in (changed_files or "").splitlines() if line]
    report = {
        "track_id": metadata["track_id"],
        "track_title": metadata.get("title", metadata["description"]),
        "revision_range": revision_range,
        "shortstat": shortstat or "no diff",
        "changed_files": files,
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--track")
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--append-review-fix-task", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    conductor_dir = repo / "conductor"
    require_canonical_workspace(conductor_dir)

    track_dir = detect_scope(conductor_dir, args.track)
    report = build_review_report(track_dir, repo)

    if args.prepare:
        review_path = track_dir / "review.md"
        content = "\n".join(
            [
                "# Review",
                "",
                f"## Scope",
                "",
                f"- Track: `{report['track_id']}`",
                f"- Revision range: `{report['revision_range']}`",
                f"- Diff summary: {report['shortstat']}",
                "",
                "## Findings",
                "",
                "## Risks",
                "",
                "## Open Gaps",
                "",
                "## Decision",
            ]
        )
        write_text(review_path, content)

    if args.append_review_fix_task:
        append_review_fix_task(track_dir / "plan.md")

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
