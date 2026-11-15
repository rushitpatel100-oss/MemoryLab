"""Mock-only tests of separate, versioned human adjudication."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.review_eval_cases import (
    load_cases, empty_review, lock_review, record_label, save_review,
)
from scripts.review_second import (
    FIELDS, add_assessment, lock_second, new_review,
)
from scripts.compare_human_reviews import build_comparison
from scripts.adjudicate_reviews import (
    new_adjudication, load_adjudication, record_final,
    lock_adjudication, build_final_summary, adjudicate_interactive,
)


class AdjudicationTests(unittest.TestCase):
    def setUp(self):
        self.cases, self.digest = load_cases()
        self.first = empty_review(self.digest)
        self.second = new_review(self.digest)
        for case in self.cases:
            record_label(self.first, case["id"], "C", "Compatible facts")
            add_assessment(
                self.second, case["id"], "C", "Compatible facts",
                {field: "U" for field, _ in FIELDS}, "K"
            )
        lock_review(self.first, self.cases)
        lock_second(self.second, self.cases)
        self.rows, self.summary = build_comparison(
            self.cases, self.first, self.second
        )
        self.queue = [r for r in self.rows if r["adjudicate"]]

    def create(self):
        return new_adjudication(
            self.digest, self.first, self.second, self.queue
        )

    def record_all(self, review):
        for row in self.queue:
            record_final(
                review, row["id"], "U", "Need independent context",
                {field: "U" for field, _ in FIELDS}, "R"
            )

    def test_all_agreed_but_pre_registered_cases_still_reviewed(self):
        self.assertEqual(len(self.queue), 7)
        self.assertIn("B04", [row["id"] for row in self.queue])

    def test_incomplete_adjudication_cannot_lock(self):
        review = self.create()
        with self.assertRaisesRegex(ValueError, "Finish every flagged"):
            lock_adjudication(review)

    def test_adjudicated_and_unexamined_agreements_are_separate(self):
        review = self.create()
        self.record_all(review)
        lock_adjudication(review)
        summary = build_final_summary(self.rows, review)
        b04 = next(x for x in summary if x["id"] == "B04")
        b01 = next(x for x in summary if x["id"] == "B01")
        self.assertEqual(b04["status"], "adjudicated")
        self.assertEqual(b04["final_label"], "uncertain")
        self.assertEqual(b01["status"], "agreed_not_adjudicated")
        self.assertEqual(b01["final_label"], "coexists")
        self.assertEqual(b01["first_label"], "coexists")

    def test_deferred_case_keeps_no_final_label(self):
        review = self.create()
        self.record_all(review)
        record_final(
            review, "B04", "X", "Need more context",
            {field: "U" for field, _ in FIELDS}, "R"
        )
        lock_adjudication(review)
        summary = build_final_summary(self.rows, review)
        b04 = next(x for x in summary if x["id"] == "B04")
        self.assertIsNone(b04["final_label"])
        self.assertEqual(b04["status"], "deferred")

    def test_locked_data_rejects_mutations(self):
        review = self.create()
        self.record_all(review)
        lock_adjudication(review)
        with self.assertRaisesRegex(ValueError, "locked"):
            record_final(
                review, "B04", "D", "Same fact",
                {field: "Y" for field, _ in FIELDS}, "D"
            )

    def test_detect_tampering_or_changed_rater_file(self):
        with tempfile.TemporaryDirectory() as dirname:
            path = Path(dirname) / "adjudication.json"
            review = self.create()
            self.record_all(review)
            lock_adjudication(review)
            save_review(review, path)
            amended_second = copy.deepcopy(self.second)
            amended_second["answers_sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "evidence changed"):
                load_adjudication(
                    path, self.digest, self.first, amended_second, self.queue
                )
            raw = json.loads(path.read_text(encoding="utf-8"))
            raw["answers"]["B04"]["reason"] = "Changed!"
            path.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "was edited"):
                load_adjudication(
                    path, self.digest, self.first, self.second, self.queue
                )

    def test_interactive_records_one_and_resumes(self):
        review = self.create()
        saved = []
        answers = iter(["D", "Paraphrase", "Y", "Y", "N", "N", "D"])
        written = adjudicate_interactive(
            self.rows, review, limit=1,
            input_fn=lambda _: next(answers),
            output_fn=lambda _: None,
            save_fn=lambda x: saved.append(copy.deepcopy(x)),
        )
        self.assertEqual(written, 1)
        self.assertEqual(len(saved), 1)
        self.assertEqual(len(review["answers"]), 1)


if __name__ == "__main__":
    unittest.main()
