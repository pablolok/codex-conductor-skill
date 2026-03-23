from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from skills_catalog import installed_skill_names, partition_recommended_skills  # noqa: E402


class SkillsCatalogTests(unittest.TestCase):
    def test_installed_skill_names_reads_repo_local_gemini_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".gemini" / "skills" / "skill-a").mkdir(parents=True)
            (repo / ".gemini" / "skills" / "skill-b").mkdir(parents=True)

            installed = installed_skill_names(repo)

            self.assertEqual(installed, {"skill-a", "skill-b"})

    def test_partition_recommended_skills_splits_installed_and_missing(self) -> None:
        recommendations = [
            {"name": "skill-a", "score": 3},
            {"name": "skill-b", "score": 2},
        ]

        partitioned = partition_recommended_skills(recommendations, {"skill-a"})

        self.assertEqual([item["name"] for item in partitioned["installed"]], ["skill-a"])
        self.assertEqual([item["name"] for item in partitioned["missing"]], ["skill-b"])


if __name__ == "__main__":
    unittest.main()
