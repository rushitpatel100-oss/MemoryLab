"""A controlled memory impact pilot; no learned utility policy yet."""

from time import perf_counter

from answer_generator import DEFAULT_CHAT_MODEL, generate_answer


def run_memory_comparison(question, memory, model=DEFAULT_CHAT_MODEL):
    """Call the same local LLM with and without one provided memory.

    This experiment holds the prompt template and model options fixed,
    apart from the presence of the memory record. It does not determine
    if an answer is correct; a human must score each outcome.
    """
    if not question.strip():
        raise ValueError("Question cannot be blank.")
    if not memory or not all(
        key in memory for key in ("id", "topic", "fact")
    ):
        raise ValueError("Select a valid memory record.")

    start = perf_counter()
    without_answer = generate_answer(
        question, [], model=model, allow_empty_context=True
    )
    without_time = perf_counter() - start

    start = perf_counter()
    with_answer = generate_answer(
        question, [memory], model=model, allow_empty_context=True
    )
    with_time = perf_counter() - start

    return {
        "question": question.strip(),
        "model": model,
        "memory": {
            "id": memory["id"],
            "topic": memory["topic"],
            "fact": memory["fact"],
        },
        "without_memory": {
            "answer": without_answer,
            "elapsed_seconds": round(without_time, 3),
        },
        "with_memory": {
            "answer": with_answer,
            "elapsed_seconds": round(with_time, 3),
        },
        "experiment_type": "manual_pilot_not_formal_evaluation",
    }
