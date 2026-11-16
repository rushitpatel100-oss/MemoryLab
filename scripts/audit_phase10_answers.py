"""Audit saved Phase 10 semantic answers without rerunning Ollama.

Read a complete *project-authored synthetic* semantic development run and
separate lost memory evidence, lost retrieval support, literal-keyword
mismatches, and answers supplied where the authored check expects abstention.
A flagged specific answer is NOT automatically proved wrong on arbitrary
datasets; a keyword match is NOT independently verified correctness.

Usage:
    python -m scripts.audit_phase10_answers

Input:  results/raw/phase10_semantic_reviewed.json
Output: results/raw/phase10_semantic_reviewed_audit.md and .json

No model calls, no personal SQLite data, no changes to the input file.
"""
import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from scripts.evaluate_downstream_memory import (
    RAW_DIR, load_dataset, is_abstention,
)

DEFAULT_SOURCE = RAW_DIR / "phase10_semantic_reviewed.json"
STATUSES = (
    "lexical_match_unverified",
    "wording_mismatch_needs_review",
    "unexpected_specific_answer",
    "expected_abstention_detected",
    "storage_support_missing",
    "retrieval_support_missing",
)
EXPLANATIONS = {
    "lexical_match_unverified":
        "Author keyword found; this does NOT verify semantic correctness.",
    "wording_mismatch_needs_review":
        "No author keyword match; paraphrase or incorrect answer possible.",
    "unexpected_specific_answer":
        "The authored scenario expects abstention, but Qwen gave a specific answer.",
    "expected_abstention_detected":
        "Detected an abstention phrase; inspect for contradictory claims too.",
    "storage_support_missing":
        "The required supporting fact was not active in SQLite.",
    "retrieval_support_missing":
        "The supporting fact was saved but not among selected memories.",
}


def triage(check):
    """Only flags possible failures; never invents human truth labels."""
    if not isinstance(check, dict):
        raise ValueError("Malformed question record.")
    answer = check.get("answer")
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("Saved answer text is missing.")
    if not isinstance(check.get("text_proxy_pass"), bool):
        raise ValueError("A recorded boolean text proxy is required.")
    abstention = check.get("expect_abstention")
    if not isinstance(abstention, bool):
        raise ValueError("Invalid authored answerability flag.")
    stored, retrieved = check.get("support_available"), check.get("support_retrieved")
    if stored not in (True, False, None) or retrieved not in (True, False, None):
        raise ValueError("Invalid evidence-availability marker.")
    if abstention:
        return ("expected_abstention_detected" if is_abstention(answer)
                else "unexpected_specific_answer")
    if stored is False:
        return "storage_support_missing"
    if retrieved is False:
        return "retrieval_support_missing"
    return ("lexical_match_unverified" if check["text_proxy_pass"]
            else "wording_mismatch_needs_review")


def audit_run(data, benchmark, digest):
    if (
        not isinstance(data, dict)
        or data.get("version") != 1
        or data.get("method") != "project_authored_semantic_development_not_accuracy"
        or data.get("dataset_sha256") != digest
        or data.get("policy") != "reviewed"
        or data.get("embedding") != "all-minilm"
        or data.get("top_k") != 3
        or data.get("minimum") != 0.25
    ):
        raise ValueError("Not the matching Phase 10 reviewed-semantic run.")
    results = data.get("results")
    expected_keys = {s["id"] + "_reviewed" for s in benchmark["scenarios"]}
    if not isinstance(results, dict) or set(results) != expected_keys:
        raise ValueError("A complete, matching reviewed run is required.")
    rows = []
    exact = 0
    for case in benchmark["scenarios"]:
        key = case["id"] + "_reviewed"
        scenario = results[key]
        if (
            not isinstance(scenario, dict)
            or scenario.get("scenario") != case["id"]
            or scenario.get("policy") != "reviewed"
            or scenario.get("expected_active_steps") != case["expected_active"]
            or not isinstance(scenario.get("checks"), list)
            or len(scenario["checks"]) != len(case["checks"])
        ):
            raise ValueError("Scenario identity/shape mismatch: " + key)
        if scenario.get("exact_active_state") is True:
            exact += 1
        observed = {q["id"]: q for q in scenario["checks"]}
        if len(observed) != len(case["checks"]):
            raise ValueError("Duplicated question IDs in " + key)
        for original in case["checks"]:
            q = observed.get(original["id"])
            if not isinstance(q, dict):
                raise ValueError("Missing question: " + key + "/" + original["id"])
            if (
                q.get("question") != original["question"]
                or q.get("expect_abstention") != original.get("expect_abstention", False)
                or q.get("expected_phrases", []) != original.get("expected_phrases", [])
                or q.get("support_steps") != original["support_steps"]
            ):
                raise ValueError("Question/expectation changed: " + key + "/" + original["id"])
            status = triage(q)
            rows.append({
                "scenario": case["id"],
                "title": case["title"],
                "id": q["id"],
                "question": q["question"],
                "answer": q["answer"],
                "expected_phrases": q.get("expected_phrases", []),
                "expect_abstention": q["expect_abstention"],
                "support_available": q["support_available"],
                "support_retrieved": q["support_retrieved"],
                "text_proxy_pass": q["text_proxy_pass"],
                "triage": status,
                "explanation": EXPLANATIONS[status],
            })
    counts = Counter(row["triage"] for row in rows)
    return {
        "scenarios": len(benchmark["scenarios"]),
        "questions": len(rows),
        "exact_memory_states": exact,
        "supported_questions": sum(r["support_available"] is not None for r in rows),
        "stored_support": sum(r["support_available"] is True for r in rows),
        "retrieved_support": sum(r["support_retrieved"] is True for r in rows),
        "lexical_passes": sum(r["text_proxy_pass"] for r in rows),
        "counts": {status: counts[status] for status in STATUSES},
        "flagged": [r for r in rows if r["triage"] in (
            "wording_mismatch_needs_review", "unexpected_specific_answer",
            "storage_support_missing", "retrieval_support_missing"
        )],
        "rows": rows,
        "provenance": (
            "AI-generated answer audit on project-authored synthetic data. "
            "No independent human annotation, no autonomous classifier "
            "accuracy, and no semantic verification of all answers."
        ),
    }


def markdown(audit, source_sha):
    lines = [
        "# Phase 10 — Semantic answer quality audit",
        "",
        "**AI-assisted diagnostic on project-authored scenarios. "
        "NOT independent human accuracy or verified model accuracy.**",
        "",
        "- Input AI-run file SHA-256: " + source_sha,
        "- Scenarios: " + str(audit["scenarios"]),
        "- Questions: " + str(audit["questions"]),
        "- Exact authored memory states: " + str(audit["exact_memory_states"])
        + "/" + str(audit["scenarios"]),
        "- Author-defined answer supports stored: " + str(audit["stored_support"])
        + "/" + str(audit["supported_questions"]),
        "- Author-defined supports retrieved: " + str(audit["retrieved_support"])
        + "/" + str(audit["supported_questions"]),
        "- Literal keyword/abstention proxy matches: "
        + str(audit["lexical_passes"]) + "/" + str(audit["questions"]),
        "",
        "## Automated triage categories",
        "",
        "| Category | Count |", "|---|---:|",
    ]
    for category, count in audit["counts"].items():
        lines.append("| " + category + " | " + str(count) + " |")
    lines += [
        "", "## Items needing semantic inspection",
        "",
        "The categories flag problems **for inspection**, not independent "
        "decisions on correctness. In particular, a keyword mismatch "
        "may be a valid paraphrase, whereas an unsupported answer can "
        "look fluent even when a matching source was retrieved.",
        "",
    ]
    if not audit["flagged"]:
        lines += ["No automated flags; this does not prove accuracy.", ""]
    for row in audit["flagged"]:
        lines += [
            "### " + row["scenario"] + " / " + row["id"] + " — " + row["triage"],
            "",
            "**Question:** " + row["question"],
            "",
            "**Answer:** " + row["answer"].replace("\n", " "),
            "",
            "**Expected author keywords:** "
            + (", ".join(row["expected_phrases"]) or "(expect abstention)"),
            "",
            "**Stored / retrieved support:** " + str(row["support_available"])
            + " / " + str(row["support_retrieved"]),
            "",
            "**Why flagged:** " + row["explanation"],
            "",
        ]
    lines += [
        "## Research limits and next step", "",
        "The numeric categories are reproducible checks based on project-authored "
        "expected phrases and answerability. Human semantic adjudication "
        "is still needed before assigning verified correct/incorrect labels. "
        "A text-proxy pass can hide a false claim; a text-proxy failure may "
        "just reflect wording. An expected-abstention failure is a serious "
        "reason to inspect unsupported specifics, but this is not a general "
        "entailment checker.", "",
        "The current reviewed-policy run does not assess the autonomous Qwen "
        "conflict classifier. Its selective storage decisions were supplied "
        "by the fictional fixture. The next experiment should explicitly "
        "compare evidence-requiring/abstention-first answer generation "
        "against the unchanged Qwen baseline, keeping the original outputs "
        "frozen and evaluating with new independent examples.", "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    args = parser.parse_args()
    try:
        benchmark, digest = load_dataset()
        raw = args.source.read_bytes()
        source = json.loads(raw)
        result = audit_run(source, benchmark, digest)
    except (OSError, ValueError, TypeError, KeyError) as err:
        print("Cannot audit Phase 10:", err)
        return 1
    prefix = args.source.with_suffix("")
    json_out = prefix.with_name(prefix.name + "_audit.json")
    md_out = prefix.with_name(prefix.name + "_audit.md")
    if json_out.exists() or md_out.exists():
        print("Existing audit preserved; refusing to overwrite:", md_out)
        return 1
    hash_value = hashlib.sha256(raw).hexdigest()
    result["source_sha256"] = hash_value
    result["created_at"] = datetime.now(timezone.utc).isoformat()
    json_out.parent.mkdir(parents=True, exist_ok=True)
    with json_out.open("x", encoding="utf-8") as out:
        json.dump(result, out, indent=2, ensure_ascii=False)
        out.write("\n")
    with md_out.open("x", encoding="utf-8") as out:
        out.write(markdown(result, hash_value))
    print("Saved audit:", md_out)
    print("Audit counts:", result["counts"])
    print("No existing AI results or SQLite memories changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
