from __future__ import annotations

import argparse
import json
from pathlib import Path

from conductor_fs import infer_track_type, load_template


def render_with(template_base: Path, metadata: dict[str, str], title: str) -> dict[str, str]:
    replacements = {
        "{{TRACK_ID}}": metadata["track_id"],
        "{{TRACK_TITLE}}": metadata["title"],
        "{{TRACK_STATUS}}": metadata["status"],
        "{{TRACK_PATH}}": metadata["path"],
        "{{TRACK_REQUEST}}": title,
        "{{TRACK_TYPE}}": metadata["type"],
    }
    outputs: dict[str, str] = {}
    for target, template_name in {"spec.md": "track_spec.md.tmpl", "plan.md": "track_plan.md.tmpl"}.items():
        content = load_template(template_base, template_name)
        for source, value in replacements.items():
            content = content.replace(source, value)
        outputs[target] = content.rstrip() + "\n"
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--track-id", required=True)
    parser.add_argument("--title", required=True)
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    template_base = Path(__file__).resolve().parents[1]
    metadata = {
        "track_id": args.track_id,
        "type": infer_track_type(args.title),
        "status": "new",
        "title": args.title,
        "path": f"conductor/tracks/{args.track_id}",
    }
    print(json.dumps(render_with(template_base, metadata, args.title), indent=2))


if __name__ == "__main__":
    main()
