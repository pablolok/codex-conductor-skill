from __future__ import annotations

import argparse
import json
from pathlib import Path

from conductor_fs import (
    detect_styleguide_names,
    detect_workspace_kind,
    infer_product_name,
    infer_solution_file,
    infer_source_roots,
    infer_tech_stack,
    read_text,
)
from skills_catalog import recommend_skills


def detect_project_maturity(repo: Path) -> tuple[str, list[str]]:
    reasons: list[str] = []
    for manifest in ("package.json", "pom.xml", "requirements.txt", "go.mod", "Cargo.toml"):
        if (repo / manifest).exists():
            reasons.append(f"found {manifest}")
    for directory in ("src", "app", "lib", "bin"):
        path = repo / directory
        if path.exists() and any(child.is_file() for child in path.rglob("*")):
            reasons.append(f"found source files under {directory}/")
    return ("brownfield", reasons) if reasons else ("greenfield", ["no dependency manifests or source roots found"])


def audit_existing_artifacts(conductor_dir: Path) -> dict[str, bool]:
    return {
        "product": (conductor_dir / "product.md").exists(),
        "product_guidelines": (conductor_dir / "product-guidelines.md").exists(),
        "tech_stack": (conductor_dir / "tech-stack.md").exists(),
        "workflow": (conductor_dir / "workflow.md").exists(),
        "index": (conductor_dir / "index.md").exists(),
        "tracks_dir": (conductor_dir / "tracks").exists(),
    }


def determine_resume_target(artifacts: dict[str, bool], conductor_dir: Path) -> dict[str, str]:
    tracks_root = conductor_dir / "tracks"
    has_complete_track = False
    if tracks_root.exists():
        for child in tracks_root.iterdir():
            if not child.is_dir():
                continue
            if all((child / name).exists() for name in ("spec.md", "plan.md", "metadata.json", "index.md")):
                has_complete_track = True
                break
    if has_complete_track:
        return {"target_section": "HALT", "announcement": "The project is already initialized. Use conductor:newTrack or conductor:implement."}
    if artifacts["index"]:
        return {"target_section": "3.0", "announcement": "Resuming setup: shared context is complete. Next: generate or refine the first track."}
    if artifacts["workflow"]:
        return {"target_section": "2.6", "announcement": "Resuming setup: workflow is defined. Next: select agent skills."}
    if artifacts["tech_stack"]:
        return {"target_section": "2.5", "announcement": "Resuming setup: tech stack is defined. Next: define workflow and skills."}
    if artifacts["product_guidelines"]:
        return {"target_section": "2.3", "announcement": "Resuming setup: product guidelines are complete. Next: define the technology stack."}
    if artifacts["product"]:
        return {"target_section": "2.2", "announcement": "Resuming setup: product definition is complete. Next: create product guidelines."}
    return {"target_section": "2.0", "announcement": "Starting setup from project discovery."}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    conductor_dir = repo / "conductor"
    maturity, reasons = detect_project_maturity(repo)
    context = "\n".join(
        [
            read_text(repo / "README.md"),
            read_text(repo / "AGENTS.md"),
            read_text(conductor_dir / "tech-stack.md"),
            read_text(conductor_dir / "workflow.md"),
        ]
    )
    catalog_path = Path(__file__).resolve().parents[1] / "skills" / "catalog.md"
    output = {
        "workspace_kind": detect_workspace_kind(conductor_dir),
        "project_maturity": maturity,
        "maturity_reasons": reasons,
        "existing_artifacts": audit_existing_artifacts(conductor_dir),
        "product_name": infer_product_name(repo),
        "solution_file": infer_solution_file(repo),
        "source_roots": infer_source_roots(repo),
        "tech_stack": infer_tech_stack(repo),
        "styleguides": detect_styleguide_names(repo),
        "recommended_skills": recommend_skills(catalog_path, context),
    }
    output["resume"] = determine_resume_target(output["existing_artifacts"], conductor_dir)
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
