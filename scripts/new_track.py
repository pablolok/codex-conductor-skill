from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "track"


def next_track_id(tracks_dir: Path, archive_dir: Path) -> str:
    max_number = 0
    for base in (tracks_dir, archive_dir):
        if not base.exists():
            continue
        for metadata in base.glob("*/metadata.json"):
            try:
                data = json.loads(read_text(metadata))
            except json.JSONDecodeError:
                continue
            match = re.match(r"track-(\d+)$", str(data.get("id", "")))
            if match:
                max_number = max(max_number, int(match.group(1)))
    return f"track-{max_number + 1:03d}"


def refresh_tracks_md(conductor_dir: Path) -> None:
    active = []
    archived = []
    for child in sorted((conductor_dir / "tracks").iterdir()):
        if not child.is_dir() or child.name == "_template":
            continue
        metadata = child / "metadata.json"
        if metadata.exists():
            active.append(json.loads(read_text(metadata)))
    if (conductor_dir / "archive").exists():
        for child in sorted((conductor_dir / "archive").iterdir()):
            if not child.is_dir():
                continue
            metadata = child / "metadata.json"
            if metadata.exists():
                archived.append(json.loads(read_text(metadata)))

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
    parser.add_argument("--title", required=True)
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    conductor_dir = repo / "conductor"
    track_template_dir = conductor_dir / "tracks" / "_template"
    tracks_dir = conductor_dir / "tracks"
    archive_dir = conductor_dir / "archive"
    if not conductor_dir.exists():
        raise SystemExit("conductor/ does not exist. Run conductor:setup first.")

    track_id = next_track_id(tracks_dir, archive_dir)
    slug = slugify(args.title)
    directory_name = f"{track_id}-{slug}"
    target_dir = tracks_dir / directory_name
    target_dir.mkdir(parents=True, exist_ok=False)

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    metadata = {
        "id": track_id,
        "slug": slug,
        "title": args.title,
        "status": "spec",
        "phase": "spec",
        "createdAt": now,
        "updatedAt": now,
        "archivedAt": None,
        "path": f"conductor/tracks/{directory_name}",
        "relatedTrackIds": [],
        "activeTask": "Refine the initial spec",
    }
    write_text(target_dir / "metadata.json", json.dumps(metadata, indent=2))

    for filename in ("spec.md", "plan.md", "review.md", "verify.md"):
        content = read_text(track_template_dir / filename)
        if filename == "spec.md":
            content = content.replace("Replace with the user request for the track.", args.title)
        write_text(target_dir / filename, content)

    refresh_tracks_md(conductor_dir)
    print(str(target_dir))


if __name__ == "__main__":
    main()
