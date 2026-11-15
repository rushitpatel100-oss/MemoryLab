"""Run a small, local-only four-label memory conflict development benchmark.

Usage:
    python -m scripts.run_conflict_benchmark --limit 4
    python -m scripts.run_conflict_benchmark
    python -m scripts.run_conflict_benchmark --output results/raw/conflicts.json

By default results are printed only. Do not publish personal data exports.
"""
import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from memory_conflicts import MODEL, RELATIONS, classify_pair

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "benchmarks" / "conflict_cases.json"


def load_cases(path=DEFAULT_CASES):
    cases = json.loads(Path(path).read_text(encoding="utf-8"))["cases"]
    if not isinstance(cases, list) or not cases:
        raise ValueError("Benchmark requires a nonempty list of cases.")
    required = {"id", "expected", "topic", "old_fact", "new_fact"}
    for case in cases:
        if not isinstance(case, dict) or not required.issubset(case):
            raise ValueError("Each case needs id, expected, topic, old_fact, new_fact.")
        if case["expected"] not in RELATIONS:
            raise ValueError(f"Unsupported label in {case['id']}.")
    return cases


def run_cases(cases, classifier=classify_pair):
    """Classify each pair without reading or changing the SQLite database."""
    results = []
    for case in cases:
        start = perf_counter()
        proposal = classifier(
            {"topic": case["topic"], "fact": case["old_fact"]},
            case["topic"], case["new_fact"]
        )
        results.append({
            "id": case["id"],
            "expected": case["expected"],
            "predicted": proposal["relation"],
            "reason": proposal["reason"],
            "source": proposal.get("source", "unknown"),
            "elapsed_seconds": round(perf_counter() - start, 3),
            "correct": proposal["relation"] == case["expected"],
        })
    return results


def summarize(results):
    if not results:
        raise ValueError("There are no results to score.")
    labels = sorted(RELATIONS)
    matrix = {expected: {predicted: 0 for predicted in labels}
              for expected in labels}
    correct = 0
    for row in results:
        if row["expected"] not in RELATIONS or row["predicted"] not in RELATIONS:
            raise ValueError("The benchmark encountered an invalid label.")
        matrix[row["expected"]][row["predicted"]] += 1
        correct += int(row["correct"])
    return {
        "total": len(results), "correct": correct,
        "accuracy": round(correct / len(results), 4),
        "confusion": matrix,
        "sources": dict(Counter(r["source"] for r in results)),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None,
                        help="Run only the first N balanced development cases.")
    parser.add_argument("--output", default=None,
                        help="Optional report path, preferably under results/raw/.")
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive.")
    cases = load_cases()
    if args.limit is not None:
        cases = cases[:args.limit]
    try:
        results = run_cases(cases)
    except Exception as exc:
        print(f"Benchmark stopped: {exc}")
        print("Check that Ollama is running with qwen2.5:1.5b installed.")
        return 1

    summary = summarize(results)
    for row in results:
        status = "PASS" if row["correct"] else "MISS"
        print(
            f"{row['id']}: expected={row['expected']:<9} "
            f"predicted={row['predicted']:<9} {status} "
            f"({row['source']}, {row['elapsed_seconds']}s)"
        )
    print(f"\nDevelopment-label agreement: "
          f"{summary['correct']}/{summary['total']} "
          "(NOT held-out model accuracy)")
    print("Classifier sources:", summary["sources"])
    labels = sorted(RELATIONS)
    print("Confusion counts (rows expected; columns predicted):")
    print("expected/predicted " + " ".join(f"{x:>10}" for x in labels))
    for label in labels:
        counts = summary["confusion"][label]
        print(f"{label:<18} " + " ".join(f"{counts[p]:>10}" for p in labels))
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps({
            "created_at": datetime.now(timezone.utc).isoformat(),
            "model": MODEL,
            "dataset": DEFAULT_CASES.name,
            "results": results,
            "summary": summary,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Saved local report:", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
