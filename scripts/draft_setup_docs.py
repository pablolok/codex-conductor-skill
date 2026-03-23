from __future__ import annotations

import argparse
import json
from pathlib import Path

from conductor_fs import infer_product_name, infer_solution_file, infer_source_roots, infer_tech_stack, read_text


def build_product(repo: Path) -> str:
    product_name = infer_product_name(repo)
    return "\n".join(
        [
            "# Product Context",
            "",
            "## Product",
            "",
            product_name,
            "",
            "## Primary Goal",
            "",
            f"Help users succeed with {product_name} using a clearly defined product direction.",
            "",
            "## Repository-Specific Context",
            "",
            f"- Solution file: `{infer_solution_file(repo)}`",
            f"- Source roots:",
            infer_source_roots(repo),
        ]
    )


def build_guidelines(repo: Path) -> str:
    return "\n".join(
        [
            "# Product Guidelines",
            "",
            "## Expectations",
            "",
            "- Preserve the current product direction and user intent of the repository.",
            "- Keep additions aligned with the repo's existing mission and workflow.",
            "- Keep Conductor artifacts concise, reviewable, and outcome-oriented.",
            "",
            "## Engineering Discipline",
            "",
            "- Treat `AGENTS.md` as binding for implementation and verification rules.",
            "- Favor deterministic verification and clear evidence in Conductor artifacts.",
            "",
            "## Repository Notes",
            "",
            "- Use `README.md` for user-facing overview.",
            "- Use `AGENTS.md` for engineering constraints and mandatory checks.",
        ]
    )


def build_tech_stack(repo: Path) -> str:
    return "\n".join(
        [
            "# Tech Stack",
            "",
            "## Runtime Stack",
            "",
            infer_tech_stack(repo),
            "",
            "## Repository Shape",
            "",
            infer_source_roots(repo),
            "",
            "## Notes",
            "",
            "- Refresh this file only when the real stack changes.",
        ]
    )


def build_workflow(repo: Path) -> str:
    existing = read_text(repo / "conductor" / "workflow.md")
    if existing:
        return existing
    return "\n".join(
        [
            "# Project Workflow",
            "",
            "## Guiding Principles",
            "",
            "1. The plan is the source of truth.",
            "2. Follow TDD where the repo workflow expects it.",
            "3. Verify coverage against the approved threshold.",
            "4. Use non-interactive commands where possible.",
            "",
            "## Commit Policy",
            "",
            "- Branch policy: ask per track whether to create or use a dedicated branch.",
            "- Commit policy: commit per phase unless a preserved workflow says otherwise.",
            "- Record task SHAs in `plan.md` when commits are created.",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    drafts = {
        "product.md": build_product(repo),
        "product-guidelines.md": build_guidelines(repo),
        "tech-stack.md": build_tech_stack(repo),
        "workflow.md": build_workflow(repo),
    }
    print(json.dumps(drafts, indent=2))


if __name__ == "__main__":
    main()
