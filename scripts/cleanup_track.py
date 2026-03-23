from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from conductor_fs import (
    now_utc,
    parse_tracks_registry,
    refresh_portfolio_indexes,
    refresh_track_index,
    remove_track_from_registry,
    require_canonical_workspace,
    resolve_track_dir,
    write_metadata,
)


def delete_track(conductor_dir: Path, track_dir: Path, template_base: Path) -> None:
    shutil.rmtree(track_dir)
    remove_track_from_registry(conductor_dir, template_base, track_dir.name)
    refresh_portfolio_indexes(conductor_dir, template_base)


def mark_archived(track_dir: Path, template_base: Path) -> None:
    metadata_path = track_dir / "metadata.json"
    if not metadata_path.exists():
        return
    import json

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["status"] = "archived"
    metadata["archived_at"] = now_utc()
    metadata["updated_at"] = metadata["archived_at"]
    metadata["path"] = f"conductor/archive/{track_dir.name}"
    write_metadata(track_dir, metadata)
    refresh_track_index(track_dir, template_base)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--track")
    parser.add_argument("--action", choices=["archive", "delete", "skip"], required=True)
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    conductor_dir = repo / "conductor"
    template_base = Path(__file__).resolve().parents[1]
    require_canonical_workspace(conductor_dir)
    track_dir = resolve_track_dir(conductor_dir, args.track)

    if args.action == "archive":
        result = {
            "action": "archive",
            "track": track_dir.name,
            "next_step": "run scripts/archive_tracks.py --repo <repo-root>",
            "checkpoints": [
                "Confirm the track is actually complete before archiving.",
                "Refresh indexes after the archive move completes.",
            ],
        }
    elif args.action == "delete":
        delete_track(conductor_dir, track_dir, template_base)
        result = {"action": "delete", "deleted": track_dir.name}
    else:
        result = {"action": "skip", "track": track_dir.name}

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
