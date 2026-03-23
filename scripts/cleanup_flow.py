from __future__ import annotations

import argparse
import json
from pathlib import Path

from conductor_fs import load_metadata, require_canonical_workspace, resolve_track_dir


def build_cleanup_flow(repo: Path, track_ref: str | None) -> dict[str, object]:
    conductor_dir = repo / "conductor"
    track_dir = resolve_track_dir(conductor_dir, track_ref)
    metadata = load_metadata(track_dir)
    return {
        "track": {
            "track_id": metadata["track_id"],
            "title": metadata.get("title", metadata["description"]),
            "status": metadata["status"],
            "path": str(track_dir).replace("\\", "/"),
        },
        "options": [
            {"label": "Review", "description": "Run conductor:review before final cleanup."},
            {"label": "Archive", "description": "Move the track into conductor/archive/ and remove it from the active registry."},
            {"label": "Delete", "description": "Permanently remove the track and unregister it."},
            {"label": "Skip", "description": "Leave the track in place for now."},
        ],
        "checkpoints": [
            "Only archive completed tracks.",
            "Require a final confirmation before permanent deletion.",
            "Refresh registry, indexes, and metadata after any cleanup action.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--track")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    require_canonical_workspace(repo / "conductor")
    print(json.dumps(build_cleanup_flow(repo, args.track), indent=2))


if __name__ == "__main__":
    main()
