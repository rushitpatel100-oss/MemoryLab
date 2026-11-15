"""Phase 8: prospective paired evaluation on *human-consensus cases only*.

Must be run ONLY AFTER both A and B have finished and locked all 24 cases.
No evaluation preview, no output before label lock, and no SQLite access.

Usage: python -m scripts.evaluate_holdout_v2

The original single-pass Qwen classifier is called once per case. The
unchanged evidence gate post-processes that SAME result; never twice.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from memory_conflicts import MODEL
from scripts.evaluate_review_v1 import paired_predict, score
from scripts.review_holdout_v2 import (
    REVIEW_PATHS, consistency_warnings, load_local_cases, load_rater,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "results" / "raw" / "holdout_v2_results.json"


def require_frozen_reviews(cases, digest, loader=load_rater):
    """Reject any missing, incomplete, or inconsistent human review."""
    ids = {case["id"] for case in cases}
    first, second = (loader(rater, cases, digest) for rater in ("A", "B"))
    for rater, review in (("A", first), ("B", second)):
        if review.get("locked") is not True:
            raise ValueError(
                f"Reviewer {rater} must finish and lock all cases first."
            )
        if set(review.get("answers", {})) != ids:
            raise ValueError(f"Reviewer {rater} has incomplete labels.")
        for cid, entry in review["answers"].items():
            issues = consistency_warnings(entry)
            if issues:
                raise ValueError(f"Reviewer {rater}, {cid}: " + "; ".join(issues))
    return first, second


def consensus_labels(cases, first, second):
    """Use only identical human labels as provisional scoring targets."""
    labels = {}
    disagreements = []
    for case in cases:
        cid = case["id"]
        a = first["answers"][cid]["label"]
        b = second["answers"][cid]["label"]
        if a == b:
            labels[cid] = a
        else:
            labels[cid] = None
            disagreements.append({"id": cid, "rater_A": a, "rater_B": b})
    return labels, disagreements


def evaluate_cases(cases, first, second, classifier=None):
    """Share model outputs; do not count unresolved disagreement as truth."""
    labels, disagreements = consensus_labels(cases, first, second)
    rows = paired_predict(cases, labels, classifier=classifier)
    agreed_rows = [row for row in rows if row["human_label"] is not None]
    stats = {
        "raw": score(agreed_rows, "raw"),
        "guarded": score(agreed_rows, "guarded"),
    }
    return rows, stats, disagreements


def main():
    try:
        cases, digest = load_local_cases()
        first, second = require_frozen_reviews(cases, digest)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
        print("Not ready to evaluate:", error)
        print("Complete and lock both independent reviews first.")
        return 1
    if OUTPUT.exists():
        print("Result file already exists; refusing to overwrite:", OUTPUT)
        print("Preserve previous runs rather than cherry-picking results.")
        return 1
    print(
        f"Both reviewers locked {len(cases)} fictional cases. "
        "Running one local Qwen call per case; the gate is deterministic."
    )
    try:
        rows, stats, disagreements = evaluate_cases(cases, first, second)
    except Exception as error:
        print("Model evaluation failed:", error)
        print("Check that local Ollama and qwen2.5:1.5b are running.")
        return 1
    agreed = len(cases) - len(disagreements)
    print(
        f"Human label agreement: {agreed}/{len(cases)}; "
        f"disputed cases not included in agreement scores: "
        f"{len(disagreements)}"
    )
    for method in ("raw", "guarded"):
        s = stats[method]
        print(
            f"{method}: {s['matches']}/{s['cases']} consensus agreement, "
            f"{s['false_replacements']} false replacement suggestions, "
            f"{s['genuine_replacements_missed']} missed supported updates, "
            f"{s['uncertain_suggestions']} uncertain recommendations"
        )
    output = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "model": MODEL,
        "dataset": "holdout_v2_cases.json",
        "dataset_sha256": digest,
        "review_A_answers_sha256": first["answers_sha256"],
        "review_B_answers_sha256": second["answers_sha256"],
        "consensus_count": agreed,
        "disagreement_count": len(disagreements),
        "disagreements": disagreements,
        "metrics_consensus_only": stats,
        "rows": rows,
        "model_seconds": round(sum(row["qwen_seconds"] for row in rows), 3),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive create avoids silently replacing the original experiment.
    with OUTPUT.open("x", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print("Saved one frozen local run:", OUTPUT)
    print(
        "Consensus is not independently verified truth. "
        "Do not tune the gate on these examples and call them held out."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
