from __future__ import annotations

import argparse
import json
import os
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


def install_one(workspace_root: Path, catalog_item: dict) -> dict:
    skills_root = workspace_root / ".agents" / "skills"
    skills_root.mkdir(parents=True, exist_ok=True)
    destination = skills_root / catalog_item["name"]
    if destination.exists():
        force_rmtree(destination)
    repo_url, branch, folder = github_folder_from_raw(catalog_item["url"])
    temp_dir = workspace_root / ".agents" / ".tmp" / catalog_item["name"]
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
    return {
        "name": catalog_item["name"],
        "destination": str(destination),
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
