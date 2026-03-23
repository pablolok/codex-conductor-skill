from __future__ import annotations

import argparse
import json
from pathlib import Path

from conversation_state import command_alias_path, init_session, resolve_session_path, update_session
from new_track_flow import build_new_track_flow
from setup_flow import build_setup_flow


APPROVE_DECISIONS = {
    "approve",
    "approved",
    "yes",
    "y",
    "install all",
    "hand-pick",
    "skip",
    "create branch",
    "use current",
    "interactive",
    "autogenerate",
}
REVISE_DECISIONS = {"revise", "suggest changes", "no", "n"}


def build_flow(repo: Path, command: str, target: str | None = None) -> dict[str, object]:
    skill_root = Path(__file__).resolve().parents[1]
    if command == "setup":
        return build_setup_flow(repo, skill_root)
    if command == "newTrack":
        if not target:
            raise SystemExit("newTrack flow requires a target title.")
        return build_new_track_flow(repo, target)
    raise SystemExit(f"Unsupported flow command '{command}'.")


def canonical_decision(decision: str | None) -> str | None:
    if decision is None:
        return None
    return decision.strip().lower()


def next_checkpoint_index(current_index: int, decision: str | None, checkpoint_count: int) -> int:
    normalized = canonical_decision(decision)
    if normalized is None:
        return current_index
    if normalized in REVISE_DECISIONS:
        return current_index
    if normalized in APPROVE_DECISIONS or normalized:
        return min(current_index + 1, checkpoint_count)
    return current_index


def load_session_state(path: Path) -> dict[str, object]:
    resolved = resolve_session_path(path)
    return json.loads(resolved.read_text(encoding="utf-8"))


def current_checkpoint_payload(repo: Path, command: str, session_path: Path, target: str | None = None) -> dict[str, object] | None:
    session = load_session_state(session_path)
    flow = build_flow(repo, command, target or session.get("target"))
    index = int(session.get("current_checkpoint", 0))
    checkpoints = flow["checkpoints"]
    if index >= len(checkpoints):
        return None
    return checkpoints[index]


def advance_flow(repo: Path, command: str, target: str | None = None, session_path: Path | None = None, decision: str | None = None) -> dict[str, object]:
    flow = build_flow(repo, command, target)
    checkpoints = flow["checkpoints"]
    if session_path is None:
        session = init_session(repo, command, target)
        index = 0
        resolved_path = Path(session["path"])
        alias_path = Path(session["alias_path"])
    else:
        session = load_session_state(session_path)
        index = int(session.get("current_checkpoint", 0))
        new_index = next_checkpoint_index(index, decision, len(checkpoints))
        session = update_session(session_path, new_index, decision or "resume")
        index = new_index
        resolved_path = resolve_session_path(session_path)
        alias_path = command_alias_path(repo, command)

    completed = index >= len(checkpoints)
    checkpoint = None if completed else checkpoints[index]
    return {
        "command": command,
        "target": target or session.get("target"),
        "session": {
            "session_id": session["session_id"],
            "path": str(resolved_path).replace("\\", "/"),
            "alias_path": str(alias_path).replace("\\", "/"),
        },
        "checkpoint_index": index,
        "checkpoint": checkpoint,
        "completed": completed,
        "overview": flow.get("overview"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--command", required=True, choices=["setup", "newTrack"])
    parser.add_argument("--target")
    parser.add_argument("--session")
    parser.add_argument("--decision")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    session_path = Path(args.session) if args.session else None
    print(json.dumps(advance_flow(repo, args.command, args.target, session_path, args.decision), indent=2))


if __name__ == "__main__":
    main()
