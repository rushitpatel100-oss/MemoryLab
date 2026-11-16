"""Compare Phase 8 versus Phase 9 AI drafts on the SAME exposed cases.

This is a regression DIAGNOSTIC. These cases have already been used for
design and review. Do not report this comparison as blind accuracy.

Run only when both local AI files are complete:
    python -m scripts.compare_ai_review_versions

No LLM calls, no SQLite writes, and no human labels are loaded.
"""
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from scripts.auto_review_holdout_v2 import OUTPUT as OLD_AI_FILE
from scripts.auto_review_v3 import OUTPUT as NEW_AI_FILE
from scripts.review_holdout_v2 import load_local_cases

ROOT = Path(__file__).resolve().parents[1]
REPORT_JSON = ROOT / "results" / "raw" / "phase9_ai_comparison.json"
REPORT_MD = ROOT / "results" / "raw" / "phase9_ai_comparison.md"
LABELS = ("duplicate", "replaces", "coexists", "uncertain")


def load_json(path):
    raw = Path(path).read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def compare(cases, digest, first, second):
    """Descriptive label-change data, never a ground-truth performance score."""
    case_ids = [c["id"] for c in cases]
    unique_ids = set(case_ids)
    if len(unique_ids) != len(case_ids):
        raise ValueError("Duplicate benchmark case identifiers.")
    for name, report in (("Phase 8", first), ("Phase 9", second)):
        if report.get("dataset_sha256") != digest:
            raise ValueError(name + ": dataset fingerprint mismatch.")
        if report.get("reviewer_type") != "automated_llm_not_human":
            raise ValueError(name + ": source is not an AI draft.")
        if report.get("independent_ground_truth") is not False:
            raise ValueError(name + ": invalid ground-truth claim.")
        answers = report.get("answers")
        if not isinstance(answers, dict) or set(answers) != unique_ids:
            raise ValueError(name + ": all cases must have model drafts.")
        for cid, decision in answers.items():
            if not isinstance(decision, dict) or decision.get("provisional_label") not in LABELS:
                raise ValueError(name + ": invalid relationship for " + cid)
    if second.get("policy_version") != "evidence_first_v3":
        raise ValueError("New report must be the Phase 9 V3 policy.")

    old, new = first["answers"], second["answers"]
    old_dist = Counter(x["provisional_label"] for x in old.values())
    new_dist = Counter(x["provisional_label"] for x in new.values())
    old_flags = sum(x.get("triage") == "needs_review" for x in old.values())
    new_flags = sum(x.get("triage") == "needs_review" for x in new.values())
    changes = []
    details = []
    for case in cases:
        cid = case["id"]
        before, after = old[cid], new[cid]
        previous = before["provisional_label"]
        current = after["provisional_label"]
        details.append({
            "id": cid, "phase8_label": previous, "phase9_label": current,
            "phase8_flagged": before.get("triage") == "needs_review",
            "phase9_flagged": after.get("triage") == "needs_review",
            "phase9_flags": after.get("flags", []),
        })
        if previous != current:
            changes.append({"id": cid, "from": previous, "to": current})
    return {
        "case_count": len(cases),
        "phase8_distribution": {label: old_dist.get(label, 0) for label in LABELS},
        "phase9_distribution": {label: new_dist.get(label, 0) for label in LABELS},
        "phase8_flagged": old_flags,
        "phase9_flagged": new_flags,
        "changed_relations": len(changes),
        "changes": changes,
        "rows": details,
        "interpretation": (
            "Exploratory AI draft comparison on previously exposed cases. "
            "Not human-labelled accuracy, not independent validation, "
            "and not proof that Phase 9 improves factual correctness."
        ),
    }


def markdown(result, old_sha, new_sha):
    lines = [
        "# Phase 9 — Automated reviewer diagnostic (not accuracy)",
        "",
        result["interpretation"],
        "",
        "- Cases: " + str(result["case_count"]),
        "- Original AI file SHA-256: " + old_sha,
        "- V3 AI file SHA-256: " + new_sha,
        "- Changed relation labels: " + str(result["changed_relations"]),
        "- Original flagged: " + str(result["phase8_flagged"]),
        "- V3 flagged: " + str(result["phase9_flagged"]),
        "",
        "| Relation | Old AI reviewer | Evidence-first V3 |",
        "|---|---:|---:|",
    ]
    for label in LABELS:
        lines.append(
            "| " + label + " | "
            + str(result["phase8_distribution"][label]) + " | "
            + str(result["phase9_distribution"][label]) + " |"
        )
    lines += ["", "## Case-by-case provisional AI labels", ""]
    lines += [
        "| Case | Old AI | V3 AI | V3 needs review |",
        "|---|---|---|---|",
    ]
    for item in result["rows"]:
        lines.append(
            "| " + item["id"] + " | " + item["phase8_label"]
            + " | " + item["phase9_label"] + " | "
            + ("yes" if item["phase9_flagged"] else "no") + " |"
        )
    lines += [
        "", "## Interpretation", "",
        "Differences describe what changed between two AI methods. "
        "A more balanced label distribution is not by itself an accuracy "
        "improvement. The original 24 cases are not a new blind holdout.",
        "",
        "The historical user-reviewed labels, original AI drafts, "
        "SQLite memories and signoff records were not overwritten.",
        "",
    ]
    return "\n".join(lines)


def main():
    try:
        cases, digest = load_local_cases()
        old, old_sha = load_json(OLD_AI_FILE)
        new, new_sha = load_json(NEW_AI_FILE)
        result = compare(cases, digest, old, new)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
        print("Cannot compare:", error)
        print("Run the Phase 9 AI review to completion first.")
        return 1
    if REPORT_JSON.exists() or REPORT_MD.exists():
        print("Existing Phase 9 comparison preserved. No overwrite.")
        return 1
    result["created_at"] = datetime.now(timezone.utc).isoformat()
    result["original_ai_sha256"] = old_sha
    result["phase9_ai_sha256"] = new_sha
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_JSON.open("x", encoding="utf-8") as out:
        json.dump(result, out, indent=2, ensure_ascii=False)
        out.write("\n")
    with REPORT_MD.open("x", encoding="utf-8") as out:
        out.write(markdown(result, old_sha, new_sha))
    print(
        f"{result['changed_relations']}/{result['case_count']} AI labels changed."
    )
    print("Original distribution:", result["phase8_distribution"])
    print("Phase 9 distribution:", result["phase9_distribution"])
    print("Comparison saved:", REPORT_MD)
    print("These are diagnostics, not independently evaluated accuracy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
