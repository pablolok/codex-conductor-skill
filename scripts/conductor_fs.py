from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CANONICAL_SHARED_FILES = (
    "README.md",
    "workflow.md",
    "product.md",
    "product-guidelines.md",
    "tech-stack.md",
    "index.md",
    "tracks.md",
)

LEGACY_TRACKS_MARKER = "compact summary view of Conductor tracks"
REGISTRY_EMPTY_TEXT = "No active tracks currently registered."
TASK_STATUS_PATTERN = re.compile(r"^(?P<indent>\s*)- \[(?P<marker>[ x~])\] (?P<title>.+?)(?:\s+(?P<sha>[a-f0-9]{7}))?$")
PHASE_HEADER_PATTERN = re.compile(r"^##\s+Phase:\s+(?P<name>.+?)(?:\s+\[checkpoint:\s*(?P<checkpoint>[a-f0-9]{7})\])?$")


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


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slugify_short_name(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    slug = slug.replace("-", "_")
    return slug or "track"


def infer_track_type(title: str) -> str:
    lowered = title.lower()
    if any(token in lowered for token in ("bug", "fix", "regression", "error")):
        return "bug"
    if any(token in lowered for token in ("chore", "cleanup", "docs", "refactor")):
        return "chore"
    return "feature"


def canonical_status(status: str | None, phase: str | None = None) -> str:
    value = (status or "").strip().lower()
    phase_value = (phase or "").strip().lower()
    if value in {"completed", "cancelled", "archived", "blocked", "new", "in_progress"}:
        return value
    if value in {"done"}:
        return "completed"
    if value in {"spec", "confirming", "planned", ""}:
        return "new"
    if value in {"implementing", "reviewing", "verifying"}:
        return "in_progress"
    if phase_value in {"implementing", "reviewing", "verifying"}:
        return "in_progress"
    if phase_value == "done":
        return "completed"
    return "new"


def status_marker_for(status: str | None) -> str:
    value = (status or "").strip().lower()
    if value == "completed":
        return "x"
    if value == "in_progress":
        return "~"
    return " "


def status_from_marker(marker: str) -> str:
    if marker == "x":
        return "completed"
    if marker == "~":
        return "in_progress"
    return "new"


def detect_workspace_kind(conductor_dir: Path) -> str:
    if not conductor_dir.exists():
        return "missing"

    tracks_file = conductor_dir / "tracks.md"
    tracks_content = read_text(tracks_file)
    if LEGACY_TRACKS_MARKER in tracks_content:
        return "legacy"

    for metadata_path in list((conductor_dir / "tracks").glob("*/metadata.json")) + list(
        (conductor_dir / "archive").glob("*/metadata.json")
    ):
        try:
            data = json.loads(read_text(metadata_path))
        except json.JSONDecodeError:
            continue
        if "track_id" in data:
            return "canonical"
        if "id" in data or "createdAt" in data or "activeTask" in data:
            return "legacy"

    if tracks_file.exists() or (conductor_dir / "index.md").exists():
        return "canonical"

    return "missing"


def require_canonical_workspace(conductor_dir: Path) -> None:
    kind = detect_workspace_kind(conductor_dir)
    if kind == "legacy":
        raise SystemExit(
            "Legacy Codex-native conductor workspace detected. "
            "Run scripts/migrate_workspace.py --repo <repo-root> before using this command."
        )
    if kind == "missing":
        raise SystemExit("No conductor/ workspace found. Run conductor:setup first.")


def normalize_metadata(data: dict, track_dir: Path | None = None) -> dict:
    legacy_id = str(data.get("id", "")).strip()
    track_id = str(data.get("track_id") or legacy_id).strip()
    title = str(data.get("title") or data.get("description") or data.get("activeTask") or track_id).strip()
    created_at = str(data.get("created_at") or data.get("createdAt") or now_utc())
    updated_at = str(data.get("updated_at") or data.get("updatedAt") or created_at)
    archived_at = data.get("archived_at")
    if archived_at is None:
        archived_at = data.get("archivedAt")
    status = canonical_status(str(data.get("status", "")), str(data.get("phase", "")))
    description = str(data.get("description") or data.get("title") or title).strip()
    normalized = {
        "track_id": track_id,
        "type": str(data.get("type") or infer_track_type(title)),
        "status": status,
        "created_at": created_at,
        "updated_at": updated_at,
        "description": description,
        "title": title,
    }
    if archived_at:
        normalized["archived_at"] = str(archived_at)
    if "phase" in data and data.get("phase"):
        normalized["phase"] = str(data.get("phase"))
    if "activeTask" in data and data.get("activeTask"):
        normalized["active_task"] = str(data.get("activeTask"))
    if "active_task" in data and data.get("active_task"):
        normalized["active_task"] = str(data.get("active_task"))
    if track_dir is not None:
        normalized["path"] = str(track_dir).replace("\\", "/")
    return normalized


def load_metadata(track_dir: Path) -> dict:
    metadata_path = track_dir / "metadata.json"
    if not metadata_path.exists():
        raise SystemExit(f"Missing metadata.json for track directory: {track_dir}")
    try:
        data = json.loads(read_text(metadata_path))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid metadata.json in {track_dir}") from exc
    return normalize_metadata(data, track_dir)


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
            item = normalize_metadata(json.loads(read_text(metadata_path)))
        except json.JSONDecodeError:
            continue
        item["path"] = f"{relative_prefix}/{child.name}".replace("\\", "/")
        item["directory"] = child.name
        results.append(item)
    return results


def parse_tracks_registry(tracks_file: Path) -> list[dict]:
    content = read_text(tracks_file)
    entries: list[dict] = []
    bullet_pattern = re.compile(
        r"- \[(?P<marker>[ x~])\] \*\*Track: (?P<title>.+?)\*\*\s*\n\s*\*Link: \[(?P<label>[^\]]+)\]\((?P<link>[^)]+)\)\*",
        re.MULTILINE,
    )
    legacy_pattern = re.compile(
        r"^##\s+\[(?P<marker>[ x~])\]\s+Track:\s+(?P<title>.+?)\s*$.*?^\*Link:\s+\[(?P<label>[^\]]+)\]\((?P<link>[^)]+)\)\*",
        re.MULTILINE | re.DOTALL,
    )
    matches = list(bullet_pattern.finditer(content))
    if not matches:
        matches = list(legacy_pattern.finditer(content))
    for match in matches:
        link = match.group("link").strip()
        if link.startswith("./"):
            resolved = (tracks_file.parent / link[2:]).resolve()
        else:
            resolved = (tracks_file.parent / link).resolve()
        track_id = resolved.name
        entries.append(
            {
                "marker": match.group("marker"),
                "status": status_from_marker(match.group("marker")),
                "title": match.group("title").strip(),
                "link_label": match.group("label").strip(),
                "link": link,
                "track_dir": resolved,
                "track_id": track_id,
            }
        )
    return entries


def render_registry(entries: list[dict], template_base: Path) -> str:
    template = load_template(template_base, "tracks.md.tmpl")
    if not entries:
        registry = REGISTRY_EMPTY_TEXT
    else:
        blocks = []
        for entry in entries:
            track_id = entry["track_id"]
            title = entry["title"]
            marker = entry.get("marker") or status_marker_for(entry.get("status"))
            relative_link = f"./tracks/{track_id}/"
            blocks.append(
                "\n".join(
                    [
                        "---",
                        "",
                        f"- [{marker}] **Track: {title}**",
                        f"  *Link: [{relative_link}]({relative_link})*",
                    ]
                )
            )
        registry = "\n\n".join(blocks)
    return template.replace("{{ACTIVE_TRACKS_REGISTRY}}", registry).rstrip() + "\n"


def write_registry(conductor_dir: Path, template_base: Path, entries: list[dict]) -> None:
    write_text(conductor_dir / "tracks.md", render_registry(entries, template_base))


def append_track_to_registry(conductor_dir: Path, template_base: Path, track_id: str, title: str, status: str = "new") -> None:
    tracks_file = conductor_dir / "tracks.md"
    entries = parse_tracks_registry(tracks_file) if tracks_file.exists() else []
    entries.append({"track_id": track_id, "title": title, "status": status, "marker": status_marker_for(status)})
    write_registry(conductor_dir, template_base, entries)


def remove_track_from_registry(conductor_dir: Path, template_base: Path, track_id: str) -> None:
    tracks_file = conductor_dir / "tracks.md"
    entries = [entry for entry in parse_tracks_registry(tracks_file) if entry["track_id"] != track_id]
    write_registry(conductor_dir, template_base, entries)


def update_registry_entry_status(conductor_dir: Path, template_base: Path, track_id: str, status: str) -> None:
    tracks_file = conductor_dir / "tracks.md"
    entries = parse_tracks_registry(tracks_file)
    updated = False
    for entry in entries:
        if entry["track_id"] == track_id:
            entry["status"] = status
            entry["marker"] = status_marker_for(status)
            updated = True
            break
    if not updated:
        raise SystemExit(f"Track '{track_id}' not found in conductor/tracks.md")
    write_registry(conductor_dir, template_base, entries)


def format_track_index(items: list[dict], empty_text: str) -> str:
    if not items:
        return empty_text
    sections = []
    for item in items:
        track_id = item.get("track_id", "unknown")
        title = item.get("title", item.get("description", "Untitled"))
        status = item.get("status", "unknown")
        path = item.get("path", "")
        sections.append(
            "\n".join(
                [
                    f"## {track_id} - {title}",
                    "",
                    f"- Status: `{status}`",
                    f"- Path: `{path}`",
                    "",
                ]
            ).rstrip()
        )
    return "\n".join(sections)


def render_portfolio_indexes(conductor_dir: Path, template_base: Path) -> dict[str, str]:
    tracks_file = conductor_dir / "tracks.md"
    active_items: list[dict] = []
    if tracks_file.exists():
        for entry in parse_tracks_registry(tracks_file):
            if not entry["track_dir"].exists():
                continue
            try:
                item = load_metadata(entry["track_dir"])
            except SystemExit:
                continue
            item["path"] = f"conductor/tracks/{entry['track_id']}"
            active_items.append(item)
    archived_items = scan_tracks(conductor_dir / "archive", "conductor/archive")
    index_template = load_template(template_base, "index.md.tmpl")
    replacements = {
        "{{ACTIVE_TRACKS_INDEX}}": format_track_index(active_items, "No active tracks currently registered."),
        "{{ARCHIVED_TRACKS_INDEX}}": format_track_index(archived_items, "No archived tracks currently registered."),
    }
    content = index_template
    for source, target in replacements.items():
        content = content.replace(source, target)
    return {"index.md": content.rstrip() + "\n"}


def refresh_portfolio_indexes(conductor_dir: Path, template_base: Path) -> None:
    for relative_target, content in render_portfolio_indexes(conductor_dir, template_base).items():
        write_text(conductor_dir / relative_target, content)


def track_context_from_metadata(metadata: dict) -> dict[str, str]:
    return {
        "{{TRACK_ID}}": metadata["track_id"],
        "{{TRACK_TITLE}}": metadata.get("title", metadata.get("description", metadata["track_id"])),
        "{{TRACK_STATUS}}": metadata["status"],
        "{{TRACK_PATH}}": metadata.get("path", ""),
    }


def render_track_index(template_base: Path, metadata: dict) -> str:
    content = load_template(template_base, "track_index.md.tmpl")
    for source, target in track_context_from_metadata(metadata).items():
        content = content.replace(source, target)
    return content.rstrip() + "\n"


def refresh_track_index(track_dir: Path, template_base: Path) -> None:
    metadata = load_metadata(track_dir)
    write_text(track_dir / "index.md", render_track_index(template_base, metadata))


def reset_generated_structure(conductor_dir: Path) -> None:
    for relative in ("templates", "tracks/_template"):
        target = conductor_dir / relative
        if target.exists():
            shutil.rmtree(target)


def ensure_tracks_registry(conductor_dir: Path, template_base: Path) -> None:
    tracks_file = conductor_dir / "tracks.md"
    if not tracks_file.exists():
        write_text(tracks_file, render_registry([], template_base))


def canonical_track_id(title: str, existing_ids: set[str], created_at: str | None = None) -> str:
    if created_at:
        date_part = re.sub(r"[^0-9]", "", created_at[:10])
    else:
        date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    base = f"{slugify_short_name(title)}_{date_part}"
    candidate = base
    counter = 2
    while candidate in existing_ids:
        candidate = f"{base}_{counter}"
        counter += 1
    return candidate


def existing_track_ids(conductor_dir: Path) -> set[str]:
    ids: set[str] = set()
    for base in (conductor_dir / "tracks", conductor_dir / "archive"):
        if not base.exists():
            continue
        for child in base.iterdir():
            if not child.is_dir():
                continue
            metadata_path = child / "metadata.json"
            if not metadata_path.exists():
                ids.add(child.name)
                continue
            try:
                data = json.loads(read_text(metadata_path))
            except json.JSONDecodeError:
                ids.add(child.name)
                continue
            ids.add(str(data.get("track_id") or data.get("id") or child.name))
    return ids


def existing_track_short_names(conductor_dir: Path) -> set[str]:
    short_names: set[str] = set()
    for track_id in existing_track_ids(conductor_dir):
        short_names.add(track_id.rsplit("_", 1)[0])
    return short_names


def write_metadata(track_dir: Path, metadata: dict) -> None:
    write_text(track_dir / "metadata.json", json.dumps(metadata, indent=2))


def resolve_track_dir(conductor_dir: Path, track_ref: str | None = None) -> Path:
    entries = parse_tracks_registry(conductor_dir / "tracks.md")
    if not entries:
        raise SystemExit("The tracks file is empty or malformed. No tracks available.")
    if track_ref:
        lowered = track_ref.strip().lower()
        exact = [entry for entry in entries if entry["track_id"].lower() == lowered or entry["title"].lower() == lowered]
        if len(exact) == 1:
            return exact[0]["track_dir"]
        partial = [entry for entry in entries if lowered in entry["track_id"].lower() or lowered in entry["title"].lower()]
        if len(partial) == 1:
            return partial[0]["track_dir"]
        if len(exact) > 1 or len(partial) > 1:
            raise SystemExit(f"Track reference '{track_ref}' is ambiguous.")
        raise SystemExit(f"Track reference '{track_ref}' not found.")
    for entry in entries:
        if entry["status"] != "completed":
            return entry["track_dir"]
    raise SystemExit("No incomplete tracks found in the tracks file.")


def parse_plan(plan_path: Path) -> list[dict[str, Any]]:
    phases: list[dict[str, Any]] = []
    current_phase: dict[str, Any] | None = None
    for line_number, line in enumerate(read_text(plan_path).splitlines(), start=1):
        phase_match = PHASE_HEADER_PATTERN.match(line.strip())
        if phase_match:
            current_phase = {
                "name": phase_match.group("name"),
                "checkpoint": phase_match.group("checkpoint"),
                "line_number": line_number,
                "tasks": [],
            }
            phases.append(current_phase)
            continue
        task_match = TASK_STATUS_PATTERN.match(line)
        if task_match and current_phase is not None:
            current_phase["tasks"].append(
                {
                    "line_number": line_number,
                    "indent": task_match.group("indent"),
                    "marker": task_match.group("marker"),
                    "title": task_match.group("title"),
                    "sha": task_match.group("sha"),
                }
            )
    return phases


def find_first_incomplete_task(plan_path: Path) -> dict[str, Any] | None:
    for phase in parse_plan(plan_path):
        for task in phase["tasks"]:
            if task["marker"] != "x":
                task_with_phase = dict(task)
                task_with_phase["phase"] = phase["name"]
                task_with_phase["phase_line"] = phase["line_number"]
                return task_with_phase
    return None


def find_in_progress_task(plan_path: Path) -> dict[str, Any] | None:
    for phase in parse_plan(plan_path):
        for task in phase["tasks"]:
            if task["marker"] == "~":
                task_with_phase = dict(task)
                task_with_phase["phase"] = phase["name"]
                task_with_phase["phase_line"] = phase["line_number"]
                return task_with_phase
    return None


def update_task_marker(plan_path: Path, line_number: int, marker: str, sha: str | None = None) -> None:
    lines = read_text(plan_path).splitlines()
    if line_number < 1 or line_number > len(lines):
        raise SystemExit(f"Invalid task line number {line_number} for {plan_path}")
    line = lines[line_number - 1]
    match = TASK_STATUS_PATTERN.match(line)
    if not match:
        raise SystemExit(f"Line {line_number} in {plan_path} is not a task line.")
    title = match.group("title")
    indent = match.group("indent")
    suffix = f" {sha}" if sha else ""
    lines[line_number - 1] = f"{indent}- [{marker}] {title}{suffix}"
    write_text(plan_path, "\n".join(lines))


def update_phase_checkpoint(plan_path: Path, phase_line_number: int, checkpoint_sha: str) -> None:
    lines = read_text(plan_path).splitlines()
    if phase_line_number < 1 or phase_line_number > len(lines):
        raise SystemExit(f"Invalid phase line number {phase_line_number} for {plan_path}")
    line = lines[phase_line_number - 1]
    match = PHASE_HEADER_PATTERN.match(line.strip())
    if not match:
        raise SystemExit(f"Line {phase_line_number} in {plan_path} is not a phase heading.")
    name = match.group("name")
    lines[phase_line_number - 1] = f"## Phase: {name} [checkpoint: {checkpoint_sha}]"
    write_text(plan_path, "\n".join(lines))


def append_review_fix_task(plan_path: Path) -> None:
    content = read_text(plan_path).rstrip()
    addition = "\n\n## Phase: Review Fixes\n- [~] Task: Apply review suggestions"
    if "## Phase: Review Fixes" in content:
        return
    write_text(plan_path, content + addition)


def latest_recorded_sha(plan_path: Path) -> str | None:
    latest = None
    for phase in parse_plan(plan_path):
        if phase["checkpoint"]:
            latest = phase["checkpoint"]
        for task in phase["tasks"]:
            if task["sha"]:
                latest = task["sha"]
    return latest


def collect_revert_candidates(conductor_dir: Path) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    for entry in parse_tracks_registry(conductor_dir / "tracks.md"):
        plan_path = entry["track_dir"] / "plan.md"
        for phase in parse_plan(plan_path):
            for task in phase["tasks"]:
                if task["marker"] == "~":
                    candidates.append(
                        {
                            "kind": "task",
                            "track_id": entry["track_id"],
                            "track_title": entry["title"],
                            "description": task["title"],
                        }
                    )
    if candidates:
        return candidates[:3]
    for entry in parse_tracks_registry(conductor_dir / "tracks.md"):
        plan_path = entry["track_dir"] / "plan.md"
        for phase in reversed(parse_plan(plan_path)):
            for task in reversed(phase["tasks"]):
                if task["marker"] == "x":
                    candidates.append(
                        {
                            "kind": "task",
                            "track_id": entry["track_id"],
                            "track_title": entry["title"],
                            "description": task["title"],
                        }
                    )
                    if len(candidates) >= 3:
                        return candidates[:3]
            if len(candidates) >= 3:
                return candidates[:3]
    return candidates[:3]
