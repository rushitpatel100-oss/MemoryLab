"""Compare single-pass Qwen proposals with a local replacement evidence gate.

This is a descriptive comparison on synthetic, author-labelled data.
The classifier is called ONCE per pair; the gate does not call Ollama.
No SQLite database is read or written.

Usage:
    python -m scripts.compare_replacement_gate --limit 4
    python -m scripts.compare_replacement_gate
    python -m scripts.compare_replacement_gate --output results/raw/gate.json
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from memory_conflicts import MODEL, classify_pair
from replacement_gate import apply_replacement_gate
from scripts.run_conflict_benchmark import load_cases

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "benchmarks" / "conflict_eval_v1.json"


def compare_cases(cases, classifier=None):
    """Score predictions and the guard on identical model outputs."""
    predict = classifier if classifier is not None else classify_pair
    rows = []
    for case in cases:
        old = {"topic": case["topic"], "fact": case["old_fact"]}
        started = perf_counter()
        predicted = predict(old, case["topic"], case["new_fact"])
        qwen_s = round(perf_counter() - started, 3)
        guarded = apply_replacement_gate(old, case["new_fact"], predicted)
        rows.append({
            "id": case["id"],
            "expected": case["expected"],
            "raw": predicted["relation"],
            "guarded": guarded["relation"],
            "gate_status": guarded["gate"]["status"],
            "raw_reason": predicted["reason"],
            "gate_reason": guarded["gate"]["reason"],
            "infer_seconds": qwen_s,
        })
    return rows


def summarize(rows, method):
    total = len(rows)
    return {
        "matches": sum(x[method] == x["expected"] for x in rows),
        "total": total,
        "false_replacements": sum(
            x[method] == "replaces" and x["expected"] != "replaces"
            for x in rows
        ),
        "true_replacements_retained": sum(
            x[method] == "replaces" and x["expected"] == "replaces"
            for x in rows
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")
    cases = load_cases(CASES)
    if args.limit:
        cases = cases[:args.limit]

    try:
        rows = compare_cases(cases)
    except Exception as error:
        print(f"Classification failed: {error}")
        print("Ensure Ollama is running with qwen2.5:1.5b.")
        return 1
    for row in rows:
        print(
            f"{row['id']}: expected={row['expected']:<9} "
            f"raw={row['raw']:<9} guarded={row['guarded']:<9} "
            f"signal={row['gate_status']}"
        )

    raw = summarize(rows, "raw")
    safe = summarize(rows, "guarded")
    print("\nAuthor-labelled, previously seen synthetic evaluation candidate.")
    print("This is NOT held-out accuracy or proof of a safe memory policy.")
    print(
        f"Single-pass raw matches: {raw['matches']}/{raw['total']}; "
        f"false replacements: {raw['false_replacements']}; "
        f"explicit replacements retained: {raw['true_replacements_retained']}"
    )
    print(
        f"Evidence-gated matches: {safe['matches']}/{safe['total']}; "
        f"false replacements: {safe['false_replacements']}; "
        f"explicit replacements retained: {safe['true_replacements_retained']}"
    )
    print(
        "Shared model inference time:",
        round(sum(r["infer_seconds"] for r in rows), 3),
        "seconds (gate uses no extra Qwen calls)"
    )
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps({
            "created_at": datetime.now(timezone.utc).isoformat(),
            "model": MODEL, "dataset": CASES.name,
            "rows": rows, "raw": raw, "guarded": safe,
        }, indent=2, ensure_ascii=False), encoding="utf-8")
        print("Saved local report:", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
