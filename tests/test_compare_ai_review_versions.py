"""No-inference tests for Phase 9 review method comparison."""
import copy
import unittest

from scripts.compare_ai_review_versions import compare, markdown
from scripts.review_holdout_v2 import load_local_cases


class VersionComparisonTests(unittest.TestCase):
    def setUp(self):
        self.cases, self.digest = load_local_cases()
        self.old = {
            "dataset_sha256": self.digest,
            "reviewer_type": "automated_llm_not_human",
            "independent_ground_truth": False,
            "answers": {
                c["id"]: {"provisional_label": "replaces",
                          "triage": "needs_review"}
                for c in self.cases
            },
        }
        self.new = copy.deepcopy(self.old)
        self.new["policy_version"] = "evidence_first_v3"

    def test_label_change_is_diagnostic_not_accuracy(self):
        self.new["answers"]["H01"]["provisional_label"] = "coexists"
        result = compare(self.cases, self.digest, self.old, self.new)
        self.assertEqual(result["changed_relations"], 1)
        self.assertEqual(result["phase8_distribution"]["replaces"], 24)
        self.assertEqual(result["phase9_distribution"]["coexists"], 1)
        self.assertIn("not proof", result["interpretation"])
        content = markdown(result, "0" * 64, "f" * 64)
        self.assertIn("not accuracy", content)
        self.assertIn("H01", content)

    def test_dataset_mismatch_fails_closed(self):
        self.new["dataset_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "fingerprint mismatch"):
            compare(self.cases, self.digest, self.old, self.new)

    def test_incomplete_model_file_fails(self):
        del self.old["answers"]["H24"]
        with self.assertRaisesRegex(ValueError, "all cases"):
            compare(self.cases, self.digest, self.old, self.new)

    def test_human_label_falsification_fails(self):
        self.old["reviewer_type"] = "human"
        with self.assertRaisesRegex(ValueError, "not an AI draft"):
            compare(self.cases, self.digest, self.old, self.new)

    def test_new_version_requires_evidence_first_policy(self):
        del self.new["policy_version"]
        with self.assertRaisesRegex(ValueError, "V3"):
            compare(self.cases, self.digest, self.old, self.new)

    def test_does_not_mutate_inputs(self):
        original_old, original_new = copy.deepcopy(self.old), copy.deepcopy(self.new)
        compare(self.cases, self.digest, self.old, self.new)
        self.assertEqual(self.old, original_old)
        self.assertEqual(self.new, original_new)


if __name__ == "__main__":
    unittest.main()
