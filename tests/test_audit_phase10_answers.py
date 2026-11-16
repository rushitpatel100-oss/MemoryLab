"""Offline tests for Phase 10 raw-answer audit; no Qwen/SQLite writes."""
import copy
import unittest

from scripts.audit_phase10_answers import audit_run, markdown, triage
from scripts.evaluate_downstream_memory import load_dataset


class Phase10AnswerAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset, cls.digest = load_dataset()

    def test_expected_abstention_but_specific_answer_is_flagged(self):
        row = {
            "answer": "It changed to Monday.",
            "expect_abstention": True,
            "text_proxy_pass": False,
            "support_available": None,
            "support_retrieved": None,
        }
        self.assertEqual(triage(row), "unexpected_specific_answer")

    def test_abstention_detected_is_not_claimed_verified(self):
        row = {
            "answer": "I don't have enough information to know.",
            "expect_abstention": True,
            "text_proxy_pass": True,
            "support_available": None,
            "support_retrieved": None,
        }
        self.assertEqual(triage(row), "expected_abstention_detected")

    def test_missing_keyword_with_evidence_is_not_assumed_wrong(self):
        row = {
            "answer": "The blue one.",
            "expect_abstention": False,
            "text_proxy_pass": False,
            "support_available": True,
            "support_retrieved": True,
        }
        self.assertEqual(triage(row), "wording_mismatch_needs_review")

    def test_storage_loss_has_priority_over_wording(self):
        row = {
            "answer": "The new venue is not established.",
            "expect_abstention": False,
            "text_proxy_pass": False,
            "support_available": False,
            "support_retrieved": False,
        }
        self.assertEqual(triage(row), "storage_support_missing")

    def test_retrieval_miss_has_priority_over_keyword_mismatch(self):
        row = {
            "answer": "No information available.",
            "expect_abstention": False,
            "text_proxy_pass": False,
            "support_available": True,
            "support_retrieved": False,
        }
        self.assertEqual(triage(row), "retrieval_support_missing")

    def test_keyword_match_is_not_truth_verification(self):
        row = {
            "answer": "The venue is Quartz Wing.",
            "expect_abstention": False,
            "text_proxy_pass": True,
            "support_available": True,
            "support_retrieved": True,
        }
        self.assertEqual(triage(row), "lexical_match_unverified")

    def test_cannot_audit_changed_dataset_or_oracle_expectation(self):
        self.assertRaisesRegex(
            ValueError, "matching Phase 10",
            audit_run, {"dataset_sha256": "wrong"}, self.dataset, self.digest
        )

    def test_complete_mock_run_distinguishes_causes(self):
        data = {
            "version": 1,
            "method": "project_authored_semantic_development_not_accuracy",
            "dataset_sha256": self.digest,
            "policy": "reviewed", "embedding": "all-minilm",
            "top_k": 3, "minimum": 0.25,
            "results": {},
        }
        for case in self.dataset["scenarios"]:
            checks = []
            for c in case["checks"]:
                checks.append({
                    "id": c["id"], "question": c["question"],
                    "expected_phrases": c.get("expected_phrases", []),
                    "expect_abstention": c.get("expect_abstention", False),
                    "support_steps": c["support_steps"],
                    "support_available": None if c.get("expect_abstention") else True,
                    "support_retrieved": None if c.get("expect_abstention") else True,
                    "text_proxy_pass": True, "answer": "placeholder",
                })
            data["results"][case["id"] + "_reviewed"] = {
                "scenario": case["id"], "policy": "reviewed",
                "expected_active_steps": case["expected_active"],
                "checks": checks, "exact_active_state": True,
            }
        q = data["results"]["P07_reviewed"]["checks"][1]
        q["text_proxy_pass"] = False
        q["answer"] = "Monday."
        q = data["results"]["P04_reviewed"]["checks"][0]
        q["text_proxy_pass"] = False
        q["answer"] = "The blue one."
        report = audit_run(data, self.dataset, self.digest)
        self.assertEqual(report["scenarios"], 14)
        self.assertEqual(report["questions"], 28)
        self.assertEqual(report["counts"]["unexpected_specific_answer"], 1)
        self.assertEqual(report["counts"]["wording_mismatch_needs_review"], 1)
        content = markdown(report, "x" * 64)
        self.assertIn("NOT independent human accuracy", content)
        self.assertIn("P07 / Q2", content)
        self.assertIn("P04 / Q1", content)

    def test_fail_on_incomplete_scenario_set(self):
        with self.assertRaisesRegex(ValueError, "complete, matching"):
            audit_run({
                "version": 1,
                "method": "project_authored_semantic_development_not_accuracy",
                "dataset_sha256": self.digest,
                "policy": "reviewed", "embedding": "all-minilm",
                "top_k": 3, "minimum": 0.25, "results": {},
            }, self.dataset, self.digest)


if __name__ == "__main__":
    unittest.main()
