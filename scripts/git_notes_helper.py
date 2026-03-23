from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--summary", required=True)
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    note = "\n".join(
        [
            f"Task: {args.task}",
            "",
            "Summary:",
            args.summary,
        ]
    )
    subprocess.run(["git", "notes", "add", "-f", "-m", note, args.sha], cwd=repo, check=True)
    print(json.dumps({"sha": args.sha, "task": args.task, "note_written": True}, indent=2))


if __name__ == "__main__":
    main()
