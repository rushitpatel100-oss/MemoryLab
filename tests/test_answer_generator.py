"""Tests for the local chat integration without running Ollama."""

import io
import json
import unittest
from unittest.mock import patch

from answer_generator import NO_MEMORY_ANSWER, generate_answer


class AnswerGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.memories = [
            {
                "id": 7,
                "topic": "job",
                "fact": "I work as a GenAI engineer.",
            }
        ]

    @patch("answer_generator.urllib.request.urlopen")
    def test_no_memories_does_not_call_model(self, urlopen):
        self.assertEqual(
            generate_answer("What is my profession?", []),
            NO_MEMORY_ANSWER,
        )
        urlopen.assert_not_called()

    @patch("answer_generator.urllib.request.urlopen")
    def test_blank_question_does_not_call_model(self, urlopen):
        self.assertEqual(
            generate_answer("  ", self.memories),
            NO_MEMORY_ANSWER,
        )
        urlopen.assert_not_called()

    @patch("answer_generator.urllib.request.urlopen")
    def test_chat_payload_and_reply(self, urlopen):
        urlopen.return_value = io.BytesIO(
            b'{"message": {"content": "You are a GenAI engineer. [M7]"}}'
        )

        answer = generate_answer("What do I do?", self.memories)

        self.assertEqual(answer, "You are a GenAI engineer. [M7]")
        request = urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))

        self.assertEqual(payload["model"], "qwen2.5:1.5b")
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["options"]["temperature"], 0)
        self.assertIn("job", payload["messages"][1]["content"])
        self.assertIn(
            "I work as a GenAI engineer.",
            payload["messages"][1]["content"],
        )

    @patch("answer_generator.urllib.request.urlopen")
    def test_empty_response_raises(self, urlopen):
        urlopen.return_value = io.BytesIO(b'{"message": {"content": ""}}')
        with self.assertRaises(ValueError):
            generate_answer("What is my profession?", self.memories)


if __name__ == "__main__":
    unittest.main()
