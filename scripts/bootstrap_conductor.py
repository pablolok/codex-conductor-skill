from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def load_template(base: Path, name: str) -> str:
    return read_text(base / "assets" / "repo_templates" / name)


def infer_product_name(repo: Path) -> str:
    readme = read_text(repo / "README.md")
    match = re.search(r"^#\s+(.+)$", readme, re.MULTILINE)
    return match.group(1).strip() if match else repo.name


def infer_solution_file(repo: Path) -> str:
    sln_files = sorted(repo.glob("*.sln"))
    return sln_files[0].name if sln_files else "Unknown"


def infer_source_roots(repo: Path) -> str:
    src_root = repo / "src"
    if not src_root.exists():
        return "- `src/` not detected"
    lines = []
    for child in sorted(src_root.iterdir()):
        if child.is_dir():
            lines.append(f"- `src/{child.name}`")
    return "\n".join(lines) if lines else "- `src/` detected but no child directories were found"


def infer_tech_stack(repo: Path) -> str:
    agents = read_text(repo / "AGENTS.md")
    lines = []
    in_section = False
    for raw_line in agents.splitlines():
        line = raw_line.strip()
        if line == "### Main Technologies":
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section and line.startswith("- "):
            lines.append(line)
    if lines:
        return "\n".join(lines)
    return "- Stack not auto-detected from `AGENTS.md`"


def scan_tracks(root: Path, relative_prefix: str) -> list[dict]:
    results: list[dict] = []
    if not root.exists():
        return results
    for child in sorted(root.iterdir()):
        if not child.is_dir() or child.name == "_template":
            continue
        metadata_path = child / "metadata.json"
        if not metadata_path.exists():
            continue
        try:
            data = json.loads(read_text(metadata_path))
        except json.JSONDecodeError:
            continue
        data["path"] = f"{relative_prefix}/{child.name}".replace("\\", "/")
        results.append(data)
    return results


def format_track_lines(tracks: list[dict], empty_text: str) -> str:
    if not tracks:
        return empty_text
    return "\n".join(
        f"- `{item.get('id', 'unknown')}` | {item.get('title', 'Untitled')} | "
        f"`{item.get('status', 'unknown')}` | phase `{item.get('phase', 'unknown')}` | "
        f"{item.get('activeTask', 'No active task')}"
        for item in tracks
    )


def refresh_tracks_index(conductor_dir: Path, template_base: Path) -> None:
    active_tracks = scan_tracks(conductor_dir / "tracks", "conductor/tracks")
    archived_tracks = scan_tracks(conductor_dir / "archive", "conductor/archive")
    template = load_template(template_base, "tracks.md.tmpl")
    content = (
        template.replace("{{ACTIVE_TRACKS}}", format_track_lines(active_tracks, "No active tracks currently registered."))
        .replace("{{ARCHIVED_TRACKS}}", format_track_lines(archived_tracks, "No archived Conductor tracks currently registered in the canonical `conductor/` model."))
    )
    write_text(conductor_dir / "tracks.md", content)


def ensure_shared_context(repo: Path, template_base: Path) -> None:
    conductor_dir = repo / "conductor"
    conductor_dir.mkdir(parents=True, exist_ok=True)
    (conductor_dir / "archive").mkdir(parents=True, exist_ok=True)
    (conductor_dir / "code_styleguides").mkdir(parents=True, exist_ok=True)
    (conductor_dir / "templates").mkdir(parents=True, exist_ok=True)
    (conductor_dir / "tracks").mkdir(parents=True, exist_ok=True)
    (conductor_dir / "tracks" / "_template").mkdir(parents=True, exist_ok=True)

    replacements = {
        "{{PRODUCT_NAME}}": infer_product_name(repo),
        "{{SOLUTION_FILE}}": infer_solution_file(repo),
        "{{SOURCE_ROOTS}}": infer_source_roots(repo),
        "{{TECH_STACK}}": infer_tech_stack(repo),
    }

    shared_files = {
        "README.md": "README.md.tmpl",
        "workflow.md": "workflow.md.tmpl",
        "product.md": "product.md.tmpl",
        "product-guidelines.md": "product-guidelines.md.tmpl",
        "tech-stack.md": "tech-stack.md.tmpl",
        "code_styleguides/README.md": "code_styleguides_README.md.tmpl",
        "templates/metadata.template.json": "metadata.template.json.tmpl",
        "templates/spec.template.md": "spec.template.md.tmpl",
        "templates/plan.template.md": "plan.template.md.tmpl",
        "templates/review.template.md": "review.template.md.tmpl",
        "templates/verify.template.md": "verify.template.md.tmpl",
        "tracks/_template/metadata.json": "track_metadata.json.tmpl",
        "tracks/_template/spec.md": "track_spec.md.tmpl",
        "tracks/_template/plan.md": "track_plan.md.tmpl",
        "tracks/_template/review.md": "track_review.md.tmpl",
        "tracks/_template/verify.md": "track_verify.md.tmpl",
    }

    for relative_target, template_name in shared_files.items():
        content = load_template(template_base, template_name)
        for source, target in replacements.items():
            content = content.replace(source, target)
        write_text(conductor_dir / relative_target, content)

    write_text(conductor_dir / "archive" / ".gitkeep", "")
    refresh_tracks_index(conductor_dir, template_base)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    template_base = Path(__file__).resolve().parents[1]
    ensure_shared_context(repo, template_base)
    print(f"Bootstrapped conductor workspace in {repo / 'conductor'}")


if __name__ == "__main__":
    main()
