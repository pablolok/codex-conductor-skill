from __future__ import annotations

import argparse
import json
from pathlib import Path

from conductor_fs import (
    append_track_to_registry,
    canonical_track_id,
    existing_track_ids,
    existing_track_short_names,
    infer_track_type,
    load_template,
    now_utc,
    refresh_portfolio_indexes,
    refresh_track_index,
    require_canonical_workspace,
    slugify_short_name,
    write_text,
)


def render_track_files(template_base: Path, metadata: dict, title: str) -> dict[str, str]:
    replacements = {
        "{{TRACK_ID}}": metadata["track_id"],
        "{{TRACK_TITLE}}": metadata["title"],
        "{{TRACK_STATUS}}": metadata["status"],
        "{{TRACK_PATH}}": metadata["path"],
        "{{TRACK_REQUEST}}": title,
        "{{TRACK_TYPE}}": metadata["type"],
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
    template_base = Path(__file__).resolve().parents[1]

    if not conductor_dir.exists():
        raise SystemExit("conductor/ does not exist. Run conductor:setup first.")

    require_canonical_workspace(conductor_dir)

    for required in ("product.md", "tech-stack.md", "workflow.md", "tracks.md"):
        if not (conductor_dir / required).exists():
            raise SystemExit(f"Missing required conductor file: {required}")

    now = now_utc()
    short_name = slugify_short_name(args.title)
    if short_name in existing_track_short_names(conductor_dir):
        raise SystemExit(
            f"A track with short name '{short_name}' already exists. "
            "Choose a different title or resume the existing track."
        )
    track_id = canonical_track_id(args.title, existing_track_ids(conductor_dir), created_at=now)
    target_dir = tracks_dir / track_id
    target_dir.mkdir(parents=True, exist_ok=False)

    metadata = {
        "track_id": track_id,
        "type": infer_track_type(args.title),
        "status": "new",
        "created_at": now,
        "updated_at": now,
        "description": args.title,
        "title": args.title,
        "path": f"conductor/tracks/{track_id}",
    }

    write_text(target_dir / "metadata.json", json.dumps(metadata, indent=2))
    for relative_target, content in render_track_files(template_base, metadata, args.title).items():
        write_text(target_dir / relative_target, content)

    refresh_track_index(target_dir, template_base)
    append_track_to_registry(conductor_dir, template_base, track_id, args.title, status="new")
    refresh_portfolio_indexes(conductor_dir, template_base)
    print(str(target_dir))


if __name__ == "__main__":
    main()
