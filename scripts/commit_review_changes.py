from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def has_worktree_changes(repo: Path) -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=True,
    )
    return bool(result.stdout.strip())


def run_git(repo: Path, args: list[str]) -> str:
    result = subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, check=True)
    return result.stdout.strip()


def commit_review_changes(repo: Path, message: str = "fix(conductor): Apply review suggestions") -> dict[str, object]:
    if not has_worktree_changes(repo):
        return {"committed": False, "reason": "no_changes"}

    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", message], cwd=repo, check=True)
    return {
        "committed": True,
        "message": message,
        "sha": run_git(repo, ["rev-parse", "--short", "HEAD"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--message", default="fix(conductor): Apply review suggestions")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    print(json.dumps(commit_review_changes(repo, args.message), indent=2))


if __name__ == "__main__":
    main()
