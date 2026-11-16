"""Summarize Phase 9 V3 versus V4 AI behaviour (NOT accuracy).

Run AFTER scripts.auto_review_v4 completes all 24 cases:
    python -m scripts.compare_v3_v4

Reads two separate local AI outputs, writes only:
    results/raw/phase9_v4_diagnostic.md
Never loads human signoffs, calls Qwen or touches memorylab.db.
The 24 examples were already exposed and are NOT blind evaluation data.
"""
import hashlib
import json
from collections import Counter
from pathlib import Path

from scripts.auto_review_v3 import OUTPUT as V3
from scripts.auto_review_v4 import OUTPUT as V4
from scripts.review_holdout_v2 import load_local_cases

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "results" / "raw" / "phase9_v4_diagnostic.md"
LABELS = ("duplicate", "replaces", "coexists", "uncertain")


def load_json(path):
    raw = Path(path).read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def compare(cases, digest, previous, current):
    ids = [case["id"] for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate case IDs.")
    for name, doc, policy in (
        ("V3", previous, "evidence_first_v3"),
        ("V4", current, "contrastive_evidence_v4"),
    ):
        if (doc.get("dataset_sha256") != digest
            or doc.get("reviewer_type") != "automated_llm_not_human"
            or doc.get("independent_ground_truth") is not False
            or doc.get("policy_version") != policy):
            raise ValueError(name + ": dataset or policy mismatch.")
        ans = doc.get("answers")
        if not isinstance(ans, dict) or set(ans) != set(ids):
            raise ValueError(name + ": all cases must be completed.")
        if any(not isinstance(x, dict) or x.get("provisional_label") not in LABELS
               for x in ans.values()):
            raise ValueError(name + ": invalid relation label.")
    before, after = previous["answers"], current["answers"]
    old_counts = Counter(x["provisional_label"] for x in before.values())
    new_counts = Counter(x["provisional_label"] for x in after.values())
    flagged_old = sum(x.get("triage") == "needs_review" for x in before.values())
    flagged_new = sum(x.get("triage") == "needs_review" for x in after.values())
    evidence_unknown = {
        key: sum(
            x.get("axes", {}).get(key) == "unknown"
            for x in after.values()
        )
        for key in ("same_entity", "same_attribute", "same_assertion",
                    "old_fact_known_obsolete", "new_value_known")
    }
    changes = []
    for cid in ids:
        prev = before[cid]["provisional_label"]
        curr = after[cid]["provisional_label"]
        changes.append({
            "id": cid, "v3": prev, "v4": curr,
            "v4_flagged": after[cid].get("triage") == "needs_review",
            "v4_flag_reasons": after[cid].get("flags", []),
            "v4_has_raw_response": bool(after[cid].get("raw_model_response")),
        })
    return {
        "cases": len(ids),
        "v3": {key: old_counts[key] for key in LABELS},
        "v4": {key: new_counts[key] for key in LABELS},
        "v3_flagged": flagged_old, "v4_flagged": flagged_new,
        "label_changes": sum(x["v3"] != x["v4"] for x in changes),
        "v4_unknown_axes": evidence_unknown,
        "v4_raw_response_saved": sum(x["v4_has_raw_response"] for x in changes),
        "rows": changes,
    }


def markdown(result, v3_sha, v4_sha):
    lines = [
        "# Phase 9 — V3 versus V4 AI diagnostic (not accuracy)",
        "",
        "**These 24 cases have already been used for reviewer development.** "
        "This report measures model behaviour, NOT independent accuracy.",
        "",
        "- V3 AI file SHA-256: " + v3_sha,
        "- V4 AI file SHA-256: " + v4_sha,
        "- Cases: " + str(result["cases"]),
        "- Labels changed: " + str(result["label_changes"]),
        "- Cases flagged V3: " + str(result["v3_flagged"]),
        "- Cases flagged V4: " + str(result["v4_flagged"]),
        "- V4 raw model response saved: " + str(result["v4_raw_response_saved"]),
        "",
        "## Relation distribution",
        "| Relation | V3 | V4 |", "|---|---:|---:|",
    ]
    for label in LABELS:
        lines.append(
            "| " + label + " | " + str(result["v3"][label])
            + " | " + str(result["v4"][label]) + " |"
        )
    lines += ["", "## V4 unknown evidence axes", "",
              "| Evidence axis | Cases unknown |", "|---|---:|"]
    for axis, n in result["v4_unknown_axes"].items():
        lines.append("| " + axis + " | " + str(n) + " |")
    lines += ["", "## Per-case output", "",
              "| Case | V3 | V4 | V4 flagged | Warnings |",
              "|---|---|---|---|---:|"]
    for row in result["rows"]:
        lines.append(
            "| " + row["id"] + " | " + row["v3"]
            + " | " + row["v4"] + " | "
            + ("yes" if row["v4_flagged"] else "no")
            + " | " + str(len(row["v4_flag_reasons"])) + " |"
        )
    lines += [
        "", "## Interpretation", "",
        "A decrease in unknowns or a wider mix of predicted labels is not "
        "proof of correctness. Confidence remains limited by a small local "
        "model and the lack of independently human-labelled, new cases. "
        "Even when V4 proposes a replacement, its safe storage action remains "
        "review_needed and no memory data is modified.",
        "",
    ]
    return "\n".join(lines)


def main():
    try:
        cases, digest = load_local_cases()
        v3, v3_sha = load_json(V3)
        v4, v4_sha = load_json(V4)
        result = compare(cases, digest, v3, v4)
    except (OSError, ValueError, TypeError, KeyError) as error:
        print("Comparison unavailable:", error)
        print("Finish python -m scripts.auto_review_v4 first.")
        return 1
    if OUTPUT.exists():
        print("Existing comparison preserved:", OUTPUT)
        return 1
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("x", encoding="utf-8") as file:
        file.write(markdown(result, v3_sha, v4_sha))
    print("V4 distribution:", result["v4"])
    print("Per-case changes:", result["label_changes"])
    print("Saved diagnostic:", OUTPUT)
    print("This is not an independently verified accuracy improvement.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
