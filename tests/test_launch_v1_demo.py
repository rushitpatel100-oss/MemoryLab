"""Isolated V1.0 Streamlit demo checks; launcher never reads live DB."""
import os
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts.launch_v1_demo import ROOT, launch


class IsolatedDemoTests(unittest.TestCase):
    def test_demo_uses_temporary_absolute_sqlite_path(self):
        snapshots = []
        def runner(command, *, env, cwd, check):
            database = Path(env["MEMORYLAB_DB_PATH"])
            snapshots.append(database)
            self.assertTrue(database.is_absolute())
            self.assertEqual(database.parent.exists(), True)
            self.assertNotEqual(database, ROOT / "memorylab.db")
            self.assertEqual(env["MEMORYLAB_DEMO_MODE"], "1")
            self.assertEqual(cwd, str(ROOT))
            self.assertIn(str(ROOT / "app.py"), command)
            self.assertIn("--server.port", command)
            return SimpleNamespace(returncode=0)
        self.assertEqual(launch(port=8502, runner=runner), 0)
        self.assertEqual(len(snapshots), 1)
        self.assertFalse(snapshots[0].parent.exists())

    def test_local_env_override_is_not_reused(self):
        def runner(command, *, env, cwd, check):
            self.assertNotEqual(env["MEMORYLAB_DB_PATH"], "custom_live.sqlite")
            self.assertEqual(env["MEMORYLAB_DEMO_MODE"], "1")
            return SimpleNamespace(returncode=0)
        with patch.dict(os.environ, {"MEMORYLAB_DB_PATH": "custom_live.sqlite"}):
            self.assertEqual(launch(runner=runner), 0)

    def test_launcher_returns_subprocess_failure(self):
        def runner(command, *, env, cwd, check):
            return SimpleNamespace(returncode=2)
        self.assertEqual(launch(runner=runner), 2)

    def test_keyboard_interrupt_is_friendly_and_cleans_up(self):
        folders = []
        def runner(command, *, env, cwd, check):
            folders.append(Path(env["MEMORYLAB_DB_PATH"]).parent)
            raise KeyboardInterrupt()
        self.assertEqual(launch(runner=runner), 0)
        self.assertFalse(folders[0].exists())

    def test_app_respects_demo_database_for_all_writes(self):
        src = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn('DB_NAME = os.environ.get("MEMORYLAB_DB_PATH", "memorylab.db")', src)
        self.assertIn("MEMORYLAB_DEMO_MODE", src)
        self.assertIn("db_path=DB_NAME,", src)
        self.assertIn("sqlite3.connect(DB_NAME)", src)

    def test_no_real_database_string_in_launcher(self):
        src = (ROOT / "scripts" / "launch_v1_demo.py").read_text(encoding="utf-8")
        self.assertIn("TemporaryDirectory(", src)
        self.assertIn("subprocess.run", src)
        self.assertNotIn("sqlite3.connect(", src)


if __name__ == "__main__":
    unittest.main()
