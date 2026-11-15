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
    def test_coexistence_example_in_prompt_and_request(self, mocked):
        # Mocked model output: verifies prompt/examples, not Qwen accuracy.
        mocked.return_value = io.BytesIO(json.dumps({
            "message": {"content": json.dumps({
                "relation": "coexists",
                "reason": "Home and work locations can be different."
            })}
        }).encode())
        result = classify_pair(
            {"topic": "test_location",
             "fact": "I have moved from Bristol to York."},
            "test_location", "I work in London."
        )
        self.assertEqual(result["relation"], "coexists")
        request = mocked.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        instructions = payload["messages"][0]["content"]
        self.assertIn("Do NOT choose uncertain", instructions)
        # Assert the rule, not exact punctuation in a prompt example.
        self.assertIn("=> coexists", instructions)
        self.assertIn("I work in London", instructions)
        # The actual old and new facts must be passed in the user payload.
        supplied_facts = payload["messages"][1]["content"]
        self.assertIn("I work in London.", supplied_facts)
        self.assertIn("I have moved from Bristol to York.", supplied_facts)
        self.assertEqual(payload["options"]["temperature"], 0)

    @patch("memory_conflicts.urllib.request.urlopen")
    def test_exact_duplicate_skips_qwen(self, mocked):
        result = classify_pair(
            {"topic": "test_location", "fact": "I work in London."},
            " TEST_LOCATION ", "  i WORK in   london!  "
        )
        self.assertEqual(result["relation"], "duplicate")
        self.assertEqual(result["source"], "local_rule")
        mocked.assert_not_called()

    @patch("memory_conflicts.urllib.request.urlopen")
    def test_paraphrase_duplicate_label_is_accepted(self, mocked):
        mocked.return_value = io.BytesIO(json.dumps({
            "message": {"content": json.dumps({
                "relation": "duplicate",
                "reason": "They express the same job location."
            })}
        }).encode())
        result = classify_pair(
            {"topic": "job", "fact": "I work in London."},
            "job", "My job is in London."
        )
        self.assertEqual(result["relation"], "duplicate")
        self.assertEqual(result["source"], "qwen")
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

    def test_duplicate_is_blocked_and_keeps_original_active(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            save_reviewed_memory(
                "location", "  I  LIVE in bristol! ",
                {1: "supersede"}, [1], self.db
            )
        self.assertEqual(self.flags(), [1])

    def test_duplicate_check_runs_before_other_approved_updates(self):
        save_reviewed_memory(
            "location", "I work in London.", {1: "keep"}, [1], self.db
        )
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            save_reviewed_memory(
                "location", " i WORK in london! ",
                {1: "supersede", 2: "keep"}, [1, 2], self.db
            )
        self.assertEqual(self.flags(), [1, 1])

    def test_unseen_topic_can_be_added(self):
        mid = save_reviewed_memory(
            "hobby", "Photography.", {}, [], self.db
        )
        self.assertEqual(mid, 2)


if __name__ == "__main__":
    unittest.main()
