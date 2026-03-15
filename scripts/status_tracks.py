from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def scan(base: Path) -> list[dict]:
    items = []
    if not base.exists():
        return items
    for child in sorted(base.iterdir()):
        if not child.is_dir() or child.name == "_template":
            continue
        metadata = child / "metadata.json"
        if metadata.exists():
            items.append(json.loads(read_text(metadata)))
    return items


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    conductor = repo / "conductor"
    active = scan(conductor / "tracks")
    archived = scan(conductor / "archive")
    print("Active tracks:")
    if not active:
        print("- none")
    else:
        for item in active:
            print(f"- {item['id']} | {item['title']} | {item['status']} | {item['phase']} | {item['activeTask']}")
    print("Archived tracks:")
    if not archived:
        print("- none")
    else:
        for item in archived:
            print(f"- {item['id']} | {item['title']} | {item['status']} | {item['phase']}")


if __name__ == "__main__":
    main()
