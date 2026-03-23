from __future__ import annotations

import argparse
import json
from pathlib import Path

from conductor_fs import (
    load_metadata,
    now_utc,
    refresh_portfolio_indexes,
    refresh_track_index,
    require_canonical_workspace,
    resolve_track_dir,
    update_registry_entry_status,
    write_metadata,
)


def repair_track(repo: Path, track_ref: str | None, status: str | None) -> dict[str, str]:
    conductor_dir = repo / "conductor"
    template_base = Path(__file__).resolve().parents[1]
    track_dir = resolve_track_dir(conductor_dir, track_ref)
    metadata = load_metadata(track_dir)
    if status:
        metadata["status"] = status
    metadata["updated_at"] = now_utc()
    write_metadata(track_dir, metadata)
    update_registry_entry_status(conductor_dir, template_base, metadata["track_id"], metadata["status"])
    refresh_track_index(track_dir, template_base)
    refresh_portfolio_indexes(conductor_dir, template_base)
    return {
        "track_id": metadata["track_id"],
        "status": metadata["status"],
        "track_path": str(track_dir).replace("\\", "/"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--track")
    parser.add_argument("--status")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    require_canonical_workspace(repo / "conductor")
    print(json.dumps(repair_track(repo, args.track, args.status), indent=2))


if __name__ == "__main__":
    main()
