"""Offline tests for AI-first human verification and provenance."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.review_signoff import (
    approve_one, approve_unflagged, draft_decision, empty_signoff,
    load_ai_drafts, load_signoff, markdown_report, review_stats,
    save_signoff, write_report,
)
from scripts.review_holdout_v2 import load_local_cases


class HumanSignoffTests(unittest.TestCase):
    def setUp(self):
        self.cases, self.digest = load_local_cases()
        self.sample = {
            "provisional_label": "coexists",
            "reason": "The two statements describe different properties.",
            "axes": {"same_entity": "yes", "same_attribute": "no",
                     "old_fact_known_obsolete": "no", "new_value_known": "yes"},
            "model_storage_action": "keep_both",
            "reviewer_type": "automated_llm_not_human",
            "triage": "draft", "flags": [],
        }
        self.ai = {
            "dataset_sha256": self.digest,
            "reviewer_type": "automated_llm_not_human",
            "independent_ground_truth": False,
            "judge_model": "qwen2.5:1.5b",
            "answers": {
                c["id"]: copy.deepcopy(self.sample) for c in self.cases
            },
        }
        self.state = empty_signoff(self.digest, "a" * 64, "qwen2.5:1.5b")

    def test_refuses_incomplete_auto_report(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "ai.json"
            del self.ai["answers"]["H01"]
            path.write_text(json.dumps(self.ai), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Finish AI triage"):
                load_ai_drafts(path, self.cases, self.digest)

    def test_requires_ai_provenance(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "ai.json"
            self.ai["reviewer_type"] = "human"
            path.write_text(json.dumps(self.ai), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Invalid AI provenance"):
                load_ai_drafts(path, self.cases, self.digest)

    def test_approval_and_human_correction_recorded(self):
        approve_one(self.state, "H01", draft_decision(self.sample), self.sample)
        self.assertEqual(self.state["decisions"]["H01"]["method"], "individual")
        changed = draft_decision(self.sample)
        changed.update({"label": "uncertain", "reason": "Subject unclear",
                        "storage_action": "review_needed"})
        approve_one(self.state, "H01", changed, self.sample)
        self.assertEqual(self.state["decisions"]["H01"]["method"], "corrected")
        self.assertEqual(len(self.state["audit"]), 2)

    def test_bulk_requires_confirmation_and_skips_flagged(self):
        self.ai["answers"]["H02"]["triage"] = "needs_review"
        with self.assertRaisesRegex(ValueError, "attest"):
            approve_unflagged(self.state, self.ai, ["H01"], attested=False)
        count = approve_unflagged(
            self.state, self.ai, ["H01", "H02"], attested=True
        )
        self.assertEqual(count, 1)
        self.assertNotIn("H02", self.state["decisions"])
        self.assertEqual(self.state["decisions"]["H01"]["method"], "bulk_attested")

    def test_signoff_cannot_rebase_to_changed_source(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "signoff.json"
            save_signoff(self.state, path)
            with self.assertRaisesRegex(ValueError, "AI source or dataset changed"):
                load_signoff(path, self.digest, "b" * 64, "qwen2.5:1.5b",
                             {c["id"] for c in self.cases})

    def test_final_report_requires_full_signoff(self):
        with self.assertRaisesRegex(ValueError, "Every case"):
            markdown_report(self.cases, self.ai, self.state)

    def test_report_preserves_provenance_and_is_versioned(self):
        approve_unflagged(
            self.state, self.ai, [c["id"] for c in self.cases], attested=True
        )
        changed = draft_decision(self.sample)
        changed.update({"label": "uncertain", "reason": "Attribute unclear",
                        "storage_action": "review_needed"})
        approve_one(self.state, "H02", changed, self.sample)
        result = markdown_report(self.cases, self.ai, self.state)
        self.assertIn("not independent human annotation", result.lower())
        self.assertIn("Bulk-attested: 23", result)
        self.assertIn("Human-corrected: 1", result)
        self.assertEqual(review_stats(self.state, self.cases)["remaining"], 0)
        with tempfile.TemporaryDirectory() as folder:
            path = write_report(self.cases, self.ai, self.state, folder)
            self.assertTrue(path.is_file())
            self.assertIn("human_reviewed", path.name)


if __name__ == "__main__":
    unittest.main()
