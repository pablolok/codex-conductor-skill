from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from conversation_state import close_session, init_session, session_blueprint, update_session  # noqa: E402


class ConversationStateTests(unittest.TestCase):
    def test_session_roundtrip_persists_checkpoint_progress(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            session = init_session(repo, "setup")
            self.assertTrue(Path(session["path"]).exists())

            updated = update_session(Path(session["path"]), 2, "revise", "Need another draft")
            self.assertEqual(updated["current_checkpoint"], 2)
            self.assertEqual(updated["history"][-1]["decision"], "revise")

            closed = close_session(Path(session["path"]), "completed")
            self.assertEqual(closed["status"], "completed")

            stored = json.loads(Path(session["path"]).read_text(encoding="utf-8"))
            self.assertEqual(stored["status"], "completed")

    def test_session_blueprint_path_updates_active_session_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            blueprint = session_blueprint(repo, "setup")
            session = init_session(repo, "setup")

            updated = update_session(Path(blueprint["state_path"]), 1, "approve")
            self.assertEqual(updated["current_checkpoint"], 1)

            alias = json.loads(Path(blueprint["state_path"]).read_text(encoding="utf-8"))
            self.assertEqual(alias["active_session"], Path(session["path"]).name)


if __name__ == "__main__":
    unittest.main()
