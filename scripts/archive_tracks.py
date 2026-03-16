from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from conductor_fs import read_text, refresh_portfolio_indexes, refresh_track_index, write_text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    conductor = repo / "conductor"
    archive_dir = conductor / "archive"
    template_base = Path(__file__).resolve().parents[1]
    archived_any = False

    archive_dir.mkdir(parents=True, exist_ok=True)

    for child in sorted((conductor / "tracks").iterdir()):
        if not child.is_dir():
            continue
        metadata_path = child / "metadata.json"
        if not metadata_path.exists():
            continue

        metadata = json.loads(read_text(metadata_path))
        if metadata.get("status") != "done":
            continue

        archived_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        target_dir = archive_dir / child.name
        if target_dir.exists():
            raise SystemExit(f"Could not archive '{child.name}' because '{target_dir}' already exists.")
        try:
            shutil.move(str(child), str(target_dir))
        except PermissionError as exc:
            raise SystemExit(
                f"Could not archive '{child.name}' because the track directory is locked by another process. "
                "Close any open editor tabs or file handles and retry."
            ) from exc

        metadata["status"] = "archived"
        metadata["phase"] = "archived"
        metadata["archivedAt"] = archived_at
        metadata["updatedAt"] = archived_at
        metadata["path"] = f"conductor/archive/{target_dir.name}"
        write_text(target_dir / "metadata.json", json.dumps(metadata, indent=2))
        refresh_track_index(target_dir, template_base)
        archived_any = True

    refresh_portfolio_indexes(conductor, template_base)
    print("archived" if archived_any else "no-op")


if __name__ == "__main__":
    main()
