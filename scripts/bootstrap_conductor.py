from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from conductor_fs import (
    detect_styleguide_names,
    infer_product_name,
    infer_solution_file,
    infer_source_roots,
    infer_tech_stack,
    load_styleguide,
    load_template,
    refresh_portfolio_indexes,
    render_portfolio_indexes,
    reset_generated_structure,
    write_text,
)


def render_shared_context(repo: Path, template_base: Path) -> dict[str, str]:
    replacements = {
        "{{PRODUCT_NAME}}": infer_product_name(repo),
        "{{SOLUTION_FILE}}": infer_solution_file(repo),
        "{{SOURCE_ROOTS}}": infer_source_roots(repo),
        "{{TECH_STACK}}": infer_tech_stack(repo),
    }

    shared_files = {
        "README.md": "README.md.tmpl",
        "workflow.md": "workflow.md.tmpl",
        "product.md": "product.md.tmpl",
        "product-guidelines.md": "product-guidelines.md.tmpl",
        "tech-stack.md": "tech-stack.md.tmpl",
        "code_styleguides/README.md": "code_styleguides_README.md.tmpl",
    }

    rendered: dict[str, str] = {}
    for relative_target, template_name in shared_files.items():
        content = load_template(template_base, template_name)
        for source, target in replacements.items():
            content = content.replace(source, target)
        rendered[relative_target] = content.rstrip() + "\n"

    for styleguide_name in detect_styleguide_names(repo):
        rendered[f"code_styleguides/{styleguide_name}"] = load_styleguide(template_base, styleguide_name).rstrip() + "\n"

    rendered["archive/.gitkeep"] = ""
    return rendered


def ensure_shared_context(repo: Path, template_base: Path) -> None:
    conductor_dir = repo / "conductor"
    conductor_dir.mkdir(parents=True, exist_ok=True)
    (conductor_dir / "archive").mkdir(parents=True, exist_ok=True)
    (conductor_dir / "code_styleguides").mkdir(parents=True, exist_ok=True)
    (conductor_dir / "tracks").mkdir(parents=True, exist_ok=True)

    reset_generated_structure(conductor_dir)

    # Rebuild selected styleguides from the skill library on each setup refresh.
    styleguide_dir = conductor_dir / "code_styleguides"
    if styleguide_dir.exists():
        shutil.rmtree(styleguide_dir)
    styleguide_dir.mkdir(parents=True, exist_ok=True)

    for relative_target, content in render_shared_context(repo, template_base).items():
        write_text(conductor_dir / relative_target, content)

    refresh_portfolio_indexes(conductor_dir, template_base)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    template_base = Path(__file__).resolve().parents[1]
    conductor_dir = repo / "conductor"

    if args.preview:
        rendered = render_shared_context(repo, template_base)
        preview = {
            "repo": str(repo),
            "conductor_exists": conductor_dir.exists(),
            "files": sorted([*rendered.keys(), *render_portfolio_indexes(conductor_dir, template_base).keys()]),
            "styleguides": detect_styleguide_names(repo),
            "context": {
                "product_name": infer_product_name(repo),
                "solution_file": infer_solution_file(repo),
                "source_roots": infer_source_roots(repo),
            },
        }
        print(json.dumps(preview, indent=2))
        return

    ensure_shared_context(repo, template_base)
    print(f"Bootstrapped conductor workspace in {repo / 'conductor'}")


if __name__ == "__main__":
    main()
