from __future__ import annotations

import argparse
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


def session_root(repo: Path) -> Path:
    return repo / ".agents" / "conductor_sessions"


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def command_alias_path(repo: Path, command: str) -> Path:
    return session_root(repo) / f"{command}.json"


def resolve_session_path(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(path)
    state = json.loads(path.read_text(encoding="utf-8"))
    active = state.get("active_session")
    if active:
        return path.parent / active
    return path


def write_command_alias(repo: Path, command: str, session_file: Path) -> None:
    alias = command_alias_path(repo, command)
    payload = {
        "command": command,
        "active_session": session_file.name,
        "updated_at": now_utc(),
    }
    alias.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def init_session(repo: Path, command: str, target: str | None = None) -> dict[str, object]:
    root = session_root(repo)
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{command}-{uuid.uuid4().hex[:8]}.json"
    state = {
        "session_id": path.stem,
        "command": command,
        "target": target,
        "status": "active",
        "created_at": now_utc(),
        "updated_at": now_utc(),
        "current_checkpoint": 0,
        "history": [],
    }
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    write_command_alias(repo, command, path)
    state["path"] = str(path)
    state["alias_path"] = str(command_alias_path(repo, command))
    return state


def update_session(path: Path, checkpoint: int, decision: str, notes: str | None = None) -> dict[str, object]:
    resolved = resolve_session_path(path)
    state = json.loads(resolved.read_text(encoding="utf-8"))
    state["current_checkpoint"] = checkpoint
    state["updated_at"] = now_utc()
    state.setdefault("history", []).append(
        {
            "timestamp": state["updated_at"],
            "checkpoint": checkpoint,
            "decision": decision,
            "notes": notes or "",
        }
    )
    resolved.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state


def close_session(path: Path, status: str) -> dict[str, object]:
    resolved = resolve_session_path(path)
    state = json.loads(resolved.read_text(encoding="utf-8"))
    state["status"] = status
    state["updated_at"] = now_utc()
    resolved.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state


def session_blueprint(repo: Path, command: str, target: str | None = None) -> dict[str, object]:
    path = command_alias_path(repo, command)
    return {
        "command": command,
        "target": target,
        "resume_supported": True,
        "state_path": str(path).replace("\\", "/"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="action", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--repo", required=True)
    init_parser.add_argument("--command", required=True)
    init_parser.add_argument("--target")

    update_parser = subparsers.add_parser("update")
    update_parser.add_argument("--path", required=True)
    update_parser.add_argument("--checkpoint", type=int, required=True)
    update_parser.add_argument("--decision", required=True)
    update_parser.add_argument("--notes")

    close_parser = subparsers.add_parser("close")
    close_parser.add_argument("--path", required=True)
    close_parser.add_argument("--status", required=True)

    args = parser.parse_args()
    if args.action == "init":
        result = init_session(Path(args.repo).resolve(), args.command, args.target)
    elif args.action == "update":
        result = update_session(Path(args.path), args.checkpoint, args.decision, args.notes)
    else:
        result = close_session(Path(args.path), args.status)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
