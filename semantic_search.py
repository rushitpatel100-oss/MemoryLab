"""Local semantic memory retrieval using Ollama's all-minilm embedding model."""

import json
import math
import urllib.request


def get_embeddings(sentences):
    """Request embedding vectors from the local Ollama API."""
    data = {
        "model": "all-minilm",
        "input": sentences
    }

    request = urllib.request.Request(
        "http://localhost:11434/api/embed",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(
        request, timeout=120
    ) as response:
        result = json.load(response)

    return result["embeddings"]


def cosine_similarity(vector_a, vector_b):
    """Compute cosine similarity between two same-length numeric vectors."""
    if len(vector_a) != len(vector_b):
        raise ValueError("Embedding dimensions must match")

    dot_product = sum(
        a * b for a, b in zip(vector_a, vector_b)
    )

    length_a = math.sqrt(
        sum(a * a for a in vector_a)
    )

    length_b = math.sqrt(
        sum(b * b for b in vector_b)
    )

    if length_a == 0 or length_b == 0:
        return 0.0

    return dot_product / (length_a * length_b)


def find_similar(question, memories):
    """Rank active candidate memory records by similarity to a question."""
    if not question.strip() or not memories:
        return []

    sentences = [question]

    for memory in memories:
        text = f"{memory['topic']}: {memory['fact']}"
        sentences.append(text)

    embeddings = get_embeddings(sentences)

    question_vector = embeddings[0]
    results = []

    for memory, memory_vector in zip(
        memories, embeddings[1:]
    ):
        similarity = cosine_similarity(
            question_vector, memory_vector
        )

        results.append({
            "memory": memory,
            "similarity": similarity
        })

    results.sort(
        key=lambda item: item["similarity"],
        reverse=True
    )

    return results
