from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from conductor_fs import (
    load_template,
    read_text,
    refresh_portfolio_indexes,
    refresh_track_index,
    write_text,
)


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


def render_track_files(template_base: Path, metadata: dict, title: str) -> dict[str, str]:
    replacements = {
        "{{TRACK_ID}}": metadata["id"],
        "{{TRACK_TITLE}}": metadata["title"],
        "{{TRACK_STATUS}}": metadata["status"],
        "{{TRACK_PHASE}}": metadata["phase"],
        "{{TRACK_ACTIVE_TASK}}": metadata["activeTask"],
        "{{TRACK_PATH}}": metadata["path"],
        "{{TRACK_REQUEST}}": title,
    }
    templates = {
        "spec.md": "track_spec.md.tmpl",
        "plan.md": "track_plan.md.tmpl",
        "review.md": "track_review.md.tmpl",
        "verify.md": "track_verify.md.tmpl",
        "index.md": "track_index.md.tmpl",
    }
    rendered = {}
    for target, template_name in templates.items():
        content = load_template(template_base, template_name)
        for source, value in replacements.items():
            content = content.replace(source, value)
        rendered[target] = content.rstrip() + "\n"
    return rendered


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--title", required=True)
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    conductor_dir = repo / "conductor"
    tracks_dir = conductor_dir / "tracks"
    archive_dir = conductor_dir / "archive"
    template_base = Path(__file__).resolve().parents[1]

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
        "activeTask": "Draft and confirm the track spec",
    }

    write_text(target_dir / "metadata.json", json.dumps(metadata, indent=2))
    for relative_target, content in render_track_files(template_base, metadata, args.title).items():
        write_text(target_dir / relative_target, content)

    refresh_track_index(target_dir, template_base)
    refresh_portfolio_indexes(conductor_dir, template_base)
    print(str(target_dir))


if __name__ == "__main__":
    main()
