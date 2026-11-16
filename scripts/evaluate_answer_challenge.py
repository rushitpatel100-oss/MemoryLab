"""Evaluate frozen reviewer labels against the lexical novelty probe.

This tests a *detector* on newly curated fictional answer pairs, NOT
Qwen answer quality. Human labels must be completed and frozen BLIND
to probe outputs. Single-reviewer, project-authored data are NOT an
independently sourced or generally representative gold benchmark.

    python -m scripts.evaluate_answer_challenge

Inputs are never changed, and outputs in results/raw are Git-ignored.
"""
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from scripts.phase13_review import DATASET, SIGNOFF, load_dataset, load_signoff
from scripts.probe_answer_novelty import check_answer

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "results" / "raw" / "phase13_probe_evaluation.json"
REPORT = ROOT / "results" / "raw" / "phase13_probe_evaluation.md"
FLAG_STATUSES = frozenset({
    "unsupported_weekday", "unsupported_number",
    "invalid_citation", "novel_terms_review",
})


def evaluate(dataset, digest, signoff):
    cases = dataset["cases"]
    ids = {case["id"] for case in cases}
    if (signoff.get("dataset_sha256") != digest
        or signoff.get("review_method")
            != "project_curated_single_reviewer_blind_to_probe"
        or signoff.get("independent_source_ground_truth") is not False
        or signoff.get("blind_to_probe_output") is not True
        or not isinstance(signoff.get("locked_at"), str)
        or set(signoff.get("decisions", {})) != ids):
        raise ValueError("Frozen, matching human-reviewed decisions are required.")
    rows = []
    for case in cases:
        outcome = check_answer(
            case["question"], case["candidate_answer"],
            case["retrieved_memories"]
        )
        true_label = signoff["decisions"][case["id"]]["label"]
        flagged = outcome["status"] in FLAG_STATUSES
        if true_label not in ("supported", "unsupported", "uncertain"):
            raise ValueError("Invalid human review label.")
        result_kind = "excluded_uncertain"
        if true_label == "unsupported":
            result_kind = "true_positive" if flagged else "false_negative"
        elif true_label == "supported":
            result_kind = "false_positive" if flagged else "true_negative"
        rows.append({
            "id": case["id"], "question": case["question"],
            "candidate_answer": case["candidate_answer"],
            "review_label": true_label,
            "review_rationale": signoff["decisions"][case["id"]].get("rationale", ""),
            "probe_status": outcome["status"], "probe_flagged": flagged,
            "novel_terms": outcome["novel_terms"],
            "unsupported_weekdays": outcome["unsupported_weekdays"],
            "unsupported_numbers": outcome["unsupported_numbers"],
            "bad_citations": outcome["bad_citations"],
            "error_class": result_kind,
        })
    counts = Counter(row["error_class"] for row in rows)
    tp, fp, tn, fn = (
        counts["true_positive"], counts["false_positive"],
        counts["true_negative"], counts["false_negative"]
    )
    def ratio(n, d):
        return round(n / d, 4) if d else None
    return {
        "method": "reviewer_blind_probe_stress_test_not_independent_accuracy",
        "source_provenance": dataset.get("provenance"),
        "cases": len(rows),
        "review_labels": dict(Counter(r["review_label"] for r in rows)),
        "probe_status_distribution": dict(Counter(r["probe_status"] for r in rows)),
        "counts": {
            "true_positive": tp, "false_positive": fp,
            "true_negative": tn, "false_negative": fn,
            "excluded_uncertain": counts["excluded_uncertain"],
        },
        "detection_precision_on_curated_cases": ratio(tp, tp + fp),
        "detection_recall_on_curated_cases": ratio(tp, tp + fn),
        "rows": rows,
    }


def markdown(result, dataset_sha, signoff_sha):
    m = result["counts"]
    lines = [
        "# Phase 13 — Human-reviewed novelty-probe challenge",
        "",
        "**Curated fictional stress test, NOT independently sourced accuracy, "
        "not Qwen answer accuracy, and not a representative population sample.**",
        "The candidate answers were authored in the project. One reviewer "
        "labelled answers before seeing the probe outputs. The reviewer "
        "may still make mistakes or share the authors' assumptions.",
        "",
        "- Dataset SHA-256: " + dataset_sha,
        "- Frozen signoff SHA-256: " + signoff_sha,
        "- Total reviewed cases: " + str(result["cases"]),
        "- Label counts: " + str(result["review_labels"]),
        "- Probe status distribution: " + str(result["probe_status_distribution"]),
        "",
        "## Detection of reviewer-labelled unsupported answers",
        "",
        "| Finding | Count |", "|---|---:|",
        "| Unsupported and flagged (TP) | " + str(m["true_positive"]) + " |",
        "| Supported but flagged (FP) | " + str(m["false_positive"]) + " |",
        "| Supported and unflagged (TN) | " + str(m["true_negative"]) + " |",
        "| Unsupported but unflagged (FN) | " + str(m["false_negative"]) + " |",
        "| Reviewer uncertain; excluded | " + str(m["excluded_uncertain"]) + " |",
        "",
        "Precision on these curated cases: "
        + str(result["detection_precision_on_curated_cases"]),
        "Recall on these curated cases: "
        + str(result["detection_recall_on_curated_cases"]),
        "",
        "## Important errors for inspection",
        "",
    ]
    errors = [r for r in result["rows"]
              if r["error_class"] in ("false_positive", "false_negative")]
    if not errors:
        lines += ["No false positives/negatives in this reviewed sample; "
                  "this does not prove general correctness.", ""]
    for item in errors:
        lines += [
            "### " + item["id"] + " — " + item["error_class"],
            "",
            "**Question:** " + item["question"],
            "",
            "**Candidate answer:** " + item["candidate_answer"],
            "",
            "**Reviewer judgement:** " + item["review_label"],
            "",
            "**Probe status:** " + item["probe_status"],
            "",
        ]
    lines += ["## All results", "",
              "| Case | Reviewer | Probe | Outcome |",
              "|---|---|---|---|"]
    for r in result["rows"]:
        lines.append(
            "| " + r["id"] + " | " + r["review_label"]
            + " | " + r["probe_status"]
            + " | " + r["error_class"] + " |"
        )
    lines += [
        "", "## Limitations", "",
        "This probe compares answer vocabulary to retrieved facts; it does "
        "not establish whether an answer responds to the correct entity, "
        "attribute, time or negation. A 'no obvious novelty' result is not "
        "a correctness certificate. Precision/recall above are **descriptive "
        "statistics on a deliberately selected, project-authored set** "
        "with a single reviewer and must not be generalized.",
        "",
        "The old Phase 10/11 model-run data and personal SQLite memory "
        "were not read or changed by this scoring process.",
        "",
    ]
    return "\n".join(lines)


def main():
    try:
        dataset, digest = load_dataset()
        ids = {case["id"] for case in dataset["cases"]}
        raw_signoff = SIGNOFF.read_bytes()
        signoff = load_signoff(SIGNOFF, digest, ids)
        summary = evaluate(dataset, digest, signoff)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
        print("Phase 13 evaluation unavailable:", error)
        print("First review and freeze all cases in app_answer_challenge.py.")
        return 1
    if OUTPUT.exists() or REPORT.exists():
        print("Existing frozen comparison preserved; refusing to overwrite.")
        return 1
    summary["dataset_sha256"] = digest
    summary["signoff_sha256"] = hashlib.sha256(raw_signoff).hexdigest()
    summary["created_at"] = datetime.now(timezone.utc).isoformat()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("x", encoding="utf-8") as out:
        json.dump(summary, out, indent=2, ensure_ascii=False)
        out.write("\n")
    with REPORT.open("x", encoding="utf-8") as out:
        out.write(markdown(summary, digest, summary["signoff_sha256"]))
    print("Saved:", REPORT)
    print("Results:", summary["counts"])
    print("Curated development stress test, NOT independent accuracy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
