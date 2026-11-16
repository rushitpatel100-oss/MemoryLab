"""Phase 10 offline development tests; never calls Ollama or user DB."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from answer_generator import NO_MEMORY_ANSWER
from scripts.evaluate_downstream_memory import (
    POLICIES, load_dataset, load_result, make_report, phrase_present,
    run_all, run_scenario, score_text_answer, summarize,
)


class Phase10DownstreamTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset, cls.digest = load_dataset()
        cls.cases = {case["id"]: case for case in cls.dataset["scenarios"]}

    def test_fresh_cases_and_checks_present(self):
        self.assertEqual(len(self.cases), 14)
        self.assertEqual(
            sum(len(x["checks"]) for x in self.cases.values()), 28
        )
        self.assertNotIn("independent", self.dataset["authorship"].split(" ")[0])

    def test_coexisting_fact_preserved_by_reviewed_not_topic_overwrite(self):
        case = self.cases["P01"]
        reviewed = run_scenario(case, "reviewed")
        baseline = run_scenario(case, "topic_overwrite")
        self.assertEqual(reviewed["active_steps"], ["a", "b"])
        self.assertTrue(reviewed["exact_active_state"])
        self.assertEqual(baseline["active_steps"], ["b"])
        self.assertEqual(baseline["missing_expected_steps"], ["a"])
        self.assertFalse(baseline["checks"][0]["support_available"])

    def test_actual_reviewed_sqlite_supersedes_named_fact_only(self):
        case = self.cases["P02"]
        reviewed = run_scenario(case, "reviewed")
        append = run_scenario(case, "append_all")
        self.assertEqual(reviewed["active_steps"], ["b"])
        self.assertEqual(reviewed["stale_old_steps_active"], [])
        self.assertEqual(append["active_steps"], ["a", "b"])
        self.assertEqual(append["stale_old_steps_active"], ["a"])

    def test_semantic_duplicate_is_scripted_to_skip_not_model_scored(self):
        case = self.cases["P03"]
        reviewed = run_scenario(case, "reviewed")
        appended = run_scenario(case, "append_all")
        self.assertEqual(reviewed["active_steps"], ["a"])
        self.assertEqual(appended["active_steps"], ["a", "b"])
        self.assertEqual(appended["unexpected_active_steps"], ["b"])

    def test_exact_formatting_duplicate_is_not_written_by_reference(self):
        reviewed = run_scenario(self.cases["P11"], "reviewed")
        self.assertEqual(reviewed["active_steps"], ["a"])
        self.assertTrue(reviewed["exact_active_state"])

    def test_ambiguous_change_keeps_original_and_does_not_guess(self):
        output = run_scenario(self.cases["P07"], "reviewed")
        self.assertEqual(output["active_steps"], ["a", "b"])
        self.assertTrue(output["checks"][1]["expect_abstention"])
        self.assertIsNone(output["checks"][1]["support_available"])

    def test_multi_step_meeting_preserves_new_location_and_material(self):
        reviewed = run_scenario(self.cases["P12"], "reviewed")
        overwrite = run_scenario(self.cases["P12"], "topic_overwrite")
        self.assertEqual(reviewed["active_steps"], ["b", "c"])
        self.assertEqual(overwrite["active_steps"], ["c"])
        self.assertEqual(overwrite["missing_expected_steps"], ["b"])

    def test_different_people_same_topic_are_preserved(self):
        output = run_scenario(self.cases["P13"], "reviewed")
        self.assertEqual(len(output["active_memories"]), 2)
        self.assertTrue(all(q["support_available"] for q in output["checks"]))

    def test_all_fourteen_reference_states_match_authored_expectations(self):
        # This is an implementation smoke test, NOT classifier accuracy.
        results = [run_scenario(case, "reviewed")
                   for case in self.dataset["scenarios"]]
        self.assertEqual(sum(x["exact_active_state"] for x in results), 14)

    def test_lexical_checks_are_strict_and_do_not_claim_semantic_truth(self):
        self.assertTrue(phrase_present("The herb is thyme. [M1]", "thyme"))
        self.assertFalse(phrase_present("The herb is thymeleaf.", "thyme"))
        check = {"expected_phrases": ["Quartz"]}
        self.assertTrue(score_text_answer(check, "Quartz Wing")["text_proxy_pass"])
        self.assertFalse(
            score_text_answer(check, "I cannot determine that.")["text_proxy_pass"]
        )
        self.assertEqual(
            score_text_answer(check, "Quartz Wing")["rule"],
            "includes_author_keyword_and_no_abstention_phrase"
        )

    def test_expected_abstention_requires_declared_phrase(self):
        check = {"expect_abstention": True}
        self.assertTrue(
            score_text_answer(check, NO_MEMORY_ANSWER)["text_proxy_pass"]
        )
        self.assertFalse(score_text_answer(check, "Friday")["text_proxy_pass"])

    def test_mock_answer_generator_receives_temporary_active_records(self):
        seen = []
        def fake(question, memories, model):
            seen.append((question, copy.deepcopy(memories), model))
            return "Juniper Studio has a printing press and a drying rack."
        result = run_scenario(
            self.cases["P01"], "reviewed", answer_fn=fake, model="test-model"
        )
        self.assertEqual(len(seen), 2)
        self.assertEqual(seen[0][2], "test-model")
        self.assertEqual(len(seen[0][1]), 2)
        self.assertEqual(
            sum(x["text_proxy_pass"] for x in result["checks"]), 2
        )

    def test_model_answer_does_not_change_reference_storage(self):
        def bogus(question, memories, model):
            return "This answer contains no matching expected phrase."
        offline = run_scenario(self.cases["P04"], "reviewed")
        online = run_scenario(
            self.cases["P04"], "reviewed", answer_fn=bogus
        )
        self.assertEqual(
            offline["active_steps"], online["active_steps"]
        )
        self.assertEqual(
            sum(x["text_proxy_pass"] for x in online["checks"]), 0
        )

    def test_resume_writes_new_scenario_not_previous(self):
        with tempfile.TemporaryDirectory() as folder:
            outfile = Path(folder) / "results.json"
            data, digest = self.dataset, self.digest
            first = run_all(
                data, digest, ("reviewed",), limit=2,
                output=outfile, log=lambda _: None
            )
            self.assertEqual(len(first["results"]), 2)
            saved = json.loads(outfile.read_text(encoding="utf-8"))
            older = copy.deepcopy(saved["results"]["P01_reviewed"])
            second = run_all(
                data, digest, ("reviewed",), limit=3,
                output=outfile, log=lambda _: None
            )
            self.assertEqual(len(second["results"]), 3)
            self.assertEqual(second["results"]["P01_reviewed"], older)

    def test_different_run_configuration_refuses_merge(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "results.json"
            run_all(
                self.dataset, self.digest, ("reviewed",),
                limit=1, output=output, log=lambda _: None
            )
            keys = {s["id"] + "_" + p
                    for s in self.dataset["scenarios"] for p in POLICIES}
            with self.assertRaisesRegex(ValueError, "different configuration"):
                load_result(
                    output, self.digest, POLICIES, "qwen2.5:1.5b",
                    False, keys
                )
            with self.assertRaisesRegex(ValueError, "different configuration"):
                load_result(
                    output, "x" * 64, ("reviewed",), "qwen2.5:1.5b",
                    False, keys
                )

    def test_report_declares_development_and_retrieval_limitation(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "results.json"
            state = run_all(
                self.dataset, self.digest, ("reviewed",),
                output=output, log=lambda _: None
            )
            report = make_report(state)
            self.assertIn("Not independent model accuracy", report)
            self.assertIn("embedding similarity/retrieval is NOT tested", report)
            self.assertTrue(output.with_suffix(".md").exists())
            summary = summarize(state["results"])
            self.assertEqual(summary["reviewed"]["scenarios"], 14)
            self.assertEqual(summary["reviewed"]["state_exact"], 14)

    def test_reference_scenarios_never_mutate_question_list(self):
        original = copy.deepcopy(self.cases["P10"])
        run_scenario(self.cases["P10"], "append_all")
        self.assertEqual(self.cases["P10"], original)


if __name__ == "__main__":
    unittest.main()
