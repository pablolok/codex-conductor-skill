from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

from conductor_fs import (
    now_utc,
    refresh_portfolio_indexes,
    refresh_track_index,
    remove_track_from_registry,
    require_canonical_workspace,
    resolve_track_dir,
    write_metadata,
)


def delete_track(conductor_dir: Path, track_dir: Path, template_base: Path) -> None:
    shutil.rmtree(track_dir)
    remove_track_from_registry(conductor_dir, template_base, track_dir.name)
    refresh_portfolio_indexes(conductor_dir, template_base)


def mark_archived(track_dir: Path, template_base: Path) -> None:
    metadata_path = track_dir / "metadata.json"
    if not metadata_path.exists():
        return
    import json

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["status"] = "archived"
    metadata["archived_at"] = now_utc()
    metadata["updated_at"] = metadata["archived_at"]
    metadata["path"] = f"conductor/archive/{track_dir.name}"
    write_metadata(track_dir, metadata)
    refresh_track_index(track_dir, template_base)


def stage_cleanup_paths(repo: Path, paths: list[Path]) -> None:
    if not paths:
        return
    normalized = [str(path.resolve()) for path in paths]
    subprocess.run(["git", "add", "-A", "--", *normalized], cwd=repo, check=True)


def commit_cleanup(repo: Path, message: str, paths: list[Path]) -> None:
    stage_cleanup_paths(repo, paths)
    subprocess.run(["git", "commit", "-m", message], cwd=repo, check=True)


def archive_track(repo: Path, conductor_dir: Path, track_dir: Path, template_base: Path, commit_changes: bool) -> dict[str, object]:
    archive_dir = conductor_dir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    destination = archive_dir / track_dir.name
    if destination.exists():
        raise SystemExit(f"Could not archive '{track_dir.name}' because '{destination}' already exists.")
    shutil.move(str(track_dir), str(destination))
    mark_archived(destination, template_base)
    remove_track_from_registry(conductor_dir, template_base, destination.name)
    refresh_portfolio_indexes(conductor_dir, template_base)
    committed = False
    if commit_changes:
        commit_cleanup(
            repo,
            f"chore(conductor): Archive track '{destination.name}'",
            [track_dir, destination, conductor_dir / "index.md", conductor_dir / "tracks.md"],
        )
        committed = True
    return {"action": "archive", "track": destination.name, "archived_to": str(destination.resolve()), "committed": committed}


def execute_cleanup_action(repo: Path, track_ref: str | None, action: str, commit_changes: bool) -> dict[str, object]:
    conductor_dir = repo / "conductor"
    template_base = Path(__file__).resolve().parents[1]
    require_canonical_workspace(conductor_dir)
    track_dir = resolve_track_dir(conductor_dir, track_ref)

    if action == "archive":
        return archive_track(repo, conductor_dir, track_dir, template_base, commit_changes)
    if action == "delete":
        delete_track(conductor_dir, track_dir, template_base)
        committed = False
        if commit_changes:
            commit_cleanup(
                repo,
                f"chore(conductor): Delete track '{track_dir.name}'",
                [track_dir, conductor_dir / "index.md", conductor_dir / "tracks.md"],
            )
            committed = True
        return {"action": "delete", "deleted": track_dir.name, "committed": committed}
    if action == "skip":
        return {"action": "skip", "track": track_dir.name, "committed": False}
    raise SystemExit(f"Unsupported cleanup action '{action}'.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--track")
    parser.add_argument("--action", choices=["archive", "delete", "skip"], required=True)
    parser.add_argument("--commit", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    print(json.dumps(execute_cleanup_action(repo, args.track, args.action, args.commit), indent=2))


if __name__ == "__main__":
    main()
