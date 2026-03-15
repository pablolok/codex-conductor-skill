from __future__ import annotations

import argparse

from pathlib import Path

from conductor_fs import scan_tracks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    conductor = repo / "conductor"
    active = scan_tracks(conductor / "tracks", "conductor/tracks")
    archived = scan_tracks(conductor / "archive", "conductor/archive")

    print("Active tracks:")
    if not active:
        print("- none")
    else:
        for item in active:
            print(
                f"- {item['id']} | {item['title']} | {item['status']} | "
                f"{item['phase']} | {item['activeTask']} | {item['path']}"
            )

    print("Archived tracks:")
    if not archived:
        print("- none")
    else:
        for item in archived:
            print(f"- {item['id']} | {item['title']} | {item['status']} | {item['phase']} | {item['path']}")


if __name__ == "__main__":
    main()
