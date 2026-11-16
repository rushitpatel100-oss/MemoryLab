"""Diagnose Phase 9 AI review failures without calling Ollama.

Usage: python -m scripts.diagnose_phase9

Reads local results/raw/holdout_v2_ai_review_v3.json. Writes a separate
results/raw/phase9_failure_diagnostics.md. This is a diagnostic of the
reviewer's saved model evidence, NOT a measurement of model accuracy.
No human labels, previous experiments, or SQLite data are changed.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

from scripts.auto_review_v3 import OUTPUT as REVIEW_FILE
from scripts.review_holdout_v2 import load_local_cases

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "results" / "raw" / "phase9_failure_diagnostics.md"
LABELS = {"duplicate", "replaces", "coexists", "uncertain"}
AXES = ("same_entity", "same_attribute", "same_assertion",
        "old_fact_known_obsolete", "new_value_known")
VALUES = {"yes", "no", "unknown"}


def diagnose(cases, digest, report):
    """Count observable failures; do not guess hidden raw model responses."""
    ids = [c["id"] for c in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("Case IDs contain duplicates.")
    if (report.get("dataset_sha256") != digest
            or report.get("reviewer_type") != "automated_llm_not_human"
            or report.get("independent_ground_truth") is not False
            or report.get("policy_version") != "evidence_first_v3"):
        raise ValueError("Not a matching Phase 9 V3 AI review.")
    answers = report.get("answers")
    if not isinstance(answers, dict) or set(answers) != set(ids):
        raise ValueError("All Phase 9 cases must be completed first.")
    labels = Counter()
    flags = Counter()
    evidence_values = {axis: Counter() for axis in AXES}
    missing_old = []
    missing_new = []
    example_rows = []
    for cid in ids:
        entry = answers[cid]
        if not isinstance(entry, dict) or entry.get("provisional_label") not in LABELS:
            raise ValueError("Invalid AI relationship label for " + cid)
        axes = entry.get("axes")
        if not isinstance(axes, dict) or set(AXES) != set(axes):
            raise ValueError("Missing Phase 9 evidence dimensions for " + cid)
        for axis in AXES:
            if axes[axis] not in VALUES:
                raise ValueError("Invalid evidence value for " + cid + ":" + axis)
            evidence_values[axis][axes[axis]] += 1
        labels[entry["provisional_label"]] += 1
        case_flags = entry.get("flags", [])
        if not isinstance(case_flags, list) or any(not isinstance(f, str) for f in case_flags):
            raise ValueError("Invalid warning structure for " + cid)
        flags.update(set(case_flags))
        if not isinstance(entry.get("old_evidence"), str) or not entry["old_evidence"].strip():
            missing_old.append(cid)
        if not isinstance(entry.get("new_evidence"), str) or not entry["new_evidence"].strip():
            missing_new.append(cid)
        example_rows.append({
            "id": cid, "label": entry["provisional_label"],
            "same_assertion": axes["same_assertion"],
            "obsolete": axes["old_fact_known_obsolete"],
            "old_quote_present": cid not in missing_old,
            "new_quote_present": cid not in missing_new,
            "flag_count": len(case_flags),
        })
    return {
        "case_count": len(ids),
        "model": report.get("judge_model", "unrecorded"),
        "distribution": {l: labels[l] for l in
                         ("duplicate", "replaces", "coexists", "uncertain")},
        "flags": dict(flags.most_common()),
        "axes": {a: {v: evidence_values[a][v] for v in
                      ("yes", "no", "unknown")} for a in AXES},
        "missing_old_quotes": missing_old,
        "missing_new_quotes": missing_new,
        "rows": example_rows,
        "status": (
            "All cases abstained. Inspect evidence-quality warnings before "
            "changing prompts, models or policy."
            if labels["uncertain"] == len(ids)
            else "Mixed labels. Review evidence-quality warnings."
        ),
    }


def markdown(stats):
    n = stats["case_count"]
    lines = [
        "# Phase 9 — Saved-evidence failure diagnostics",
        "",
        "**Diagnostic only.** This report analyses saved AI draft evidence "
        "without rerunning Ollama or treating AI output as ground truth.",
        "",
        "- Cases: " + str(n),
        "- Model: " + str(stats["model"]),
        "- Interpretation: " + stats["status"],
        "- Old evidence quote missing/invalid: "
        + str(len(stats["missing_old_quotes"])) + "/" + str(n),
        "- New evidence quote missing/invalid: "
        + str(len(stats["missing_new_quotes"])) + "/" + str(n),
        "",
        "## Relationship distribution",
        "",
        "| Relationship | Count |", "|---|---:|",
    ]
    for label, count in stats["distribution"].items():
        lines.append("| " + label + " | " + str(count) + " |")
    lines += [
        "", "## Evidence axis distribution",
        "", "| Axis | Yes | No | Unknown |", "|---|---:|---:|---:|",
    ]
    for axis, values in stats["axes"].items():
        lines.append(
            "| " + axis + " | " + str(values["yes"])
            + " | " + str(values["no"])
            + " | " + str(values["unknown"]) + " |"
        )
    lines += [
        "", "## Warnings (number of cases)",
        "", "| Warning | Cases |", "|---|---:|",
    ]
    for flag, count in stats["flags"].items():
        lines.append("| " + flag.replace("|", "/") + " | " + str(count) + " |")
    lines += [
        "", "## Every case", "",
        "| ID | Label | Same assertion | Old obsolete | Old quote | New quote | Flags |",
        "|---|---|---|---|---|---|---:|",
    ]
    for r in stats["rows"]:
        lines.append(
            "| " + r["id"] + " | " + r["label"]
            + " | " + r["same_assertion"] + " | " + r["obsolete"]
            + " | " + ("yes" if r["old_quote_present"] else "no")
            + " | " + ("yes" if r["new_quote_present"] else "no")
            + " | " + str(r["flag_count"]) + " |"
        )
    lines += [
        "", "## Interpretation limits",
        "",
        "The Phase 9 output only preserves VALIDATED evidence excerpts and "
        "normalised axes. A missing excerpt could indicate that the LLM returned "
        "none, returned an invented quote, or the strict substring checker "
        "rejected a legitimate paraphrase. This summary cannot distinguish "
        "those causes because the raw Ollama message was not retained.",
        "",
        "Do not claim improvement or degradation in classifier accuracy from "
        "these already-exposed 24 cases. Use a fresh, independently labelled "
        "set for that evaluation. No SQLite contents or historical signoffs "
        "have been altered.",
        "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=REPORT_PATH)
    args = parser.parse_args()
    try:
        cases, digest = load_local_cases()
        report = json.loads(REVIEW_FILE.read_text(encoding="utf-8"))
        stats = diagnose(cases, digest, report)
    except (OSError, ValueError, TypeError) as error:
        print("Cannot diagnose Phase 9:", error)
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        print("Existing diagnosis preserved:", args.output)
        return 1
    with args.output.open("x", encoding="utf-8") as output:
        output.write(markdown(stats))
    print("Saved independent diagnostic:", args.output)
    print(stats["status"])
    print("Old quote missing:", len(stats["missing_old_quotes"]))
    print("New quote missing:", len(stats["missing_new_quotes"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
