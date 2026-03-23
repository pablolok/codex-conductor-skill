from __future__ import annotations

import argparse
import json
from pathlib import Path

from bootstrap_conductor import ensure_shared_context
from conductor_fs import write_text


APPROVED_SHARED_FILES = {
    "product.md",
    "product-guidelines.md",
    "tech-stack.md",
    "workflow.md",
}


def normalize_newline(content: str) -> str:
    return content if content.endswith("\n") else f"{content}\n"


def apply_setup_drafts(repo: Path, drafts: dict[str, str]) -> Path:
    template_base = Path(__file__).resolve().parents[1]
    ensure_shared_context(repo, template_base)
    conductor_dir = repo / "conductor"
    for relative_path, content in drafts.items():
        if relative_path not in APPROVED_SHARED_FILES:
            continue
        write_text(conductor_dir / relative_path, normalize_newline(content))
    return conductor_dir


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--drafts-json", required=True)
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    drafts = json.loads(Path(args.drafts_json).read_text(encoding="utf-8"))
    conductor_dir = apply_setup_drafts(repo, drafts)
    print(str(conductor_dir))


if __name__ == "__main__":
    main()
