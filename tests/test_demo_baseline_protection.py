"""Regression tests for demo-only transactional broad-save prevention.

Execute the actual save_memory() function via AST extraction so importing
Streamlit's entire interactive app is unnecessary. Use only a temporary,
fictional SQLite fixture. No real database path or model access.
"""
import ast
import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def baseline_function(database):
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    node = next(
        item for item in module.body
        if isinstance(item, ast.FunctionDef) and item.name == "save_memory"
    )
    namespace = {
        "connect": lambda: sqlite3.connect(database),
        "os": os,
        "closing": closing,
        "datetime": datetime,
        "timezone": timezone,
    }
    exec(compile(ast.Module(body=[node], type_ignores=[]), "app.py", "exec"),
         namespace)
    return namespace["save_memory"]


class DemoBaselineProtectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="memorylab_demo_guard_test_")
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "fictional.sqlite3"
        with closing(sqlite3.connect(self.db)) as conn, conn:
            conn.execute(
                "CREATE TABLE memories("
                "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "topic TEXT NOT NULL, fact TEXT NOT NULL,"
                "created_at TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1)"
            )
        self.save = baseline_function(self.db)

    def rows(self):
        with closing(sqlite3.connect(self.db)) as conn:
            return conn.execute(
                "SELECT topic, fact, active FROM memories ORDER BY id"
            ).fetchall()

    def test_first_demo_memory_is_allowed(self):
        with patch.dict(os.environ, {"MEMORYLAB_DEMO_MODE": "1"}):
            self.assertTrue(self.save("orchid-demo", "Maple Room."))
        self.assertEqual(self.rows(), [("orchid-demo", "Maple Room.", 1)])

    def test_existing_demo_topic_cannot_be_bulk_superseded(self):
        with patch.dict(os.environ, {"MEMORYLAB_DEMO_MODE": "1"}):
            self.assertTrue(self.save("orchid-demo", "Maple Room."))
            self.assertFalse(self.save("orchid-demo", "Front desk."))
        self.assertEqual(self.rows(), [("orchid-demo", "Maple Room.", 1)])

    def test_demo_guard_normalizes_topic_before_checking(self):
        with patch.dict(os.environ, {"MEMORYLAB_DEMO_MODE": "1"}):
            self.assertTrue(self.save("Orchid-Demo", "Maple Room."))
            self.assertFalse(self.save(" orchid-DEMO ", "Front desk."))
        self.assertEqual(self.rows(), [("orchid-demo", "Maple Room.", 1)])

    def test_new_topic_still_works_in_demo(self):
        with patch.dict(os.environ, {"MEMORYLAB_DEMO_MODE": "1"}):
            self.assertTrue(self.save("orchid-demo", "Maple Room."))
            self.assertTrue(self.save("other-demo", "A different fact."))
        self.assertEqual(len(self.rows()), 2)
        self.assertTrue(all(row[2] == 1 for row in self.rows()))

    def test_normal_research_baseline_behavior_remains_available(self):
        with patch.dict(os.environ, {"MEMORYLAB_DEMO_MODE": "0"}):
            self.assertTrue(self.save("orchid-demo", "Maple Room."))
            self.assertTrue(self.save("orchid-demo", "Front desk."))
        self.assertEqual(
            self.rows(),
            [("orchid-demo", "Maple Room.", 0),
             ("orchid-demo", "Front desk.", 1)],
        )

    def test_demo_button_is_disabled_despite_acknowledgement(self):
        source = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn("demo_bulk_overwrite_blocked =", source)
        self.assertIn("or demo_bulk_overwrite_blocked,", source)
        self.assertIn("ISOLATED DEMO SAFEGUARD", source)


if __name__ == "__main__":
    unittest.main()
