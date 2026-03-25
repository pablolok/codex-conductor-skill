from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from conversation_state import session_blueprint
from conductor_fs import detect_styleguide_names, detect_workspace_kind, infer_product_name, read_text
from draft_setup_docs import build_guidelines, build_product, build_tech_stack, build_workflow
from setup_workspace import audit_existing_artifacts, detect_project_maturity, determine_resume_target
from skills_catalog import installed_skill_names, partition_recommended_skills, recommend_skills


def git_has_uncommitted_changes(repo: Path) -> bool:
    if not (repo / ".git").exists():
        return False
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return False
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    return any(" conductor/" not in line.replace("\\", "/") for line in lines)


def available_styleguides(skill_root: Path) -> list[str]:
    styleguide_dir = skill_root / "assets" / "styleguides"
    return sorted(item.name for item in styleguide_dir.iterdir() if item.is_file())


def mode_question(file_name: str, prompt: str, interactive: str, autogenerate: str) -> dict[str, object]:
    return {
        "kind": "mode",
        "file": file_name,
        "question": {
            "header": file_name,
            "question": prompt,
            "type": "choice",
            "multiSelect": False,
            "options": [
                {"label": "Interactive", "description": interactive},
                {"label": "Autogenerate", "description": autogenerate},
            ],
        },
    }


def approval_question(file_name: str, content: str) -> dict[str, object]:
    return {
        "kind": "approval",
        "file": file_name,
        "question": {
            "header": "Review Draft",
            "question": f"Please review the drafted {file_name} below. What would you like to do next?\n\n---\n\n{content}",
            "type": "choice",
            "multiSelect": False,
            "options": [
                {"label": "Approve", "description": "The draft looks correct, continue."},
                {"label": "Suggest changes", "description": "Revise the draft before continuing."},
            ],
        },
    }


def build_product_questions(maturity: str, product_name: str) -> list[dict[str, object]]:
    question = {
        "header": "Product",
        "question": "Which product framing best matches this repository?",
        "type": "choice",
        "multiSelect": False,
        "options": [
            {"label": "End-user app", "description": f"{product_name} primarily delivers features to end users."},
            {"label": "Platform/service", "description": f"{product_name} primarily exposes internal or external services."},
            {"label": "Library/tooling", "description": f"{product_name} primarily supports other developers or systems."},
        ],
    }
    audience = {
        "header": "Users",
        "question": "Who should the product optimize for first?",
        "type": "choice",
        "multiSelect": True,
        "options": [
            {"label": "External users", "description": "Optimize for customers or public users."},
            {"label": "Internal teams", "description": "Optimize for operators, support, or internal stakeholders."},
            {"label": "Developers", "description": "Optimize for contributors, integrators, or maintainers."},
        ],
    }
    goals = {
        "header": "Goals",
        "question": "Which outcomes matter most in the product guide?",
        "type": "choice",
        "multiSelect": True,
        "options": [
            {"label": "Reliability", "description": "Emphasize stable, predictable behavior."},
            {"label": "Velocity", "description": "Emphasize fast iteration and delivery."},
            {"label": "Clarity", "description": "Emphasize understandable UX, docs, and workflows."},
        ],
    }
    questions = [question, audience, goals]
    if maturity == "brownfield":
        questions.append(
            {
                "header": "Preserve",
                "question": "What should setup preserve from the existing repository direction?",
                "type": "choice",
                "multiSelect": True,
                "options": [
                    {"label": "Current scope", "description": "Keep the current mission and product boundary."},
                    {"label": "Existing users", "description": "Preserve the current user/stakeholder expectations."},
                    {"label": "Delivery model", "description": "Preserve the current implementation and release model."},
                ],
            }
        )
    return questions


def build_guideline_questions(maturity: str) -> list[dict[str, object]]:
    questions = [
        {
            "header": "Voice",
            "question": "What tone should product-facing content use?",
            "type": "choice",
            "multiSelect": False,
            "options": [
                {"label": "Direct", "description": "Plain, concise, and operational."},
                {"label": "Supportive", "description": "Guiding and user-friendly without excess detail."},
                {"label": "Technical", "description": "Precise and engineering-first."},
            ],
        },
        {
            "header": "UX",
            "question": "Which UX principles should be explicit in the guidelines?",
            "type": "choice",
            "multiSelect": True,
            "options": [
                {"label": "Consistency", "description": "Preserve predictable patterns and terminology."},
                {"label": "Feedback", "description": "Make state and outcomes visible."},
                {"label": "Recovery", "description": "Support error handling and reversal paths."},
            ],
        },
        {
            "header": "Quality",
            "question": "Which engineering-quality rules should the product guidelines reinforce?",
            "type": "choice",
            "multiSelect": True,
            "options": [
                {"label": "Verification", "description": "Require evidence for user-visible changes."},
                {"label": "Accessibility", "description": "Preserve accessibility and inclusive behavior."},
                {"label": "Minimal scope", "description": "Prefer focused, reviewable increments."},
            ],
        },
    ]
    if maturity == "brownfield":
        questions.append(
            {
                "header": "Existing UI",
                "question": "How closely should the guidelines preserve existing repo patterns?",
                "type": "choice",
                "multiSelect": False,
                "options": [
                    {"label": "Preserve", "description": "Keep the established style unless there is a defect."},
                    {"label": "Tighten", "description": "Preserve direction but formalize the rules."},
                    {"label": "Modernize", "description": "Allow targeted updates while respecting the product."},
                ],
            }
        )
    return questions


def build_tech_questions(maturity: str, detected_stack: str) -> list[dict[str, object]]:
    if maturity == "brownfield":
        return [
            {
                "header": "Tech Stack",
                "question": f"Is this inferred stack correct?\n\n{detected_stack}",
                "type": "yesno",
            },
            {
                "header": "Stack Fix",
                "question": "If the inferred stack is incomplete, what should be corrected?",
                "type": "text",
                "placeholder": "List the missing or incorrect stack details",
            },
        ]
    return [
        {
            "header": "Language",
            "question": "Which implementation languages should the project use?",
            "type": "choice",
            "multiSelect": True,
            "options": [
                {"label": "TypeScript", "description": "Strong choice for modern web and tooling."},
                {"label": "Python", "description": "Good for services, scripting, and data-heavy work."},
                {"label": "C#", "description": "Good for .NET applications, services, and desktop apps."},
            ],
        },
        {
            "header": "Frontend",
            "question": "Which frontend direction should the project use?",
            "type": "choice",
            "multiSelect": True,
            "options": [
                {"label": "React", "description": "Component-oriented web UI."},
                {"label": "Server rendered", "description": "Prefer MVC, Razor, or template-driven UI."},
                {"label": "No frontend", "description": "This is backend-only or tooling-first."},
            ],
        },
        {
            "header": "Backend",
            "question": "Which backend direction should the project use?",
            "type": "choice",
            "multiSelect": True,
            "options": [
                {"label": "HTTP API", "description": "Expose service endpoints."},
                {"label": "Worker/jobs", "description": "Prefer background processing or automation."},
                {"label": "Embedded/local", "description": "Prefer local app or CLI execution."},
            ],
        },
        {
            "header": "Data",
            "question": "What persistence model should the project target?",
            "type": "choice",
            "multiSelect": True,
            "options": [
                {"label": "SQL", "description": "Relational storage and structured schema."},
                {"label": "Document", "description": "Flexible or document-oriented persistence."},
                {"label": "No database", "description": "No persistent data layer is required yet."},
            ],
        },
    ]


def build_workflow_questions(styleguides: list[str]) -> list[dict[str, object]]:
    return [
        {
            "header": "Workflow",
            "question": "Should setup preserve the official Conductor workflow template unless you explicitly request edits?",
            "type": "yesno",
        },
        {
            "header": "Commands",
            "question": "Should the Development Commands examples in workflow.md be tailored to this repository now?",
            "type": "yesno",
        },
        {
            "header": "Customize",
            "question": "If workflow.md needs edits beyond command examples, how should setup proceed?",
            "type": "choice",
            "multiSelect": False,
            "options": [
                {"label": "Keep Official", "description": "Preserve the upstream wording and structure."},
                {"label": "Review First", "description": "Discuss proposed edits before changing the template."},
                {"label": "Repo Specific", "description": "Adapt the workflow text for this repository now."},
            ],
        },
        {
            "header": "Guides",
            "question": "Which code style guides should setup install into conductor/code_styleguides/?",
            "type": "choice",
            "multiSelect": True,
            "options": [{"label": name, "description": f"Install {name} into the workspace."} for name in styleguides],
        },
    ]


def build_styleguide_mode_question(recommended: list[str]) -> dict[str, object]:
    description = ", ".join(recommended) if recommended else "no specific recommendation"
    return {
        "header": "Code Style Guide",
        "question": f"How would you like to proceed with code style guides? Recommended: {description}",
        "type": "choice",
        "multiSelect": False,
        "options": [
            {"label": "Recommended", "description": "Use the recommended guides."},
            {"label": "Select from Library", "description": "Choose guides manually from the library."},
        ],
    }


def build_styleguide_library_batches(styleguides: list[str]) -> list[dict[str, object]]:
    batches = []
    for index in range(0, len(styleguides), 4):
        group = styleguides[index : index + 4]
        options = [{"label": name, "description": f"Install {name} into the workspace."} for name in group]
        if len(options) == 1:
            options.append({"label": "None", "description": "Do not add another guide from this batch."})
        batches.append(
            {
                "header": "Code Style Guide",
                "question": f"Which code style guides would you like to include? (Part {index // 4 + 1})",
                "type": "choice",
                "multiSelect": True,
                "options": options,
            }
        )
    return batches


def build_setup_flow(repo: Path, skill_root: Path) -> dict[str, object]:
    conductor_dir = repo / "conductor"
    maturity, reasons = detect_project_maturity(repo)
    artifacts = audit_existing_artifacts(conductor_dir)
    resume = determine_resume_target(artifacts, conductor_dir)
    catalog_path = skill_root / "skills" / "catalog.md"
    context = "\n".join(
        [
            read_text(repo / "README.md"),
            read_text(repo / "AGENTS.md"),
            read_text(conductor_dir / "product.md"),
            read_text(conductor_dir / "product-guidelines.md"),
            read_text(conductor_dir / "tech-stack.md"),
            read_text(conductor_dir / "workflow.md"),
        ]
    )
    drafts = {
        "product.md": build_product(repo),
        "product-guidelines.md": build_guidelines(repo),
        "tech-stack.md": build_tech_stack(repo),
        "workflow.md": build_workflow(repo),
    }
    styleguides = available_styleguides(skill_root)
    recommended_styleguides = detect_styleguide_names(repo)
    product_name = infer_product_name(repo)
    detected_stack = read_text(conductor_dir / "tech-stack.md") or drafts["tech-stack.md"]
    recommendations = recommend_skills(catalog_path, context)
    skill_partition = partition_recommended_skills(recommendations, installed_skill_names(repo))
    checkpoints = [
        {
            "kind": "permission",
            "question": {
                "header": "Permission",
                "question": "A brownfield project has been detected. May I perform a read-only scan to analyze the repository?",
                "type": "yesno",
            },
            "when": "brownfield",
        },
        mode_question(
            "product.md",
            "How would you like to define the product details?",
            "Guide the product definition with focused questions.",
            "Draft the product guide from the repository context.",
        ),
        {
            "kind": "interactive",
            "file": "product.md",
            "questions": build_product_questions(maturity, product_name),
        },
        approval_question("product.md", drafts["product.md"]),
        mode_question(
            "product-guidelines.md",
            "How would you like to define the product guidelines?",
            "Choose tone, UX principles, and quality rules interactively.",
            "Draft repository-appropriate guidelines automatically.",
        ),
        {
            "kind": "interactive",
            "file": "product-guidelines.md",
            "questions": build_guideline_questions(maturity),
        },
        approval_question("product-guidelines.md", drafts["product-guidelines.md"]),
        mode_question(
            "tech-stack.md",
            "How would you like to define the technology stack?",
            "Confirm or select the major runtime components interactively.",
            "Draft the tech stack from the repo context.",
        ),
        {
            "kind": "interactive",
            "file": "tech-stack.md",
            "questions": build_tech_questions(maturity, detected_stack),
        },
        approval_question("tech-stack.md", drafts["tech-stack.md"]),
        {
            "kind": "interactive",
            "file": "workflow.md",
            "questions": build_workflow_questions(styleguides),
            "recommended_styleguides": recommended_styleguides,
            "styleguide_mode_question": build_styleguide_mode_question(recommended_styleguides),
            "styleguide_library_batches": build_styleguide_library_batches(styleguides),
        },
        approval_question("workflow.md", drafts["workflow.md"]),
    ]
    checkpoints.append(
        {
            "kind": "skills",
            "question": {
                "header": "Install Skills",
                "question": "I found recommended skills for this repository. How would you like to proceed?",
                "type": "choice",
                "multiSelect": False,
                "options": [
                    {"label": "Install All", "description": "Install all recommended skills."},
                    {"label": "Hand-pick", "description": "Select specific skills from the catalog."},
                    {"label": "Skip", "description": "Do not install any skills right now."},
                ],
            },
            "recommended_skills": recommendations,
            "installed_recommendations": skill_partition["installed"],
            "missing_recommendations": skill_partition["missing"],
            "hand_pick_prompt": {
                "header": "Select Skills",
                "question": "Which skills would you like to install? Type the names separated by commas.",
                "type": "text",
                "placeholder": "e.g. firebase-auth-basics, firebase-firestore-basics",
            },
            "skip_reason": "No recommended skills were detected for this repository context." if not recommendations else "",
            "reload_instruction": "New skills installed. Please run `/skills reload` and confirm before continuing.",
        }
    )
    checkpoints.append(
        {
            "kind": "confirm",
            "question": {
                "header": "Confirm Setup",
                "question": "Please confirm the proposed shared context, workflow policy, and files to materialize under conductor/.",
                "type": "yesno",
            },
        }
    )
    flow = {
        "overview": [
            "Project discovery",
            "Shared context drafting",
            "Workflow confirmation",
            "Skills recommendation",
            "Workspace preview and confirmation",
            "Initial track handoff",
        ],
        "audit": {
            "workspace_kind": detect_workspace_kind(conductor_dir),
            "project_maturity": maturity,
            "maturity_reasons": reasons,
            "git_uncommitted_changes": git_has_uncommitted_changes(repo),
            "existing_artifacts": artifacts,
            "resume": resume,
        },
        "checkpoints": checkpoints,
        "drafts": drafts,
        "styleguides": {"available": styleguides, "recommended": recommended_styleguides},
        "session": session_blueprint(repo, "setup"),
    }
    return flow


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    skill_root = Path(__file__).resolve().parents[1]
    print(json.dumps(build_setup_flow(repo, skill_root), indent=2))


if __name__ == "__main__":
    main()
