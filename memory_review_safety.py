"""Reusable warnings for potentially misleading AI memory relationships.

These are generic text cues for a HUMAN reviewer, NOT a semantic
classifier. A missing warning does not prove that a memory can safely
be skipped or superseded. This module has no model/database/network access.
"""
import re

_CHANGE_WORDS = re.compile(
    r"\b(?:replaced?|replacing|changed?|changing|moved?|moving|"
    r"stopped|ceased|switched|instead|no longer|rather than)\b",
    re.IGNORECASE,
)
_ROLE_PAIRS = (
    ("home", "away"), ("office", "basement"), ("morning", "evening"),
)


def role_contrasts(old_fact, new_fact):
    """Find specific role/qualifier contrasts; only heuristic signals."""
    before = set(re.findall(r"[a-z]+", old_fact.casefold()))
    after = set(re.findall(r"[a-z]+", new_fact.casefold()))
    return [
        f"{a} versus {b}" for a, b in _ROLE_PAIRS
        if (a in before and b in after) or (b in before and a in after)
    ]


def duplicate_risk_signals(old_fact, new_fact):
    """Warnings for an AI-suggested duplicate; never approve suppression."""
    flags = []
    contrasts = role_contrasts(old_fact, new_fact)
    if contrasts:
        flags.append("Different role/location qualifier: " + ", ".join(contrasts))
    if _CHANGE_WORDS.search(new_fact):
        flags.append(
            "New fact contains change/cessation wording; may be an update."
        )
    return flags


def replacement_risk_signals(old_fact, new_fact):
    """Extra cautions for a proposed supersession of an old fact."""
    flags = []
    contrasts = role_contrasts(old_fact, new_fact)
    if contrasts:
        flags.append(
            "Potentially different entities or attributes: "
            + ", ".join(contrasts)
        )
    if re.search(r"\bone of\b", new_fact, re.IGNORECASE):
        flags.append(
            "New fact uses an indefinite referent ('one of'); identity is not proven."
        )
    return flags


def requires_confirmation(relation, source="qwen"):
    """Any non-exact AI duplicate or replacement must be confirmed."""
    return relation in {"duplicate", "replaces", "uncertain"} and source != "local_rule"
