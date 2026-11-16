"""No-network tests of the V3/V4 AI-only comparator."""
import copy
import unittest

from scripts.compare_v3_v4 import compare, markdown
from scripts.review_holdout_v2 import load_local_cases


class V4DiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.cases, self.digest = load_local_cases()
        self.v3 = {
            "dataset_sha256": self.digest,
            "reviewer_type": "automated_llm_not_human",
            "independent_ground_truth": False,
            "policy_version": "evidence_first_v3",
            "answers": {
                c["id"]: {
                    "provisional_label": "uncertain",
                    "triage": "needs_review"
                } for c in self.cases
            },
        }
        self.v4 = copy.deepcopy(self.v3)
        self.v4["policy_version"] = "contrastive_evidence_v4"
        for row in self.v4["answers"].values():
            row["axes"] = {
                "same_entity": "yes", "same_attribute": "yes",
                "same_assertion": "no",
                "old_fact_known_obsolete": "no",
                "new_value_known": "no",
            }
            row["raw_model_response"] = '{"axes":{}}'

    def test_descriptive_changes_not_accuracy(self):
        self.v4["answers"]["H01"]["provisional_label"] = "coexists"
        result = compare(self.cases, self.digest, self.v3, self.v4)
        self.assertEqual(result["label_changes"], 1)
        self.assertEqual(result["v3"]["uncertain"], 24)
        self.assertEqual(result["v4"]["coexists"], 1)
        self.assertEqual(result["v4_raw_response_saved"], 24)
        self.assertIn("not accuracy", markdown(result, "a", "b"))

    def test_reject_wrong_dataset(self):
        self.v4["dataset_sha256"] = "x"
        with self.assertRaisesRegex(ValueError, "mismatch"):
            compare(self.cases, self.digest, self.v3, self.v4)

    def test_reject_human_provenance_in_ai_report(self):
        self.v4["reviewer_type"] = "human"
        with self.assertRaisesRegex(ValueError, "mismatch"):
            compare(self.cases, self.digest, self.v3, self.v4)

    def test_reject_missing_case(self):
        del self.v4["answers"]["H22"]
        with self.assertRaisesRegex(ValueError, "all cases"):
            compare(self.cases, self.digest, self.v3, self.v4)

    def test_does_not_mutate_either_report(self):
        old = copy.deepcopy(self.v3)
        new = copy.deepcopy(self.v4)
        compare(self.cases, self.digest, self.v3, self.v4)
        self.assertEqual(old, self.v3)
        self.assertEqual(new, self.v4)


if __name__ == "__main__":
    unittest.main()
