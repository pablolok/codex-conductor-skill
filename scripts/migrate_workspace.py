from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from conductor_fs import (
    canonical_status,
    canonical_track_id,
    detect_workspace_kind,
    existing_track_ids,
    infer_track_type,
    now_utc,
    refresh_portfolio_indexes,
    refresh_track_index,
    scan_tracks,
    write_registry,
    write_text,
)


def migrate_collection(root: Path, conductor_dir: Path, template_base: Path) -> list[dict]:
    migrated: list[dict] = []
    ids_in_use = existing_track_ids(conductor_dir)
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        metadata_path = child / "metadata.json"
        if not metadata_path.exists():
            continue
        try:
            data = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid metadata.json in {child}") from exc

        title = str(data.get("title") or data.get("description") or data.get("activeTask") or child.name)
        created_at = str(data.get("createdAt") or data.get("created_at") or now_utc())
        track_id = canonical_track_id(title, ids_in_use, created_at=created_at)
        ids_in_use.add(track_id)
        status = canonical_status(str(data.get("status", "")), str(data.get("phase", "")))
        canonical = {
            "track_id": track_id,
            "type": str(data.get("type") or infer_track_type(title)),
            "status": status,
            "created_at": created_at,
            "updated_at": str(data.get("updatedAt") or data.get("updated_at") or created_at),
            "description": str(data.get("description") or title),
            "title": title,
        }
        archived_at = data.get("archivedAt") or data.get("archived_at")
        if archived_at:
            canonical["archived_at"] = str(archived_at)

        target_dir = root / track_id
        if child != target_dir:
            shutil.move(str(child), str(target_dir))

        write_text(target_dir / "metadata.json", json.dumps(canonical, indent=2))
        refresh_track_index(target_dir, template_base)
        migrated.append({"track_id": track_id, "title": title, "status": status})
    return migrated


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    conductor_dir = repo / "conductor"
    template_base = Path(__file__).resolve().parents[1]
    kind = detect_workspace_kind(conductor_dir)

    if kind == "missing":
        raise SystemExit("No conductor/ workspace found to migrate.")
    if kind == "canonical":
        raise SystemExit("Workspace is already in canonical Gemini-compatible format.")

    tracks_dir = conductor_dir / "tracks"
    archive_dir = conductor_dir / "archive"
    tracks_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)

    migrate_collection(tracks_dir, conductor_dir, template_base)
    migrate_collection(archive_dir, conductor_dir, template_base)

    active_entries = scan_tracks(tracks_dir, "conductor/tracks")
    registry_entries = [
        {"track_id": item["track_id"], "title": item.get("title", item["description"]), "status": item["status"]}
        for item in active_entries
    ]
    write_registry(conductor_dir, template_base, registry_entries)
    refresh_portfolio_indexes(conductor_dir, template_base)
    print("migrated")


if __name__ == "__main__":
    main()
