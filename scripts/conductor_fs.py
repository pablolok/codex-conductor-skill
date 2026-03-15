from __future__ import annotations

import json
import re
import shutil
from pathlib import Path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def load_template(base: Path, name: str) -> str:
    return read_text(base / "assets" / "repo_templates" / name)


def load_styleguide(base: Path, name: str) -> str:
    return read_text(base / "assets" / "styleguides" / name)


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


def detect_styleguide_names(repo: Path) -> list[str]:
    content = (
        read_text(repo / "AGENTS.md")
        + "\n"
        + read_text(repo / "README.md")
        + "\n"
        + infer_solution_file(repo)
    ).lower()
    styleguides = ["general.md"]
    if ".net" in content or "avalonia" in content or ".sln" in content or "c#" in content:
        styleguides.append("dotnet.md")
    return styleguides


def scan_tracks(root: Path, relative_prefix: str) -> list[dict]:
    results: list[dict] = []
    if not root.exists():
        return results
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        metadata_path = child / "metadata.json"
        if not metadata_path.exists():
            continue
        try:
            data = json.loads(read_text(metadata_path))
        except json.JSONDecodeError:
            continue
        data["path"] = f"{relative_prefix}/{child.name}".replace("\\", "/")
        data["directory"] = child.name
        results.append(data)
    return results


def format_track_summary(items: list[dict], empty_text: str) -> str:
    if not items:
        return empty_text
    return "\n".join(
        f"- `{item.get('id', 'unknown')}` | {item.get('title', 'Untitled')} | "
        f"`{item.get('status', 'unknown')}` | phase `{item.get('phase', 'unknown')}` | "
        f"{item.get('activeTask', 'No active task')} | `{item.get('path', '')}`"
        for item in items
    )


def format_track_index(items: list[dict], empty_text: str) -> str:
    if not items:
        return empty_text
    sections = []
    for item in items:
        sections.append("\n".join([
            f"## {item.get('id', 'unknown')} - {item.get('title', 'Untitled')}",
            "",
            f"- Status: `{item.get('status', 'unknown')}`",
            f"- Phase: `{item.get('phase', 'unknown')}`",
            f"- Active task: {item.get('activeTask', 'No active task')}",
            f"- Path: `{item.get('path', '')}`",
            "",
        ]))
    return "\n".join(sections).rstrip()


def render_portfolio_indexes(conductor_dir: Path, template_base: Path) -> dict[str, str]:
    active_tracks = scan_tracks(conductor_dir / "tracks", "conductor/tracks")
    archived_tracks = scan_tracks(conductor_dir / "archive", "conductor/archive")
    index_template = load_template(template_base, "index.md.tmpl")
    tracks_template = load_template(template_base, "tracks.md.tmpl")
    replacements = {
        "{{ACTIVE_TRACKS_INDEX}}": format_track_index(active_tracks, "No active tracks currently registered."),
        "{{ARCHIVED_TRACKS_INDEX}}": format_track_index(
            archived_tracks,
            "No archived tracks currently registered.",
        ),
        "{{ACTIVE_TRACKS_SUMMARY}}": format_track_summary(active_tracks, "No active tracks currently registered."),
        "{{ARCHIVED_TRACKS_SUMMARY}}": format_track_summary(
            archived_tracks,
            "No archived tracks currently registered.",
        ),
    }
    rendered = {}
    for target_name, template in (("index.md", index_template), ("tracks.md", tracks_template)):
        content = template
        for source, target in replacements.items():
            content = content.replace(source, target)
        rendered[target_name] = content.rstrip() + "\n"
    return rendered


def refresh_portfolio_indexes(conductor_dir: Path, template_base: Path) -> None:
    for relative_target, content in render_portfolio_indexes(conductor_dir, template_base).items():
        write_text(conductor_dir / relative_target, content)


def track_context_from_metadata(metadata: dict) -> dict[str, str]:
    return {
        "{{TRACK_ID}}": metadata["id"],
        "{{TRACK_TITLE}}": metadata["title"],
        "{{TRACK_STATUS}}": metadata["status"],
        "{{TRACK_PHASE}}": metadata["phase"],
        "{{TRACK_ACTIVE_TASK}}": metadata["activeTask"],
        "{{TRACK_PATH}}": metadata["path"],
    }


def render_track_index(template_base: Path, metadata: dict) -> str:
    content = load_template(template_base, "track_index.md.tmpl")
    for source, target in track_context_from_metadata(metadata).items():
        content = content.replace(source, target)
    return content.rstrip() + "\n"


def refresh_track_index(track_dir: Path, template_base: Path) -> None:
    metadata = json.loads(read_text(track_dir / "metadata.json"))
    write_text(track_dir / "index.md", render_track_index(template_base, metadata))


def reset_generated_structure(conductor_dir: Path) -> None:
    for relative in ("templates", "tracks/_template"):
        target = conductor_dir / relative
        if target.exists():
            shutil.rmtree(target)
