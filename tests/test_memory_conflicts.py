"""No-network unit tests for the smart memory review prototype."""
import io
import json
import os
import sqlite3
import tempfile
from contextlib import closing
import unittest
from unittest.mock import patch

from memory_conflicts import classify_pair
from memory_store import save_reviewed_memory


class ConflictProposalTests(unittest.TestCase):
    OLD = {"topic": "location", "fact": "I live in Bristol."}

    @patch("memory_conflicts.urllib.request.urlopen")
    def test_valid_replacement(self, mocked):
        mocked.return_value = io.BytesIO(json.dumps({
            "message": {"content": json.dumps({
                "relation": "replaces", "reason": "A move was stated."
            })}
        }).encode())
        result = classify_pair(self.OLD, "location", "I moved to York.")
        self.assertEqual(result["relation"], "replaces")
        mocked.assert_called_once()

    @patch("memory_conflicts.urllib.request.urlopen")
    def test_invalid_reply_is_uncertain(self, mocked):
        mocked.return_value = io.BytesIO(
            b'{"message":{"content":"not-json"}}'
        )
        result = classify_pair(self.OLD, "location", "I work in London.")
        self.assertEqual(result["relation"], "uncertain")


class SafeStorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "test.db")
        with closing(sqlite3.connect(self.db)) as conn, conn:
            conn.execute(
                "CREATE TABLE memories ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "topic TEXT NOT NULL, fact TEXT NOT NULL, "
                "created_at TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1)"
            )
            conn.execute(
                "INSERT INTO memories(topic,fact,created_at) "
                "VALUES('location','I live in Bristol.','t0')"
            )

    def tearDown(self):
        self.tmp.cleanup()

    def flags(self):
        with closing(sqlite3.connect(self.db)) as conn:
            return [r[0] for r in conn.execute(
                "SELECT active FROM memories ORDER BY id"
            )]

    def test_keep_both(self):
        save_reviewed_memory(
            "location", "I work in London.", {1: "keep"}, [1], self.db
        )
        self.assertEqual(self.flags(), [1, 1])

    def test_supersede_one(self):
        save_reviewed_memory(
            "location", "I moved to York.", {1: "supersede"}, [1], self.db
        )
        self.assertEqual(self.flags(), [0, 1])

    def test_stale_review_is_rejected(self):
        before = self.flags()
        with self.assertRaises(ValueError):
            save_reviewed_memory(
                "location", "I moved to York.", {}, [], self.db
            )
        self.assertEqual(self.flags(), before)

    def test_missing_review_decision_is_rejected(self):
        with self.assertRaises(ValueError):
            save_reviewed_memory(
                "location", "I moved to York.", {}, [1], self.db
            )
        self.assertEqual(self.flags(), [1])

    def test_unseen_topic_can_be_added(self):
        mid = save_reviewed_memory(
            "hobby", "Photography.", {}, [], self.db
        )
        self.assertEqual(mid, 2)


if __name__ == "__main__":
    unittest.main()
