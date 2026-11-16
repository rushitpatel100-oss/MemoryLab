"""Phase 11 experiment: evidence-required answer generation.

Compare a NEW extractive answer mode against the saved, unchanged
Phase 10 semantic answer run on the same project-authored fictional
examples. This is a development diagnostic, NOT a blind accuracy test.

    python -m scripts.evaluate_answer_evidence --limit 3
    python -m scripts.evaluate_answer_evidence

Reads the old baseline only for comparing after completing a new run.
New files: results/raw/phase11_extractive_reviewed.json/.md and
results/raw/phase11_evidence_comparison.md. Never overwrites past runs,
calls no personal-memory database and makes no conflict policy decisions.
"""
import argparse
import hashlib
import json
from pathlib import Path

from answer_evidence import generate_extractive_answer
from answer_generator import DEFAULT_CHAT_MODEL, NO_MEMORY_ANSWER
from scripts.evaluate_downstream_memory import RAW_DIR, load_dataset
from scripts.evaluate_semantic_outcomes import (
    load_saved, run_all_semantic,
)
from scripts.review_eval_cases import save_review

BASELINE = RAW_DIR / "phase10_semantic_reviewed.json"
EXPERIMENT = RAW_DIR / "phase11_extractive_reviewed.json"
COMPARISON = RAW_DIR / "phase11_evidence_comparison.md"
MODE = "extractive_evidence_v1"


def compare(data, baseline, candidate):
    """Compare behavior only; neither result is an independent accuracy label."""
    cases = data["scenarios"]
    keys = {c["id"] + "_reviewed" for c in cases}
    for title, report in (("baseline", baseline), ("candidate", candidate)):
        if not isinstance(report.get("results"), dict) or set(report["results"]) != keys:
            raise ValueError(title + ": incomplete scenarios.")
        if (
            report.get("policy") != "reviewed"
            or report.get("embedding") != "all-minilm"
            or report.get("top_k") != 3
            or report.get("minimum") != 0.25
        ):
            raise ValueError(title + ": different retrieval configuration.")
    if baseline.get("dataset_sha256") != candidate.get("dataset_sha256"):
        raise ValueError("Baseline and candidate are for different datasets.")
    if baseline.get("model") != candidate.get("model"):
        raise ValueError("Answer model changed between comparison runs.")
    if candidate.get("answer_mode") != MODE:
        raise ValueError("Candidate provenance/mode missing.")
    rows = []
    for case in cases:
        cid = case["id"]
        a = baseline["results"][cid + "_reviewed"]["checks"]
        b = candidate["results"][cid + "_reviewed"]["checks"]
        if len(a) != len(case["checks"]) or len(b) != len(a):
            raise ValueError("Question count mismatch: " + cid)
        for expected, old, new in zip(case["checks"], a, b):
            if (
                old["id"] != expected["id"] or new["id"] != expected["id"]
                or old["question"] != new["question"]
                or old["question"] != expected["question"]
            ):
                raise ValueError("Different question identities: " + cid)
            rows.append({
                "case": cid, "question_id": expected["id"],
                "question": expected["question"],
                "expect_abstention": expected.get("expect_abstention", False),
                "baseline": old["answer"],
                "extractive": new["answer"],
                "baseline_proxy": old["text_proxy_pass"],
                "extractive_proxy": new["text_proxy_pass"],
                "baseline_abstained": old["answer"].strip() == NO_MEMORY_ANSWER,
                "extractive_abstained": new["answer"].strip() == NO_MEMORY_ANSWER,
                "baseline_support_retrieved": old["support_retrieved"],
                "extractive_support_retrieved": new["support_retrieved"],
            })
    return {
        "scenarios": len(cases),
        "questions": len(rows),
        "baseline_text_proxy": sum(r["baseline_proxy"] for r in rows),
        "extractive_text_proxy": sum(r["extractive_proxy"] for r in rows),
        "baseline_unanswered": sum(r["baseline_abstained"] for r in rows),
        "extractive_unanswered": sum(r["extractive_abstained"] for r in rows),
        "baseline_unsupported_answer_events": sum(
            r["expect_abstention"] and not r["baseline_abstained"]
            for r in rows
        ),
        "extractive_unsupported_answer_events": sum(
            r["expect_abstention"] and not r["extractive_abstained"]
            for r in rows
        ),
        "extractive_abstentions_on_answerable_checks": sum(
            not r["expect_abstention"] and r["extractive_abstained"]
            for r in rows
        ),
        "rows": rows,
    }


def markdown(result, old_sha, new_sha):
    lines = [
        "# Phase 11 — Baseline vs extractive-evidence answers",
        "",
        "**Exploratory, previously exposed fictional development cases. NOT "
        "blind accuracy or independent human verification.**",
        "",
        "- Old Phase 10 JSON SHA-256: " + old_sha,
        "- New extractive JSON SHA-256: " + new_sha,
        "- Scenarios: " + str(result["scenarios"]),
        "- Questions: " + str(result["questions"]),
        "- Baseline literal-answer proxy: " + str(result["baseline_text_proxy"]),
        "- Extractive literal-answer proxy: " + str(result["extractive_text_proxy"]),
        "- Baseline abstentions: " + str(result["baseline_unanswered"]),
        "- Extractive abstentions: " + str(result["extractive_unanswered"]),
        "- Baseline specific replies on authored-unanswerable questions: "
        + str(result["baseline_unsupported_answer_events"]),
        "- Extractive specific replies on authored-unanswerable questions: "
        + str(result["extractive_unsupported_answer_events"]),
        "- Extractive abstentions on authored-answerable questions: "
        + str(result["extractive_abstentions_on_answerable_checks"]),
        "",
        "## Case-by-case answers",
        "",
        "| ID | Question | Old baseline answer | Extractive answer | "
        "Old proxy | New proxy |",
        "|---|---|---|---|---|---|",
    ]
    for r in result["rows"]:
        cells = [
            r["case"] + " " + r["question_id"],
            r["question"], r["baseline"], r["extractive"],
            str(r["baseline_proxy"]), str(r["extractive_proxy"])
        ]
        lines.append("| " + " | ".join(
            str(s).replace("|", "/").replace("\n", " ")[:350]
            for s in cells
        ) + " |")
    lines += [
        "", "## Critical validity limitations", "",
        "Extractive quotes and spans are validated against a matching memory "
        "ID, but a true quote can STILL be irrelevant to the question, and "
        "a model may extract an old value when asked for the new value. "
        "An increase in abstention may prevent unsupported guesses but can "
        "lose legitimate answers. The evaluation uses author-defined "
        "phrases and is not semantic truth adjudication.",
        "",
        "No old saved AI answer, original human signoff, source dataset, "
        "or personal SQLite memory was changed. Evaluate a new independent "
        "set and audit the model's explanations before production adoption.",
        "",
    ]
    return "\n".join(lines)


def run_and_compare(*, limit=None, model=DEFAULT_CHAT_MODEL,
                    answer_fn=generate_extractive_answer, ranker=None,
                    log=print):
    data, digest = load_dataset()
    kwargs = {}
    if ranker is not None:
        kwargs["ranker"] = ranker
    state = run_all_semantic(
        data, digest, "reviewed", output=EXPERIMENT,
        model=model, limit=limit, answer_fn=answer_fn,
        **kwargs
    )
    if "answer_mode" not in state:
        state["answer_mode"] = MODE
        save_review(state, EXPERIMENT)
    elif state["answer_mode"] != MODE:
        raise ValueError("Existing answer-mode provenance does not match.")
    if len(state["results"]) != len(data["scenarios"]):
        log(f"Experiment progress: {len(state['results'])}/{len(data['scenarios'])}")
        return state
    if COMPARISON.exists():
        log("Existing Phase 11 comparison preserved: " + str(COMPARISON))
        return state
    if not BASELINE.exists():
        log("Baseline Phase 10 JSON missing; candidate output still saved.")
        return state
    raw_old, raw_new = BASELINE.read_bytes(), EXPERIMENT.read_bytes()
    previous = json.loads(raw_old)
    current = json.loads(raw_new)
    diff = compare(data, previous, current)
    COMPARISON.parent.mkdir(parents=True, exist_ok=True)
    with COMPARISON.open("x", encoding="utf-8") as out:
        out.write(markdown(
            diff, hashlib.sha256(raw_old).hexdigest(),
            hashlib.sha256(raw_new).hexdigest()
        ))
    log("Saved comparison: " + str(COMPARISON))
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=DEFAULT_CHAT_MODEL)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive.")
    try:
        print("Testing local EXTRACTIVE evidence answers, not changing app.py.")
        state = run_and_compare(limit=args.limit, model=args.model)
        print(f"Completed {len(state['results'])}/14 fictional scenarios.")
        print("Results:", EXPERIMENT)
        print("These are project-authored development diagnostics, NOT accuracy.")
        return 0
    except (OSError, ValueError, TypeError, KeyError) as error:
        print("Phase 11 experiment stopped:", error)
        print("Completed new scenarios are saved. Rerun to resume.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
