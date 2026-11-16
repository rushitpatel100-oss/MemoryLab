"""Offline grounding-guard tests; Ollama calls are mocked."""
import io
import json
import unittest
from unittest.mock import patch

from answer_evidence import (
    NO_MEMORY_ANSWER, SCHEMA, generate_extractive_answer,
    validate_extraction,
)


class ExtractiveEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.memories = [
            {"id": 1, "topic": "library", "fact": "The library has a blue telescope."},
            {"id": 2, "topic": "library", "fact": "The library opens on Fridays."},
        ]
        self.response = {
            "supported": True, "memory_id": 1,
            "quote": "blue telescope", "answer_span": "blue telescope",
            "explanation": "The object is explicitly stated.",
        }

    def test_valid_source_and_verbatim_answer_span(self):
        self.assertEqual(
            validate_extraction(self.response, self.memories)["answer_span"],
            "blue telescope",
        )

    def test_nonexistent_memory_id_refused(self):
        payload = dict(self.response, memory_id=9)
        self.assertIsNone(validate_extraction(payload, self.memories))

    def test_model_hallucinated_value_is_refused(self):
        payload = dict(self.response, answer_span="red telescope")
        self.assertIsNone(validate_extraction(payload, self.memories))

    def test_fake_quote_is_refused(self):
        payload = dict(self.response, quote="has a red telescope")
        self.assertIsNone(validate_extraction(payload, self.memories))

    def test_quote_cannot_come_from_different_memory(self):
        payload = dict(self.response, memory_id=2)
        self.assertIsNone(validate_extraction(payload, self.memories))

    def test_unsupported_answer_is_abstention(self):
        payload = dict(self.response, supported=False, memory_id=0,
                       quote="", answer_span="")
        self.assertIsNone(validate_extraction(payload, self.memories))

    @patch("answer_evidence.urllib.request.urlopen")
    def test_valid_model_message_yields_cited_extractive_answer(self, open_url):
        open_url.return_value = io.BytesIO(
            json.dumps({
                "message": {"content": json.dumps(self.response)}
            }).encode("utf-8")
        )
        answer = generate_extractive_answer(
            "What telescope does the library have?", self.memories
        )
        self.assertEqual(answer, "blue telescope [M1]")
        body = json.loads(open_url.call_args.args[0].data)
        self.assertEqual(body["format"], SCHEMA)
        self.assertEqual(body["model"], "qwen2.5:1.5b")
        self.assertIn("memory_records", body["messages"][1]["content"])

    @patch("answer_evidence.urllib.request.urlopen")
    def test_unsupported_response_fails_closed(self, open_url):
        open_url.return_value = io.BytesIO(
            b'{"message":{"content":"{\\"supported\\":false,\\"memory_id\\":0,\\"quote\\":\\"\\",\\"answer_span\\":\\"\\",\\"explanation\\":\\"unknown\\"}"}}'
        )
        self.assertEqual(
            generate_extractive_answer("Which day is new?", self.memories),
            NO_MEMORY_ANSWER
        )

    @patch("answer_evidence.urllib.request.urlopen")
    def test_malformed_model_message_fails_closed(self, open_url):
        open_url.return_value = io.BytesIO(
            b'{"message":{"content":"not valid json"}}'
        )
        self.assertEqual(
            generate_extractive_answer("Which day?", self.memories),
            NO_MEMORY_ANSWER
        )

    @patch("answer_evidence.urllib.request.urlopen")
    def test_no_memories_never_calls_model(self, open_url):
        self.assertEqual(
            generate_extractive_answer("What is the answer?", []),
            NO_MEMORY_ANSWER
        )
        open_url.assert_not_called()

    def test_boolean_id_not_treated_as_integer_one(self):
        payload = dict(self.response, memory_id=True)
        self.assertIsNone(validate_extraction(payload, self.memories))

    def test_wrong_answer_with_real_quote_is_not_guaranteed_caught(self):
        # Intentionally documents the limitation of extractive validation.
        response = dict(self.response, memory_id=2,
                        quote="opens on Fridays", answer_span="Fridays")
        self.assertIsNotNone(validate_extraction(response, self.memories))
        # A question asking for a *new* day might still be answered incorrectly.


if __name__ == "__main__":
    unittest.main()
