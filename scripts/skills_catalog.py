from __future__ import annotations

import json
import re
from pathlib import Path

from conductor_fs import read_text


GENERIC_KEYWORDS = {"setup", "deployment", "architectural design", "pipeline design", "database", "auth"}


def load_catalog(path: Path) -> list[dict]:
    items: list[dict] = []
    current: dict | None = None
    for line in read_text(path).splitlines():
        heading = re.match(r"^###\s+(.+)$", line)
        if heading:
            if current:
                items.append(current)
            current = {"name": heading.group(1), "dependencies": [], "keywords": []}
            continue
        if current is None:
            continue
        desc = re.match(r"^- \*\*Description\*\*: (.+)$", line)
        if desc:
            current["description"] = desc.group(1)
            continue
        url = re.match(r"^- \*\*URL\*\*: (.+)$", line)
        if url:
            current["url"] = url.group(1)
            continue
        party = re.match(r"^- \*\*Party\*\*: (.+)$", line)
        if party:
            current["party"] = party.group(1)
            continue
        dep = re.match(r"^\s+- \*\*Dependencies\*\*: `(.+)`$", line)
        if dep:
            current["dependencies"].extend([item.strip() for item in dep.group(1).split("`, `")])
            continue
        kw = re.match(r"^\s+- \*\*Keywords\*\*: (.+)$", line)
        if kw:
            current["keywords"].extend([item.strip(" `") for item in kw.group(1).split(",")])
            continue
    if current:
        items.append(current)
    return items


def recommend_skills(catalog_path: Path, context: str) -> list[dict]:
    context_lower = context.lower()
    recommendations = []
    for item in load_catalog(catalog_path):
        score = 0
        for dependency in item.get("dependencies", []):
            if dependency.lower() in context_lower:
                score += 2
        for keyword in item.get("keywords", []):
            normalized = keyword.lower()
            if normalized in GENERIC_KEYWORDS:
                continue
            if normalized in context_lower:
                score += 1
        if score > 0:
            enriched = dict(item)
            enriched["score"] = score
            recommendations.append(enriched)
    recommendations.sort(key=lambda item: (-item["score"], item["name"]))
    return recommendations


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--context", required=True)
    args = parser.parse_args()
    print(json.dumps(recommend_skills(Path(args.catalog), args.context), indent=2))
