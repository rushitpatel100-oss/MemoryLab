"""Compare baseline and staged classifiers on the same synthetic examples.

Run from the repo root:
  python -m scripts.compare_classifiers --limit 4
  python -m scripts.compare_classifiers
  python -m scripts.compare_classifiers --output results/raw/staged_comparison.json

This does not read or modify memorylab.db. It calls local Ollama and may
take longer because the staged model sometimes uses two inference calls.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from memory_conflicts import MODEL, classify_pair
from memory_staged import classify_pair_staged
from scripts.run_conflict_benchmark import load_cases

ROOT = Path(__file__).resolve().parents[1]
EVAL_SET = ROOT / "benchmarks" / "conflict_eval_v1.json"


def evaluate_pair(case, baseline=classify_pair, staged=classify_pair_staged):
    """Compare the two implementations on one identical fictional input."""
    old = {"topic": case["topic"], "fact": case["old_fact"]}
    arguments = (old, case["topic"], case["new_fact"])
    start = perf_counter()
    baseline_result = baseline(*arguments)
    baseline_seconds = round(perf_counter() - start, 3)
    start = perf_counter()
    staged_result = staged(*arguments)
    staged_seconds = round(perf_counter() - start, 3)
    return {
        "id": case["id"],
        "expected": case["expected"],
        "baseline": baseline_result["relation"],
        "baseline_source": baseline_result.get("source", "unknown"),
        "baseline_seconds": baseline_seconds,
        "staged": staged_result["relation"],
        "staged_source": staged_result.get("source", "unknown"),
        "staged_seconds": staged_seconds,
        "staged_trace": staged_result.get("stages", []),
        "baseline_reason": baseline_result["reason"],
        "staged_reason": staged_result["reason"],
    }


def score(rows, method):
    correct = sum(x[method] == x["expected"] for x in rows)
    # The most dangerous mismatch for this app is suggesting supersession
    # when the supplied expected label is not "replaces".
    false_replacements = sum(
        x[method] == "replaces" and x["expected"] != "replaces" for x in rows
    )
    coexists_as_replaces = sum(
        x[method] == "replaces" and x["expected"] == "coexists"
        for x in rows
    )
    return {
        "matches": correct, "total": len(rows),
        "false_replacements": false_replacements,
        "coexists_as_replaces": coexists_as_replaces,
        "elapsed_seconds": round(
            sum(x[f"{method}_seconds"] for x in rows), 3
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")
    cases = load_cases(EVAL_SET)
    if args.limit:
        cases = cases[:args.limit]
    rows = []
    for case in cases:
        try:
            outcome = evaluate_pair(case)
        except Exception as error:
            print(f"Stopped at {case['id']}: {error}")
            print("Ensure Ollama and qwen2.5:1.5b are running locally.")
            return 1
        rows.append(outcome)
        print(
            f"{case['id']}: expected={case['expected']:<9} "
            f"baseline={outcome['baseline']:<9} staged={outcome['staged']:<9} "
            f"baseline_s={outcome['baseline_seconds']:.2f} "
            f"staged_s={outcome['staged_seconds']:.2f}"
        )

    base = score(rows, "baseline")
    alternative = score(rows, "staged")
    print("\nAuthor-labelled fictional evaluation candidate; NOT held-out accuracy.")
    print(
        f"Baseline matches: {base['matches']}/{base['total']}; "
        f"false replacements: {base['false_replacements']}; "
        f"coexistence false replacements: {base['coexists_as_replaces']}; "
        f"total runtime: {base['elapsed_seconds']}s"
    )
    print(
        f"Staged matches:   {alternative['matches']}/{alternative['total']}; "
        f"false replacements: {alternative['false_replacements']}; "
        f"coexistence false replacements: {alternative['coexists_as_replaces']}; "
        f"total runtime: {alternative['elapsed_seconds']}s"
    )
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps({
            "created_at": datetime.now(timezone.utc).isoformat(),
            "model": MODEL,
            "dataset": EVAL_SET.name,
            "rows": rows,
            "baseline": base,
            "staged": alternative,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Wrote local JSON:", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
