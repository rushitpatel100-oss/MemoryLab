"""Audit V4 AI memory decisions without inference or memory changes.

Uses the SAVED V4 AI draft, not the user's signed labels.
Checks whether a proposed 'duplicate' could silently discard a real update.
Even an apparently safe duplicate is never authorized for skipping without
a separate human approval: this is an inspection tool, not a classifier.

    python -m scripts.audit_review_v4

Writes ONLY results/raw/phase9_v4_safety_audit.md and refuses overwrite.
No Ollama calls, no SQLite writes, no revisions to AI or human source JSON.
"""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from scripts.auto_review_v3 import exact_quote, role_conflict
from scripts.auto_review_v4 import OUTPUT as V4_FILE, POLICY
from scripts.review_holdout_v2 import load_local_cases

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "results" / "raw" / "phase9_v4_safety_audit.md"
LABELS = {"duplicate", "replaces", "coexists", "uncertain"}
CHANGE_LANGUAGE = re.compile(
    r"\b(?:replaced?|replacing|changed?|changing|moved?|moving|"
    r"stopped|ceased|switched|instead|no longer|rather than)\b",
    re.IGNORECASE,
)


def audit_case(case, draft):
    """Conservative general-purpose risk cues, not a new human gold label."""
    label = draft["provisional_label"]
    alerts = []
    contrasts = role_conflict(case["old_fact"], case["new_fact"])
    changed = bool(CHANGE_LANGUAGE.search(case["new_fact"]))
    if label == "duplicate":
        if contrasts:
            alerts.append(
                "Different role/location qualifier: " + ", ".join(contrasts)
            )
        if changed:
            alerts.append(
                "New fact contains change/cessation wording; may be an update."
            )
        axes = draft.get("axes", {})
        if axes.get("same_assertion") != "yes":
            alerts.append("AI duplicate label lacks explicit repetition evidence.")
        if axes.get("same_entity") != "yes" or axes.get("same_attribute") != "yes":
            alerts.append(
                "AI duplicate lacks confirmed matching entity/attribute."
            )
        for key, textkey, factkey in (
            ("old", "old_quote", "old_fact"),
            ("new", "new_quote", "new_fact"),
        ):
            if not exact_quote(draft.get(textkey), case[factkey]):
                alerts.append(
                    "Supporting " + key + " quote missing or not verbatim."
                )
    original_action = draft.get("safe_storage_action", "review_needed")
    if label == "duplicate":
        status = "high_priority" if alerts else "confirm_duplicate"
        guarded_action = "review_needed"
    elif label == "replaces":
        status = "confirm_replacement"
        guarded_action = "review_needed"
    elif label == "uncertain":
        status = "unresolved"
        guarded_action = "review_needed"
    else:
        status = "compatible_proposal"
        guarded_action = "keep_both"
    return {
        "id": case["id"],
        "old_fact": case["old_fact"],
        "new_fact": case["new_fact"],
        "ai_label": label,
        "v4_action": original_action,
        "audit_action": guarded_action,
        "status": status,
        "alerts": alerts,
    }


def audit(cases, digest, source):
    """Recompute review recommendations; do not change the source object."""
    ids = [c["id"] for c in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("Repeated case IDs in dataset.")
    if (source.get("dataset_sha256") != digest
            or source.get("reviewer_type") != "automated_llm_not_human"
            or source.get("independent_ground_truth") is not False
            or source.get("policy_version") != POLICY):
        raise ValueError("The V4 source provenance or dataset does not match.")
    answers = source.get("answers")
    if not isinstance(answers, dict) or set(answers) != set(ids):
        raise ValueError("Complete all 24 V4 reviews before auditing.")
    rows = []
    for case in cases:
        item = answers[case["id"]]
        if not isinstance(item, dict) or item.get("provisional_label") not in LABELS:
            raise ValueError("Invalid V4 decision for " + case["id"])
        rows.append(audit_case(case, item))
    count = Counter(row["status"] for row in rows)
    return {
        "cases": len(rows),
        "high_priority": count["high_priority"],
        "confirmation_needed": count["confirm_duplicate"],
        "replacement_confirmation": count["confirm_replacement"],
        "unresolved": count["unresolved"],
        "compatible_proposals": count["compatible_proposal"],
        "prevented_duplicate_skips": sum(
            row["ai_label"] == "duplicate"
            and row["audit_action"] == "review_needed" for row in rows
        ),
        "rows": rows,
    }


def render(result, source_sha):
    lines = [
        "# MemoryLab — V4 duplicate-suppression safety audit",
        "",
        "**Exploratory audit, not model accuracy or human ground truth.** "
        "This report flags possible false duplicates and requires a human "
        "decision before skipping any new memory.",
        "",
        "- Input V4 AI JSON SHA-256: " + source_sha,
        "- Cases: " + str(result["cases"]),
        "- High-priority duplicate warnings: "
        + str(result["high_priority"]),
        "- Other duplicate proposals requiring approval: "
        + str(result["confirmation_needed"]),
        "- Duplicate skips withheld from automation: "
        + str(result["prevented_duplicate_skips"]),
        "- Unresolved cases: " + str(result["unresolved"]),
        "- Replacement proposals requiring approval: "
        + str(result["replacement_confirmation"]),
        "",
        "## Review shortlist",
        "",
        "| Case | V4 label | Review priority | Suggested action | Reason |",
        "|---|---|---|---|---|",
    ]
    order = {"high_priority": 0, "confirm_duplicate": 1,
             "confirm_replacement": 2, "unresolved": 3,
             "compatible_proposal": 4}
    for row in sorted(result["rows"], key=lambda r: (order[r["status"]], r["id"])):
        reason = "; ".join(row["alerts"]) or (
            "AI proposal requires confirmation; no independently checked truth."
            if row["status"] == "confirm_duplicate" else
            "No extra automated high-risk signal; review per existing policy."
        )
        lines.append(
            "| " + row["id"] + " | " + row["ai_label"]
            + " | " + row["status"] + " | " + row["audit_action"]
            + " | " + reason.replace("|", "/").replace("\n", " ") + " |"
        )
    lines += [
        "", "## Highest-priority source facts", "",
    ]
    for row in result["rows"]:
        if row["status"] == "high_priority":
            lines += [
                "### " + row["id"], "",
                "**Old:** " + row["old_fact"], "",
                "**New:** " + row["new_fact"], "",
                "**Signals:** " + "; ".join(row["alerts"]), "",
            ]
    lines += [
        "## What this audit does not prove", "",
        "Change words and contrasting roles are generic warning heuristics, "
        "not a semantic classifier. Some warnings may be false positives, "
        "and unflagged duplicates may still be wrong. Any stored AI "
        "'skip_duplicate' recommendation is a proposed action, NOT permission "
        "to ignore a genuine update. This report does not alter the original "
        "V4 JSON, human labels, database, or earlier experiments. These "
        "24 cases are already exposed and must not be reported as a blind "
        "accuracy benchmark.", "",
    ]
    return "\n".join(lines)


def main():
    try:
        cases, digest = load_local_cases()
        raw = V4_FILE.read_bytes()
        data = json.loads(raw)
        result = audit(cases, digest, data)
    except (OSError, ValueError, TypeError) as error:
        print("Cannot audit V4:", error)
        return 1
    if OUTPUT.exists():
        print("Existing audit preserved:", OUTPUT)
        return 1
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("x", encoding="utf-8") as file:
        file.write(render(result, hashlib.sha256(raw).hexdigest()))
    print("Saved:", OUTPUT)
    print("High-priority duplicate warnings:", result["high_priority"])
    print("Other duplicates requiring human approval:",
          result["confirmation_needed"])
    print("Auto skip-duplicate actions withheld:",
          result["prevented_duplicate_skips"])
    print("No original review or memory was changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
