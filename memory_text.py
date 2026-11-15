"""Pure text rules for conservative, exact-ish memory duplicate detection.

This detects the same words after case, whitespace, Unicode compatibility
and terminal punctuation normalization. It is not a semantic equivalence test.
"""
import unicodedata


def normalize_topic(value):
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def normalize_fact(value):
    value = " ".join(unicodedata.normalize("NFKC", value).casefold().split())
    return value.rstrip(" .!?")


def is_same_stored_fact(old_topic, old_fact, new_topic, new_fact):
    """Compare two topic/fact pairs without calling an LLM."""
    return (
        normalize_topic(old_topic) == normalize_topic(new_topic)
        and normalize_fact(old_fact) == normalize_fact(new_fact)
    )
