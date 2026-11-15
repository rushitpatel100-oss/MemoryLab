"""Prospective, label-first diagnostic for MemoryLab's replacement gate.

Before first run:
  python -m scripts.review_eval_cases
  python -m scripts.review_eval_cases --lock

Then (all 20 fictional cases, no partial model-preview mode):
  python -m scripts.evaluate_review_v1

The program refuses unlabeled/unlocked files. It never connects to
SQLite, and compares one Qwen prediction with the guarded result.
"""
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from memory_conflicts import MODEL, RELATIONS, classify_pair
from replacement_gate import apply_replacement_gate
from scripts.review_eval_cases import (
    CASES_FILE, LABELS_FILE, load_cases, load_review,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "results" / "raw" / "review_v1_results.json"


def require_locked_labels(cases, digest, path=LABELS_FILE):
    review = load_review(path, digest, {case["id"] for case in cases})
    if review.get("locked") is not True:
        raise ValueError(
            "Blind labels must be completed and locked before evaluation. "
            "Run: python -m scripts.review_eval_cases --lock"
        )
    if set(review["answers"]) != {c["id"] for c in cases}:
        raise ValueError("Locked file does not cover every case.")
    return {cid: entry["label"] for cid, entry in review["answers"].items()}


def paired_predict(cases, human_labels, classifier=None):
    """Use one Qwen result for both raw and guarded comparisons."""
    predict = classifier if classifier is not None else classify_pair
    rows = []
    for case in cases:
        old = {"topic": case["topic"], "fact": case["old_fact"]}
        started = perf_counter()
        original = predict(old, case["topic"], case["new_fact"])
        elapsed = round(perf_counter() - started, 3)
        guarded = apply_replacement_gate(old, case["new_fact"], original)
        rows.append({
            "id": case["id"], "human_label": human_labels[case["id"]],
            "raw": original["relation"],
            "guarded": guarded["relation"],
            "model_source": original.get("source", "unknown"),
            "gate_status": guarded["gate"]["status"],
            "raw_reason": original["reason"],
            "gate_reason": guarded["gate"]["reason"],
            "qwen_seconds": elapsed,
        })
    return rows


def score(rows, method):
    """Metrics emphasize false supersession and missed genuine updates."""
    labels = sorted(RELATIONS)
    counts = {gold: {pred: 0 for pred in labels} for gold in labels}
    for row in rows:
        gold, pred = row["human_label"], row[method]
        if gold not in RELATIONS or pred not in RELATIONS:
            raise ValueError("An unsupported classification was produced.")
        counts[gold][pred] += 1
    count = len(rows)
    return {
        "matches": sum(row[method] == row["human_label"] for row in rows),
        "cases": count,
        "false_replacements": sum(
            row[method] == "replaces" and row["human_label"] != "replaces"
            for row in rows
        ),
        "coexistence_as_replacements": sum(
            row[method] == "replaces" and row["human_label"] == "coexists"
            for row in rows
        ),
        "genuine_replacements_recognized": sum(
            row[method] == "replaces" and row["human_label"] == "replaces"
            for row in rows
        ),
        "genuine_replacements_missed": sum(
            row[method] != "replaces" and row["human_label"] == "replaces"
            for row in rows
        ),
        "uncertain_suggestions": sum(
            row[method] == "uncertain" for row in rows
        ),
        "confusion": counts,
    }


def run_evaluation(cases, human_labels, classifier=None):
    rows = paired_predict(cases, human_labels, classifier=classifier)
    return rows, {"raw": score(rows, "raw"),
                  "guarded": score(rows, "guarded")}


def main():
    # No --limit option by design: review labels must be frozen first.
    try:
        cases, digest = load_cases()
        labels = require_locked_labels(cases, digest)
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as error:
        print(f"Cannot evaluate yet: {error}")
        return 1

    print(
        f"Review labels locked for {len(cases)} fictional cases. "
        "Running local Qwen once per case."
    )
    try:
        rows, summaries = run_evaluation(cases, labels)
    except Exception as error:
        print(f"Evaluation failed: {error}")
        print("Check that Ollama is running with qwen2.5:1.5b.")
        return 1

    print("\nResults after label lock (not independently adjudicated):")
    for row in rows:
        print(
            f"{row['id']}: human={row['human_label']:<9} "
            f"raw={row['raw']:<9} guarded={row['guarded']:<9} "
            f"gate={row['gate_status']}"
        )
    for name, values in summaries.items():
        print(
            f"\n{name.upper()}: {values['matches']}/{values['cases']} "
            f"agreement with reviewer; false replacements "
            f"{values['false_replacements']}; missed genuine updates "
            f"{values['genuine_replacements_missed']}; "
            f"uncertain suggestions {values['uncertain_suggestions']}"
        )
    print(
        "\nLocal model call distribution:",
        dict(Counter(row["model_source"] for row in rows))
    )
    print("This is a prospective single-reviewer diagnostic, not a verified model accuracy.")

    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "model": MODEL, "dataset": CASES_FILE.name,
        "dataset_sha256": digest, "label_source": LABELS_FILE.name,
        "rows": rows, "metrics": summaries,
        "model_seconds": round(sum(row["qwen_seconds"] for row in rows), 3),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Saved local analysis: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
