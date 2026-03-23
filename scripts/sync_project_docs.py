from __future__ import annotations

import argparse
import json
from pathlib import Path

from conductor_fs import read_text, require_canonical_workspace, resolve_track_dir, semantic_link_from_index, write_text


def summarize_spec(spec_path: Path) -> str:
    lines = []
    capture = False
    for line in read_text(spec_path).splitlines():
        stripped = line.strip()
        if stripped.startswith("## Goal"):
            capture = True
            continue
        if capture and stripped.startswith("## "):
            break
        if capture and stripped:
            lines.append(stripped)
    return " ".join(lines) or "No explicit goal summary found."


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--track")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    conductor_dir = repo / "conductor"
    require_canonical_workspace(conductor_dir)

    track_dir = resolve_track_dir(conductor_dir, args.track)
    project_index = conductor_dir / "index.md"
    product_path = semantic_link_from_index(project_index, "Product Definition", "product.md")
    tech_path = semantic_link_from_index(project_index, "Tech Stack", "tech-stack.md")
    guidelines_path = semantic_link_from_index(project_index, "Product Guidelines", "product-guidelines.md")
    spec_path = track_dir / "spec.md"
    summary = summarize_spec(spec_path)

    proposals = {
        "product.md": f"\n\n## Latest Track Sync\n\n- {track_dir.name}: {summary}\n",
        "tech-stack.md": "\n\n## Latest Track Sync\n\n- No stack change proposed from this helper.\n",
        "product-guidelines.md": "\n\n## Latest Track Sync\n\n- No product-guideline change proposed from this helper.\n",
    }

    if args.apply:
        for path, addition in ((product_path, proposals["product.md"]), (tech_path, proposals["tech-stack.md"]), (guidelines_path, proposals["product-guidelines.md"])):
            if "## Latest Track Sync" in read_text(path):
                continue
            write_text(path, read_text(path).rstrip() + addition)

    print(
        json.dumps(
            {
                "track": track_dir.name,
                "product_path": str(product_path),
                "tech_stack_path": str(tech_path),
                "product_guidelines_path": str(guidelines_path),
                "proposals": proposals,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
