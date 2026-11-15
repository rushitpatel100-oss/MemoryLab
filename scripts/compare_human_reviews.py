"""Compare locked human reviews, without running Qwen.

   python -m scripts.compare_human_reviews

The second reviewer should not run this script before their labels
are complete and locked. Neither label file is modified.
"""
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from scripts.review_eval_cases import (
    LABELS_FILE, load_cases, load_review,
)
from scripts.review_second import SECOND_FILE, load_second

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "results" / "raw" / "review_v1_disagreements.json"

# Declared before second review: items meriting semantic rubric review
# even when both raters happen to agree.
PRIORITY_IDS = {"B02", "B04", "B07", "B10", "B12", "B15", "B18"}
LABELS = ("duplicate", "replaces", "coexists", "uncertain")


def locked_reviews(cases, digest, first_path=LABELS_FILE,
                   second_path=SECOND_FILE):
    ids = {c["id"] for c in cases}
    first = load_review(first_path, digest, ids)
    second = load_second(second_path, digest, ids)
    if first.get("locked") is not True:
        raise ValueError("The original human labels are not locked.")
    if second.get("locked") is not True:
        raise ValueError(
            "Second review is not locked. Finish reviewing before comparison."
        )
    for name, review in (("First", first), ("Second", second)):
        if set(review["answers"]) != ids:
            raise ValueError(name + " reviewer has incomplete labels.")
    return first, second


def build_comparison(cases, first, second):
    """Keep each rater's original answers, reasons and structured axes."""
    rows = []
    for case in cases:
        cid = case["id"]
        first_answer = first["answers"][cid]
        second_answer = second["answers"][cid]
        differs = first_answer["label"] != second_answer["label"]
        priority = cid in PRIORITY_IDS
        rows.append({
            "id": cid,
            "topic": case["topic"],
            "old_fact": case["old_fact"],
            "new_fact": case["new_fact"],
            "first": {
                "label": first_answer["label"],
                "reason": first_answer["reason"],
            },
            "second": second_answer,
            "disagreement": differs,
            "pre_registered_priority": priority,
            "adjudicate": differs or priority,
        })
    agreements = sum(not row["disagreement"] for row in rows)
    n = len(rows)
    p_o = agreements / n if n else 0
    p1 = Counter(row["first"]["label"] for row in rows)
    p2 = Counter(row["second"]["label"] for row in rows)
    p_e = sum(p1[label] * p2[label] for label in LABELS) / (n * n) if n else 0
    kappa = ((p_o - p_e) / (1 - p_e)) if n and p_e < 1 else None
    metrics = {
        "total": n,
        "same_label": agreements,
        "disagreements": n - agreements,
        "agreement_fraction": round(p_o, 4),
        "cohens_kappa": round(kappa, 4) if kappa is not None else None,
        "rater1_counts": dict(p1),
        "rater2_counts": dict(p2),
        "needs_adjudication": sum(row["adjudicate"] for row in rows),
        "adjudication_ids": [
            row["id"] for row in rows if row["adjudicate"]
        ],
    }
    return rows, metrics


def main():
    try:
        cases, digest = load_cases()
        first, second = locked_reviews(cases, digest)
        rows, metrics = build_comparison(cases, first, second)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as error:
        print("Cannot compare reviewers:", error)
        return 1
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dataset": "review_v1_cases.json",
        "dataset_sha256": digest,
        "first_answers_sha256": first["answers_sha256"],
        "second_answers_sha256": second["answers_sha256"],
        "metrics": metrics,
        "rows": rows,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"Human agreement: {metrics['same_label']}/{metrics['total']}; "
        f"disagreements: {metrics['disagreements']}; "
        f"cases for adjudication: {metrics['needs_adjudication']}."
    )
    print(
        "Cohen's kappa (descriptive, only 20 authored cases):",
        metrics["cohens_kappa"],
    )
    print("Review these IDs: " + ", ".join(metrics["adjudication_ids"]))
    print("Saved local report:", OUTPUT)
    print("Does not establish ground truth, safety, or independent expertise.")
    print("Next: python -m scripts.adjudicate_reviews --limit 4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
