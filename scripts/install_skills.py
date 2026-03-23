from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import stat
from pathlib import Path

from skills_catalog import load_catalog


def github_folder_from_raw(url: str) -> tuple[str, str, str]:
    prefix = "https://raw.githubusercontent.com/"
    if not url.startswith(prefix):
        raise SystemExit(f"Unsupported skill URL: {url}")
    remainder = url[len(prefix):].strip("/")
    owner, repo, branch, *path_parts = remainder.split("/")
    return f"https://github.com/{owner}/{repo}.git", branch, "/".join(path_parts)


def force_rmtree(path: Path) -> None:
    def onerror(func, target, exc_info):
        os.chmod(target, stat.S_IWRITE)
        func(target)

    if path.exists():
        shutil.rmtree(path, onerror=onerror)


def gemini_skills_root(workspace_root: Path) -> Path:
    return workspace_root / ".gemini" / "skills"


def codex_skills_root(workspace_root: Path) -> Path:
    return workspace_root / ".codex" / "skills"


def parse_skill_description(skill_path: Path) -> str | None:
    content = skill_path.read_text(encoding="utf-8")
    match = re.search(r"^description:\s*(.+)$", content, re.MULTILINE)
    if not match:
        return None
    return match.group(1).strip()


def codex_bridge_content(skill_name: str, description: str | None = None) -> str:
    title = skill_name.replace("-", " ").title()
    bridge_description = description or f"Use the installed Gemini {skill_name} skill as the source of truth."
    return "\n".join(
        [
            "---",
            f"name: {skill_name}",
            f"description: {bridge_description}",
            "---",
            "",
            f"# {title} Bridge",
            "",
            f"Use the installed Gemini skill at `.gemini/skills/{skill_name}/SKILL.md` as the source of truth.",
            "",
            "Workflow:",
            "",
            f"1. Read and follow `.gemini/skills/{skill_name}/SKILL.md`.",
            f"2. If that skill references scripts, metadata, or companion files, resolve them from `.gemini/skills/{skill_name}/`.",
            "3. Do not treat this bridge folder as the implementation source. It exists only so Codex can discover the skill without copying the Gemini payload.",
            "",
            "## Codex Integration",
            "",
            "For Codex-managed projects, keep the responsibilities split:",
            "",
            "- `.gemini/skills/` contains the actual Gemini/Conductor skill implementations.",
            "- `.codex/skills/` contains only Codex bridges and Codex-specific integration notes.",
            "",
            "When installing, updating, or auditing skills from Codex, preserve both layers. Do not replace Gemini skills with Codex wrappers and do not copy full Gemini payloads into `.codex/skills`.",
            "",
        ]
    )


def write_codex_bridge(workspace_root: Path, skill_name: str, description: str | None = None) -> Path:
    bridge_dir = codex_skills_root(workspace_root) / skill_name
    bridge_dir.mkdir(parents=True, exist_ok=True)
    skill_path = bridge_dir / "SKILL.md"
    skill_path.write_text(codex_bridge_content(skill_name, description), encoding="utf-8")
    return skill_path


def install_one(workspace_root: Path, catalog_item: dict) -> dict:
    skills_root = gemini_skills_root(workspace_root)
    skills_root.mkdir(parents=True, exist_ok=True)
    destination = skills_root / catalog_item["name"]
    if destination.exists():
        force_rmtree(destination)
    repo_url, branch, folder = github_folder_from_raw(catalog_item["url"])
    temp_dir = workspace_root / ".gemini" / ".tmp" / catalog_item["name"]
    if temp_dir.exists():
        force_rmtree(temp_dir)
    temp_dir.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse", "--branch", branch, repo_url, str(temp_dir)], check=True)
    subprocess.run(["git", "-C", str(temp_dir), "sparse-checkout", "set", folder], check=True)
    source = temp_dir / folder
    if not source.exists():
        raise SystemExit(f"Skill source folder not found after sparse checkout: {folder}")
    shutil.copytree(source, destination)
    force_rmtree(temp_dir)
    bridge = write_codex_bridge(workspace_root, catalog_item["name"], parse_skill_description(source / "SKILL.md"))
    return {
        "name": catalog_item["name"],
        "destination": str(destination),
        "codex_bridge": str(bridge),
        "url": catalog_item["url"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--skills", nargs="+", required=True)
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    catalog = {item["name"]: item for item in load_catalog(Path(args.catalog))}
    installed = []
    for skill_name in args.skills:
        if skill_name not in catalog:
            raise SystemExit(f"Unknown skill '{skill_name}' in catalog.")
        installed.append(install_one(repo, catalog[skill_name]))
    print(json.dumps({"installed": installed, "reload_required": True}, indent=2))


if __name__ == "__main__":
    main()
