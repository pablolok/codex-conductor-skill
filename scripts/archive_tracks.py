from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def refresh_tracks_md(conductor_dir: Path) -> None:
    def scan(base: Path) -> list[dict]:
        items = []
        if not base.exists():
            return items
        for child in sorted(base.iterdir()):
            if not child.is_dir() or child.name == "_template":
                continue
            metadata = child / "metadata.json"
            if metadata.exists():
                items.append(json.loads(read_text(metadata)))
        return items

    active = scan(conductor_dir / "tracks")
    archived = scan(conductor_dir / "archive")

    def format_lines(items: list[dict], empty_text: str) -> str:
        if not items:
            return empty_text
        return "\n".join(
            f"- `{item['id']}` | {item['title']} | `{item['status']}` | phase `{item['phase']}` | {item['activeTask']}"
            for item in items
        )

    content = "\n".join(
        [
            "# Tracks",
            "",
            "This file is the canonical markdown index of Conductor tracks in this repository.",
            "",
            "## Active Tracks",
            "",
            format_lines(active, "No active tracks currently registered."),
            "",
            "## Archived Tracks",
            "",
            format_lines(archived, "No archived Conductor tracks currently registered in the canonical `conductor/` model."),
            "",
            "## Notes",
            "",
            "- `conductor/tracks/_template/` is a scaffold, not an active track.",
            "- Per-track structured state lives in each track's `metadata.json`.",
        ]
    )
    write_text(conductor_dir / "tracks.md", content)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    conductor = repo / "conductor"
    archived_any = False

    for child in sorted((conductor / "tracks").iterdir()):
        if not child.is_dir() or child.name == "_template":
            continue
        metadata_path = child / "metadata.json"
        if not metadata_path.exists():
            continue
        metadata = json.loads(read_text(metadata_path))
        if metadata.get("status") != "done":
            continue
        metadata["status"] = "archived"
        metadata["phase"] = "archived"
        metadata["archivedAt"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        write_text(metadata_path, json.dumps(metadata, indent=2))
        shutil.move(str(child), str(conductor / "archive" / child.name))
        archived_any = True

    refresh_tracks_md(conductor)
    print("archived" if archived_any else "no-op")


if __name__ == "__main__":
    main()
