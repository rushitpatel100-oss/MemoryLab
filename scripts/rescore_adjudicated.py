"""Re-score frozen Experiment 010 predictions using later adjudicated labels.

No Qwen inference, SQLite reads/writes, or edits of either input JSON.

Run from the MemoryLab repository root after the adjudication export:
  python -m scripts.rescore_adjudicated
"""
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "results" / "raw" / "review_v1_results.json"
ADJUDICATED = ROOT / "results" / "raw" / "review_v1_adjudicated_summary.json"
OUTPUT = ROOT / "results" / "raw" / "review_v1_adjudicated_metrics.json"
LABELS = {"duplicate", "coexists", "replaces", "uncertain"}


def unique_rows(rows, kind):
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{kind} must contain nonempty rows.")
    if any(not isinstance(row, dict) or not isinstance(row.get("id"), str)
           for row in rows):
        raise ValueError(f"{kind} contains invalid case IDs.")
    ids = [row["id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{kind} contains repeated case IDs.")
    return {row["id"]: row for row in rows}


def metrics(rows, label_key, method):
    """Count reviewer agreement, false replacements, and withheld updates."""
    checked = [r for r in rows if r[label_key] is not None]
    return {
        "matches": sum(r[method] == r[label_key] for r in checked),
        "cases": len(checked),
        "false_replacements": sum(
            r[method] == "replaces" and r[label_key] != "replaces"
            for r in checked
        ),
        "recognized_replacements": sum(
            r[method] == "replaces" and r[label_key] == "replaces"
            for r in checked
        ),
        "missed_replacements": sum(
            r[method] != "replaces" and r[label_key] == "replaces"
            for r in checked
        ),
        "uncertain_suggestions": sum(
            r[method] == "uncertain" for r in checked
        ),
    }


def compare_reports(original, adjudicated):
    """Return a descriptive, versioned re-score; leave raw predictions intact."""
    if (not original.get("dataset_sha256") or
            original.get("dataset_sha256") != adjudicated.get("dataset_sha256")):
        raise ValueError("Dataset fingerprints differ; cannot compare.")
    first = unique_rows(original.get("rows"), "Experiment 010")
    second = unique_rows(adjudicated.get("rows"), "Adjudication")
    if set(first) != set(second):
        raise ValueError("Case IDs differ between the two exports.")
    combined = []
    for cid in sorted(first):
        r, a = first[cid], second[cid]
        if r.get("human_label") != a.get("first_label"):
            raise ValueError(f"Original human label mismatch for {cid}.")
        for key in ("human_label", "raw", "guarded"):
            if r.get(key) not in LABELS:
                raise ValueError(f"Invalid {key} value in {cid}.")
        if a.get("second_label") not in LABELS:
            raise ValueError(f"Invalid second reviewer label in {cid}.")
        if a.get("status") not in (
            "adjudicated", "agreed_not_adjudicated", "deferred"
        ):
            raise ValueError(f"Invalid adjudication status in {cid}.")
        label = a.get("final_label")
        if a["status"] == "deferred":
            if label is not None:
                raise ValueError(f"Deferred case {cid} must not have a final label.")
        elif label not in LABELS:
            raise ValueError(f"Missing final label for {cid}.")
        if a["status"] == "agreed_not_adjudicated" and (
            a["first_label"] != a["second_label"] or
            label != a["first_label"]
        ):
            raise ValueError(f"Unadjudicated agreement is inconsistent: {cid}.")
        combined.append({
            "id": cid,
            "initial_label": r["human_label"],
            "final_label": label,
            "status": a["status"],
            "raw": r["raw"],
            "guarded": r["guarded"],
        })
    results = {}
    for labels, key in (("initial", "initial_label"),
                        ("adjudicated", "final_label")):
        results[labels] = {
            method: metrics(combined, key, method)
            for method in ("raw", "guarded")
        }
    return {
        "dataset_sha256": original["dataset_sha256"],
        "cases": len(combined),
        "adjudicated_cases": sum(r["status"] == "adjudicated" for r in combined),
        "unexamined_agreements": sum(
            r["status"] == "agreed_not_adjudicated" for r in combined
        ),
        "deferred_cases": sum(r["status"] == "deferred" for r in combined),
        "first_second_agreement": sum(
            first[r["id"]]["human_label"] == second[r["id"]]["second_label"]
            for r in combined
        ),
        "label_changes": [
            {"id": r["id"], "before": r["initial_label"],
             "after": r["final_label"]}
            for r in combined if r["final_label"] is not None
            and r["initial_label"] != r["final_label"]
        ],
        "metrics": results,
    }


def main():
    try:
        original = json.loads(RAW.read_text(encoding="utf-8"))
        adjudicated = json.loads(ADJUDICATED.read_text(encoding="utf-8"))
        result = compare_reports(original, adjudicated)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("Cannot rescore:", error)
        print("Keep both original JSON files unchanged under results/raw/.")
        return 1
    result["computed_at"] = datetime.now(timezone.utc).isoformat()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("Original predictions reused; no Ollama or database access.")
    print(
        "First/second reviewer agreement:",
        f"{result['first_second_agreement']}/{result['cases']}"
    )
    for stage, stats in result["metrics"].items():
        for method, counts in stats.items():
            print(
                f"{stage} {method}: {counts['matches']}/{counts['cases']} "
                f"matches; false replacements {counts['false_replacements']}; "
                f"missed genuine replacements {counts['missed_replacements']}"
            )
    print("Adjudication label changes:", result["label_changes"])
    print("Local report:", OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
