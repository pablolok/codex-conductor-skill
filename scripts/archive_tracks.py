from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from conductor_fs import (
    load_metadata,
    now_utc,
    parse_tracks_registry,
    refresh_portfolio_indexes,
    refresh_track_index,
    remove_track_from_registry,
    require_canonical_workspace,
    write_text,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    conductor = repo / "conductor"
    archive_dir = conductor / "archive"
    template_base = Path(__file__).resolve().parents[1]
    require_canonical_workspace(conductor)

    archived_any = False
    archive_dir.mkdir(parents=True, exist_ok=True)
    for entry in parse_tracks_registry(conductor / "tracks.md"):
        track_dir = entry["track_dir"]
        metadata = load_metadata(track_dir)
        if metadata["status"] != "completed":
            continue

        destination = archive_dir / track_dir.name
        if destination.exists():
            raise SystemExit(f"Could not archive '{track_dir.name}' because '{destination}' already exists.")
        try:
            shutil.move(str(track_dir), str(destination))
        except PermissionError as exc:
            raise SystemExit(
                f"Could not archive '{track_dir.name}' because the track directory is locked by another process."
            ) from exc

        metadata["status"] = "archived"
        metadata["archived_at"] = now_utc()
        metadata["path"] = f"conductor/archive/{destination.name}"
        write_text(destination / "metadata.json", json.dumps(metadata, indent=2))
        refresh_track_index(destination, template_base)
        remove_track_from_registry(conductor, template_base, metadata["track_id"])
        archived_any = True

    refresh_portfolio_indexes(conductor, template_base)
    print("archived" if archived_any else "no-op")


if __name__ == "__main__":
    main()
