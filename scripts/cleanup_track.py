from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from conductor_fs import parse_tracks_registry, refresh_portfolio_indexes, remove_track_from_registry, require_canonical_workspace, resolve_track_dir


def delete_track(conductor_dir: Path, track_dir: Path, template_base: Path) -> None:
    shutil.rmtree(track_dir)
    remove_track_from_registry(conductor_dir, template_base, track_dir.name)
    refresh_portfolio_indexes(conductor_dir, template_base)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--track")
    parser.add_argument("--action", choices=["archive", "delete", "skip"], required=True)
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    conductor_dir = repo / "conductor"
    template_base = Path(__file__).resolve().parents[1]
    require_canonical_workspace(conductor_dir)
    track_dir = resolve_track_dir(conductor_dir, args.track)

    if args.action == "archive":
        result = {"action": "archive", "next_step": "run scripts/archive_tracks.py --repo <repo-root>"}
    elif args.action == "delete":
        delete_track(conductor_dir, track_dir, template_base)
        result = {"action": "delete", "deleted": track_dir.name}
    else:
        result = {"action": "skip", "track": track_dir.name}

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
