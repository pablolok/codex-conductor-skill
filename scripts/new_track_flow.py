from __future__ import annotations

import argparse
import json
from pathlib import Path

from conductor_fs import (
    canonical_track_id,
    existing_track_ids,
    existing_track_short_names,
    infer_track_type,
    read_text,
    require_canonical_workspace,
    slugify_short_name,
)
from draft_new_track import render_with
from skills_catalog import installed_skill_names, partition_recommended_skills, recommend_skills
from workflow_policy import parse_workflow_policy


def approval_question(header: str, body: str, approve: str, revise: str) -> dict[str, object]:
    return {
        "header": header,
        "question": body,
        "type": "choice",
        "multiSelect": False,
        "options": [
            {"label": "Approve", "description": approve},
            {"label": "Revise", "description": revise},
        ],
    }


def spec_questions(track_type: str, title: str) -> list[list[dict[str, object]]]:
    if track_type == "feature":
        return [
            [
                {
                    "header": "Outcome",
                    "question": f"What user or product outcome should '{title}' deliver?",
                    "type": "choice",
                    "multiSelect": True,
                    "options": [
                        {"label": "New capability", "description": "Adds a new user-visible workflow."},
                        {"label": "Simpler flow", "description": "Improves an existing user journey."},
                        {"label": "Operational gain", "description": "Improves maintainability or support operations."},
                    ],
                },
                {
                    "header": "Surface",
                    "question": "Which surfaces are in scope?",
                    "type": "choice",
                    "multiSelect": True,
                    "options": [
                        {"label": "UI", "description": "User interface changes are required."},
                        {"label": "API", "description": "Service or contract changes are required."},
                        {"label": "Storage", "description": "Persistence or schema changes are required."},
                    ],
                },
                {
                    "header": "Rules",
                    "question": "Which behavior constraints should the spec make explicit?",
                    "type": "choice",
                    "multiSelect": True,
                    "options": [
                        {"label": "Validation", "description": "Input or state validation must be clear."},
                        {"label": "Permissions", "description": "Authorization or role behavior matters."},
                        {"label": "Compatibility", "description": "Existing integrations or data must keep working."},
                    ],
                },
                {
                    "header": "Non-goals",
                    "question": "Which scope boundaries should the spec call out?",
                    "type": "choice",
                    "multiSelect": True,
                    "options": [
                        {"label": "No redesign", "description": "Avoid unrelated UX or architecture changes."},
                        {"label": "No migrations", "description": "Avoid data migrations unless required."},
                        {"label": "No broad refactor", "description": "Keep changes limited to the feature slice."},
                    ],
                },
            ]
        ]
    return [
        [
            {
                "header": "Scope",
                "question": f"What best describes the target for '{title}'?",
                "type": "choice",
                "multiSelect": False,
                "options": [
                    {"label": "Bug fix", "description": "Repair incorrect or regressed behavior."},
                    {"label": "Chore", "description": "Maintenance or housekeeping work."},
                    {"label": "Refactor", "description": "Internal improvement without intended behavior change."},
                ],
            },
            {
                "header": "Evidence",
                "question": "What evidence should the spec require before the work is considered done?",
                "type": "choice",
                "multiSelect": True,
                "options": [
                    {"label": "Repro closed", "description": "The original problem can no longer be reproduced."},
                    {"label": "Tests added", "description": "Automated coverage guards the changed behavior."},
                    {"label": "Docs updated", "description": "Operational or user docs reflect the change."},
                ],
            },
            {
                "header": "Risk",
                "question": "What should the spec protect while this work is done?",
                "type": "choice",
                "multiSelect": True,
                "options": [
                    {"label": "Behavior parity", "description": "Avoid unintended changes outside the target issue."},
                    {"label": "Data safety", "description": "Protect persisted or migrated data."},
                    {"label": "Release safety", "description": "Keep rollback and verification straightforward."},
                ],
            },
        ]
    ]


def workflow_requires_checkpoint(workflow_text: str) -> bool:
    return bool(parse_workflow_policy(workflow_text)["requires_phase_checkpoints"])


def build_new_track_flow(repo: Path, title: str) -> dict[str, object]:
    conductor_dir = repo / "conductor"
    require_canonical_workspace(conductor_dir)
    for required in ("product.md", "tech-stack.md", "workflow.md", "tracks.md"):
        if not (conductor_dir / required).exists():
            raise SystemExit(f"Missing required conductor file: {required}")

    short_name = slugify_short_name(title)
    if short_name in existing_track_short_names(conductor_dir):
        raise SystemExit(
            f"A track with short name '{short_name}' already exists. Choose a different title or resume the existing track."
        )

    workflow_text = read_text(conductor_dir / "workflow.md")
    track_id = canonical_track_id(title, existing_track_ids(conductor_dir))
    track_type = infer_track_type(title)
    template_base = Path(__file__).resolve().parents[1]
    draft_files = render_with(
        template_base,
        {
            "track_id": track_id,
            "type": track_type,
            "status": "new",
            "title": title,
            "path": f"conductor/tracks/{track_id}",
        },
        title,
    )
    context = "\n".join(
        [
            read_text(conductor_dir / "product.md"),
            read_text(conductor_dir / "product-guidelines.md"),
            read_text(conductor_dir / "tech-stack.md"),
            read_text(conductor_dir / "workflow.md"),
            draft_files["spec.md"],
            draft_files["plan.md"],
        ]
    )
    catalog_path = Path(__file__).resolve().parents[1] / "skills" / "catalog.md"
    recommendations = recommend_skills(catalog_path, context)
    skill_partition = partition_recommended_skills(recommendations, installed_skill_names(repo))
    checkpoints: list[dict[str, object]] = [
        {
            "kind": "branch",
            "question": {
                "header": "Branch",
                "question": "Should this track use a dedicated branch before implementation begins?",
                "type": "choice",
                "multiSelect": False,
                "options": [
                    {"label": "Create branch", "description": "Create a dedicated branch for this track."},
                    {"label": "Use current", "description": "Stay on the current branch if it is already dedicated."},
                ],
            },
        },
        {
            "kind": "interactive",
            "file": "spec.md",
            "intro": "I will now guide the specification for this track.",
            "question_batches": spec_questions(track_type, title),
        },
        {
            "kind": "approval",
            "file": "spec.md",
            "question": approval_question(
                "Confirm Spec",
                f"Please review the drafted Specification below. Does this accurately capture the requirements?\n\n---\n\n{draft_files['spec.md']}",
                "The specification looks correct, proceed to planning.",
                "Revise the requirements before planning.",
            ),
        },
        {
            "kind": "approval",
            "file": "plan.md",
            "question": approval_question(
                "Confirm Plan",
                f"Please review the drafted Implementation Plan below. Does this look correct and cover all necessary steps?\n\n---\n\n{draft_files['plan.md']}",
                "The plan looks correct, proceed.",
                "Revise the implementation plan.",
            ),
            "workflow_requires_phase_checkpoint": workflow_requires_checkpoint(workflow_text),
        },
    ]
    if recommendations:
        checkpoints.append(
            {
                "kind": "skills",
                "question": {
                    "header": "Install Skills",
                    "question": "I found skills that could help with this track. Which ones should be installed now?",
                    "type": "choice",
                    "multiSelect": True,
                    "options": [
                        {"label": item["name"], "description": item["description"]} for item in recommendations
                    ],
                },
                "installed_recommendations": skill_partition["installed"],
                "missing_recommendations": skill_partition["missing"],
                "reload_instruction": "New skills installed. Please run `/skills reload` and confirm before continuing.",
            }
        )
    return {
        "track": {
            "title": title,
            "short_name": short_name,
            "track_id": track_id,
            "track_type": track_type,
            "path": f"conductor/tracks/{track_id}",
        },
        "checkpoints": checkpoints,
        "drafts": draft_files,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--title", required=True)
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    print(json.dumps(build_new_track_flow(repo, args.title), indent=2))


if __name__ == "__main__":
    main()
