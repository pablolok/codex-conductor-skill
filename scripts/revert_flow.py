from __future__ import annotations

import argparse
import json
from pathlib import Path

from conductor_fs import collect_revert_candidates, require_canonical_workspace, resolve_track_dir
from revert_track import build_revert_plan


def selection_menu(candidates: list[dict[str, str]]) -> dict[str, object]:
    def normalize_label(text: str) -> str:
        for prefix in ("Task: ", "Phase: "):
            if text.startswith(prefix):
                return text[len(prefix) :]
        return text

    options = [
        {
            "label": f"[{item['kind'].title()}] {normalize_label(item['description'])}",
            "description": f"Track: {item['track_id']}",
        }
        for item in candidates[:4]
    ]
    return {
        "header": "Select Item",
        "question": "I found multiple in-progress items (or recently completed items). Please choose which one to revert:",
        "type": "choice",
        "multiSelect": False,
        "options": options,
    }


def target_confirmation(plan: dict[str, object]) -> dict[str, object]:
    return {
        "header": "Confirm",
        "question": f"You asked to revert the target: '{plan['target']}'. Is this correct?",
        "type": "yesno",
    }


def plan_confirmation(plan: dict[str, object]) -> dict[str, object]:
    return {
        "header": "Confirm Plan",
        "question": "Do you want to proceed with the drafted plan?",
        "type": "choice",
        "multiSelect": False,
        "options": [
            {"label": "Approve", "description": "Proceed with the revert actions."},
            {"label": "Revise", "description": "I want to change the revert plan."},
        ],
        "revise_prompt": {
            "header": "Revise",
            "question": "Please describe the changes needed for the revert plan.",
            "type": "text",
        },
        "summary": {
            "target": plan["target"],
            "commit_count": len(plan["commits"]),
            "commits": plan["commits"],
        },
    }


def build_flow(repo: Path, track_ref: str | None, task: str | None, candidates_only: bool) -> dict[str, object]:
    conductor_dir = repo / "conductor"
    candidates = collect_revert_candidates(conductor_dir)
    if candidates_only:
        return {
            "candidates": candidates,
            "checkpoints": [
                "Pick the smallest safe revert scope first.",
                "Prefer reverting the most recent recorded task or phase checkpoint.",
                "Repair plan.md, metadata.json, and review/verify artifacts after rollback.",
            ],
        }
    if not track_ref:
        if not candidates:
            raise SystemExit("No in-progress or recently completed items were found to revert.")
        return {
            "selection_menu": selection_menu(candidates),
            "candidates": candidates,
            "checkpoints": [
                "Choose the smallest safe revert scope first.",
                "If the desired target is missing, ask the user to clarify it before proceeding.",
            ],
        }
    track_dir = resolve_track_dir(conductor_dir, track_ref)
    plan = build_revert_plan(repo, track_dir, task)
    plan["checkpoints"] = [
        "Confirm the target task or phase before mutating git history.",
        "Revert associated implementation commits before plan-update commits.",
        "Realign plan.md markers, metadata status, and indexes after the revert.",
    ]
    plan["target_confirmation"] = target_confirmation(plan)
    plan["plan_confirmation"] = plan_confirmation(plan)
    return plan


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--track")
    parser.add_argument("--task")
    parser.add_argument("--candidates", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    require_canonical_workspace(repo / "conductor")
    print(json.dumps(build_flow(repo, args.track, args.task, args.candidates), indent=2))


if __name__ == "__main__":
    main()
