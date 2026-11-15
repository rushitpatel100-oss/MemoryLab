"""Conservative, auditable replacement-evidence gate for MemoryLab.

Does not verify truth, subject identity, or attribute identity. It ONLY
recognises a narrow old-value-to-new-value text signal. If Qwen suggests
replacement without that signal, the displayed recommendation becomes
"uncertain"; the original model prediction is preserved for evaluation.
Nothing here writes to SQLite or authorises supersession.
"""
import re

from memory_conflicts import classify_pair
from memory_text import normalize_fact

# This is deliberately narrow: it does not pretend to understand every
# natural-language revision. It can miss true updates and can be fooled
# by unrelated phrases. User approval remains necessary in all cases.
CUE = re.compile(
    r"\b(moved|move|switched|switch|renamed|rename|repainted|repaint|"
    r"rescheduled|reschedule|changed|change|updated|update)\b",
    re.IGNORECASE,
)
TRANSITION = re.compile(
    r"\bfrom\s+([\w'-]+(?:\s+[\w'-]+){0,3})\s+to\s+"
    r"([\w'-]+(?:\s+[\w'-]+){0,3})(?=\W|$)",
    re.IGNORECASE,
)


def replacement_evidence(old_fact, new_fact):
    """Find a possible explicit value transition, not proof of a valid update.

    For safety, an old value must appear as whole words in the old text;
    there must be a change verb before an explicit 'from X to Y' span.
    """
    old = normalize_fact(old_fact)
    new = normalize_fact(new_fact)
    for match in TRANSITION.finditer(new):
        previous_text = new[:match.start()]
        if not CUE.search(previous_text):
            continue
        previous_value, new_value = match.group(1).strip(), match.group(2).strip()
        if previous_value == new_value:
            continue
        if re.search(
            r"(?<!\w)" + re.escape(previous_value) + r"(?!\w)", old
        ):
            return {
                "status": "transition_signal",
                "reason": (
                    f"New fact states a change from '{previous_value}' "
                    f"to '{new_value}', and the old fact mentions "
                    f"'{previous_value}'. Confirm subject and attribute manually."
                ),
            }
    return {
        "status": "needs_review",
        "reason": (
            "No narrow, explicit old-value-to-new-value transition "
            "was verified by the text rule. The old fact may still be valid."
        ),
    }


def apply_replacement_gate(old, new_fact, proposal):
    """Apply a transparent guard to an existing model recommendation."""
    raw_relation = proposal["relation"]
    result = dict(proposal)
    result["raw_relation"] = raw_relation
    if raw_relation != "replaces":
        result["gate"] = {
            "status": "not_applicable",
            "reason": "Qwen did not suggest superseding this fact.",
        }
        return result

    evidence = replacement_evidence(old["fact"], new_fact)
    result["gate"] = evidence
    if evidence["status"] == "needs_review":
        result["relation"] = "uncertain"
        result["reason"] = (
            "Replacement not supported by the narrow text-evidence rule. "
            "Preserve the old fact unless you independently verify the update."
        )
    return result


def classify_pair_guarded(old, new_topic, new_fact, *, classifier=None):
    """Single Qwen call plus a free local text check; no extra LLM calls."""
    compare = classifier if classifier is not None else classify_pair
    proposal = compare(old, new_topic, new_fact)
    return apply_replacement_gate(old, new_fact, proposal)
