from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from conductor_fs import require_canonical_workspace
from revert_flow import build_flow


def run_execute_revert(repo: Path, track_ref: str, task: str | None) -> dict[str, object]:
    command = [
        "python",
        str(Path(__file__).resolve().parent / "execute_revert.py"),
        "--repo",
        str(repo),
        "--track",
        track_ref,
        "--repair-state",
    ]
    if task:
        command.extend(["--task", task])
    result = subprocess.run(command, cwd=repo, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise SystemExit(result.stderr.strip() or result.stdout.strip() or "execute_revert.py failed")
    return json.loads(result.stdout)


def advance_revert_runtime(repo: Path, track_ref: str | None, task: str | None, action: str) -> dict[str, object]:
    require_canonical_workspace(repo / "conductor")

    if action == "start":
        return {"stage": "selection", "flow": build_flow(repo, None, None, False)}
    if action == "prepare":
        return {"stage": "confirmation", "flow": build_flow(repo, track_ref, task, False)}
    if action == "execute":
        if not track_ref:
            raise SystemExit("A track is required to execute a revert.")
        execution = run_execute_revert(repo, track_ref, task)
        return {"stage": "completed", "execution": execution}
    raise SystemExit(f"Unsupported revert runtime action '{action}'.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--track")
    parser.add_argument("--task")
    parser.add_argument("--action", choices=["start", "prepare", "execute"], required=True)
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    print(json.dumps(advance_revert_runtime(repo, args.track, args.task, args.action), indent=2))


if __name__ == "__main__":
    main()
