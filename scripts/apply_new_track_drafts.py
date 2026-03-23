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
    now_utc,
    refresh_portfolio_indexes,
    require_canonical_workspace,
    slugify_short_name,
    write_text,
)
from new_track import render_track_files


def normalize_newline(content: str) -> str:
    return content if content.endswith("\n") else f"{content}\n"


def create_track_from_drafts(repo: Path, title: str, spec_text: str, plan_text: str) -> Path:
    conductor_dir = repo / "conductor"
    tracks_dir = conductor_dir / "tracks"
    template_base = Path(__file__).resolve().parents[1]

    require_canonical_workspace(conductor_dir)
    for required in ("product.md", "tech-stack.md", "workflow.md", "tracks.md"):
        if not (conductor_dir / required).exists():
            raise SystemExit(f"Missing required conductor file: {required}")

    short_name = slugify_short_name(title)
    if short_name in existing_track_short_names(conductor_dir):
        raise SystemExit(
            f"A track with short name '{short_name}' already exists. Choose a different title or resume the existing track."
        )

    now = now_utc()
    track_id = canonical_track_id(title, existing_track_ids(conductor_dir), created_at=now)
    track_dir = tracks_dir / track_id
    track_dir.mkdir(parents=True, exist_ok=False)

    metadata = {
        "track_id": track_id,
        "type": infer_track_type(title),
        "status": "new",
        "created_at": now,
        "updated_at": now,
        "description": title,
        "title": title,
        "path": f"conductor/tracks/{track_id}",
    }

    rendered = render_track_files(template_base, metadata, title)
    rendered["spec.md"] = normalize_newline(spec_text)
    rendered["plan.md"] = normalize_newline(plan_text)

    write_text(track_dir / "metadata.json", json.dumps(metadata, indent=2))
    for relative_target, content in rendered.items():
        write_text(track_dir / relative_target, content)

    append_track_to_registry(conductor_dir, template_base, track_id, title, status="new")
    refresh_portfolio_indexes(conductor_dir, template_base)
    return track_dir


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--spec-file", required=True)
    parser.add_argument("--plan-file", required=True)
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    track_dir = create_track_from_drafts(
        repo,
        args.title,
        Path(args.spec_file).read_text(encoding="utf-8"),
        Path(args.plan_file).read_text(encoding="utf-8"),
    )
    print(str(track_dir))


if __name__ == "__main__":
    main()
