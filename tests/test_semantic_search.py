"""Offline unit tests: no local Ollama instance required."""

import unittest
from unittest.mock import patch

from semantic_search import cosine_similarity, find_similar


class SemanticSearchTests(unittest.TestCase):
    def test_identical_vectors(self):
        self.assertAlmostEqual(
            cosine_similarity([1.0, 2.0], [1.0, 2.0]),
            1.0
        )

    def test_zero_vector(self):
        self.assertEqual(
            cosine_similarity([0.0, 0.0], [1.0, 0.0]),
            0.0
        )

    def test_dimension_mismatch(self):
        with self.assertRaises(ValueError):
            cosine_similarity([1.0, 2.0], [1.0])

    @patch("semantic_search.get_embeddings")
    def test_retrieval_ranking(self, mocked_embeddings):
        mocked_embeddings.return_value = [
            [1.0, 0.0],  # query vector
            [0.0, 1.0],  # unrelated memory
            [1.0, 0.0],  # related memory
        ]
        memories = [
            {"topic": "hobby", "fact": "I like painting."},
            {"topic": "job", "fact": "I am a GenAI engineer."},
        ]
        results = find_similar("What is my profession?", memories)

        self.assertEqual(results[0]["memory"]["topic"], "job")
        self.assertGreater(results[0]["similarity"], results[1]["similarity"])

    @patch("semantic_search.get_embeddings")
    def test_empty_question_is_not_embedded(self, mocked_embeddings):
        self.assertEqual(
            find_similar("  ", [{"topic": "job", "fact": "Engineer"}]),
            []
        )
        mocked_embeddings.assert_not_called()


if __name__ == "__main__":
    unittest.main()
