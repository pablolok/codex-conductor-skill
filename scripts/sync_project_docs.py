from __future__ import annotations

import argparse
import difflib
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


def diff_text(original: str, updated: str, path_label: str) -> str:
    return "\n".join(
        difflib.unified_diff(
            original.splitlines(),
            updated.splitlines(),
            fromfile=path_label,
            tofile=path_label,
            lineterm="",
        )
    )


def build_sync_payload(repo: Path, track_ref: str | None) -> dict[str, object]:
    conductor_dir = repo / "conductor"
    track_dir = resolve_track_dir(conductor_dir, track_ref)
    project_index = conductor_dir / "index.md"
    product_path = semantic_link_from_index(project_index, "Product Definition", "product.md")
    tech_path = semantic_link_from_index(project_index, "Tech Stack", "tech-stack.md")
    guidelines_path = semantic_link_from_index(project_index, "Product Guidelines", "product-guidelines.md")
    spec_path = track_dir / "spec.md"
    summary = summarize_spec(spec_path)

    targets = [
        ("Product", product_path, f"\n\n## Latest Track Sync\n\n- {track_dir.name}: {summary}\n"),
        ("Tech Stack", tech_path, "\n\n## Latest Track Sync\n\n- No stack change proposed from this helper.\n"),
        ("Product Guidelines", guidelines_path, "\n\n## Latest Track Sync\n\n- No product-guideline change proposed from this helper.\n"),
    ]

    proposals: dict[str, str] = {}
    approval_questions: list[dict[str, object]] = []
    for header, path, addition in targets:
        original = read_text(path).rstrip()
        updated = original if "## Latest Track Sync" in original else original + addition
        proposals[path.name] = addition
        approval_questions.append(
            {
                "header": header,
                "question": f"I've prepared the following proposed changes to `{path.name}`. Do you approve?\n\n---\n\n```diff\n{diff_text(original, updated, path.name)}\n```",
                "type": "yesno",
                "path": str(path).replace("\\", "/"),
            }
        )

    return {
        "track": track_dir.name,
        "product_path": str(product_path),
        "tech_stack_path": str(tech_path),
        "product_guidelines_path": str(guidelines_path),
        "proposals": proposals,
        "approval_questions": approval_questions,
    }


def apply_sync_payload(payload: dict[str, object]) -> None:
    for path_key, proposal in (
        ("product_path", payload["proposals"]["product.md"]),
        ("tech_stack_path", payload["proposals"]["tech-stack.md"]),
        ("product_guidelines_path", payload["proposals"]["product-guidelines.md"]),
    ):
        path = Path(str(payload[path_key]))
        current = read_text(path)
        if "## Latest Track Sync" in current:
            continue
        write_text(path, current.rstrip() + str(proposal))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--track")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    conductor_dir = repo / "conductor"
    require_canonical_workspace(conductor_dir)
    payload = build_sync_payload(repo, args.track)
    if args.apply:
        apply_sync_payload(payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
