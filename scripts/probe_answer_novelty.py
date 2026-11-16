"""Phase 12: diagnostic screening for novel factual claims in saved Qwen answers.

This is NOT an entailment checker or a model accuracy score. It only
identifies certain tokens/days/numbers present in the answer but absent
from RETRIEVED evidence. Words that already appear in an old value can
still be used incorrectly when a question asks for the new value.

Runs OFFLINE on the original Phase 10 semantic JSON, without rerunning
a model or accessing the user's database:
    python -m scripts.probe_answer_novelty

Inputs remain untouched. Reports under Git-ignored results/raw/.
The previously exposed synthetic examples are NOT a blind evaluation.
"""
import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from answer_generator import NO_MEMORY_ANSWER
from scripts.evaluate_downstream_memory import RAW_DIR, load_dataset

SOURCE = RAW_DIR / "phase10_semantic_reviewed.json"
REPORT = RAW_DIR / "phase12_answer_novelty_probe.md"
JSON_REPORT = RAW_DIR / "phase12_answer_novelty_probe.json"

WEEKDAYS = frozenset(
    ("monday", "tuesday", "wednesday", "thursday", "friday",
     "saturday", "sunday")
)
NUMBER_WORDS = {
    # "one" is often anaphoric ("the blue one"), not a quantity.
    # Treat it as a normal word to prevent false unsupported-number flags.
    "zero": "0", "two": "2", "three": "3",
    "four": "4", "five": "5", "six": "6", "seven": "7",
    "eight": "8", "nine": "9", "ten": "10", "eleven": "11",
    "twelve": "12", "thirteen": "13", "fourteen": "14",
    "fifteen": "15", "sixteen": "16", "seventeen": "17",
    "eighteen": "18", "nineteen": "19", "twenty": "20",
}
# Generic glue words and answer preambles, not dataset-specific values.
GLUE = frozenset((
    "a", "an", "and", "are", "as", "at", "be", "based", "belong",
    "belongs", "belonging", "by", "called", "currently", "does",
    "do", "for", "from", "had", "has", "have", "in", "is", "it",
    "its", "memory", "memories", "my", "now", "of", "on", "one",
    "or", "our", "place", "provided", "record", "records", "refer",
    "referring", "rescheduled", "the", "their", "there", "this",
    "to", "was", "were", "which", "who", "with", "you", "your",
    "takes", "taking", "what", "when", "where", "that", "answer",
))


def words(text):
    if not isinstance(text, str):
        raise ValueError("Token source must be text.")
    result = []
    for item in re.findall(r"[a-zA-Z]+|\d+", text.casefold()):
        token = item
        if len(token) > 4 and token.endswith("s") and not token.endswith("ss"):
            token = token[:-1]
        token = NUMBER_WORDS.get(token, token)
        result.append(token)
    return result


def check_answer(question, answer, selected):
    """Inspect claims against retrieved text only, with no gold labels."""
    if not isinstance(question, str) or not isinstance(answer, str):
        raise ValueError("Question and answer must be strings.")
    if not isinstance(selected, list) or any(
        not isinstance(m, dict) or not isinstance(m.get("id"), int)
        or not isinstance(m.get("fact"), str) for m in selected
    ):
        raise ValueError("Retrieved records must include numeric IDs and facts.")
    if answer.strip() == NO_MEMORY_ANSWER:
        return {"status": "abstained", "novel_terms": [],
                "unsupported_weekdays": [], "unsupported_numbers": [],
                "bad_citations": []}

    context_tokens = set(words(" ".join(m["fact"] for m in selected)))
    question_tokens = set(words(question))
    proposed = re.sub(r"\[M\d+\]", " ", answer, flags=re.IGNORECASE)
    tokens = set(words(proposed))
    citations = [int(n) for n in re.findall(r"\[M(\d+)\]", answer, re.I)]
    available_ids = {m["id"] for m in selected}
    bad_citations = sorted({n for n in citations if n not in available_ids})
    day_tokens = tokens & WEEKDAYS
    novel_days = sorted(day_tokens - context_tokens)
    numerals = {v for v in tokens if v.isdigit()}
    novel_nums = sorted(numerals - context_tokens, key=lambda v: (len(v), v))
    # Unlike an entailment check, this simple novelty comparison does not
    # know whether a statement asserts an old or new value.
    novel = sorted(t for t in tokens if t not in context_tokens
                   and t not in question_tokens and t not in GLUE)
    if bad_citations:
        status = "invalid_citation"
    elif novel_days:
        status = "unsupported_weekday"
    elif novel_nums:
        status = "unsupported_number"
    elif novel:
        status = "novel_terms_review"
    else:
        status = "no_obvious_lexical_novelty"
    return {
        "status": status, "novel_terms": novel,
        "unsupported_weekdays": novel_days,
        "unsupported_numbers": novel_nums,
        "bad_citations": bad_citations,
    }


def inspect_run(run, dataset, digest):
    """Reject changed/question-mismatched inputs instead of mixing runs."""
    if any((
        run.get("dataset_sha256") != digest,
        run.get("policy") != "reviewed",
        run.get("method") != "project_authored_semantic_development_not_accuracy",
        run.get("embedding") != "all-minilm",
    )):
        raise ValueError("Not a matching baseline Phase 10 run.")
    cases = dataset["scenarios"]
    results = run.get("results")
    if not isinstance(results, dict) or set(results) != {
        case["id"] + "_reviewed" for case in cases
    }:
        raise ValueError("A complete 14-scenario Phase 10 result is required.")
    rows = []
    for case in cases:
        result = results[case["id"] + "_reviewed"]
        if (result.get("scenario") != case["id"]
            or result.get("policy") != "reviewed"
            or not isinstance(result.get("checks"), list)
            or len(result["checks"]) != len(case["checks"])):
            raise ValueError("Scenario mismatch: " + case["id"])
        active = result.get("active_memories")
        if not isinstance(active, list):
            raise ValueError("No active memories in " + case["id"])
        ids = {m["id"] for m in active}
        checks = result["checks"]
        for check, authored in zip(checks, case["checks"]):
            if (check.get("id") != authored["id"]
                or check.get("question") != authored["question"]):
                raise ValueError("Question identity mismatch.")
            retrieved_ids = check.get("retrieved_memory_ids")
            if not isinstance(retrieved_ids, list) or not set(retrieved_ids).issubset(ids):
                raise ValueError("Invalid retrieval IDs.")
            selected = [m for m in active if m["id"] in retrieved_ids]
            finding = check_answer(check["question"], check["answer"], selected)
            rows.append({
                "id": case["id"] + "/" + check["id"],
                "question": check["question"],
                "answer": check["answer"],
                "support_retrieved": check.get("support_retrieved"),
                "authored_expect_abstention": authored.get("expect_abstention", False),
                **finding,
            })
    counts = Counter(r["status"] for r in rows)
    return {
        "method": "lexical_novelty_probe_not_entailment_or_accuracy",
        "dataset_sha256": digest,
        "total_questions": len(rows),
        "counts": dict(counts),
        "rows": rows,
    }


def markdown(result, sha):
    lines = [
        "# Phase 12 — Answer novelty screening (development only)",
        "",
        "**Not independent accuracy, truth verification, or a safe autonomous "
        "answering policy.** This probe flags novel tokens in *saved* "
        "baseline answers; it does not call an LLM or modify memories.",
        "",
        "- Original Phase 10 input SHA-256: " + sha,
        "- Questions: " + str(result["total_questions"]),
        "",
        "## Screening outcomes", "",
        "| Status | Count |", "|---|---:|",
    ]
    for label, n in sorted(result["counts"].items()):
        lines.append("| " + label + " | " + str(n) + " |")
    lines += ["", "## All saved answers", "",
              "| Case/question | Status | Novel terms | Answer |",
              "|---|---|---|---|"]
    for row in result["rows"]:
        lines.append(
            "| " + row["id"] + " | " + row["status"] + " | "
            + ", ".join(row["novel_terms"])
            + " | " + row["answer"].replace("|", "/").replace("\n", " ")[:250]
            + " |"
        )
    lines += [
        "", "## Methodological limits", "",
        "A term that appears in memory is not necessarily relevant or true "
        "for the user's question. This method can miss stale values, "
        "negated claims, false associations, or a new fact described using "
        "old vocabulary. Conversely, a legitimate paraphrase, synonym or "
        "new morphological form may trigger manual review. It is NOT a "
        "semantic entailment check or a replacement for human oversight.",
        "",
        "The status is computed without looking at the authored answer "
        "keywords or expected answerability; those are recorded only for "
        "later diagnostic inspection. These 14 fictional cases have already "
        "been examined and cannot validate this newly designed method.",
        "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    args = parser.parse_args()
    try:
        raw = args.source.read_bytes()
        run = json.loads(raw)
        dataset, digest = load_dataset()
        findings = inspect_run(run, dataset, digest)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("Cannot inspect Phase 10 baseline:", error)
        return 1
    if JSON_REPORT.exists() or REPORT.exists():
        print("Existing Phase 12 report preserved (no overwrite).")
        return 1
    findings["input_sha256"] = hashlib.sha256(raw).hexdigest()
    findings["created_at"] = datetime.now(timezone.utc).isoformat()
    JSON_REPORT.parent.mkdir(parents=True, exist_ok=True)
    with JSON_REPORT.open("x", encoding="utf-8") as output:
        json.dump(findings, output, indent=2, ensure_ascii=False)
        output.write("\n")
    with REPORT.open("x", encoding="utf-8") as output:
        output.write(markdown(findings, findings["input_sha256"]))
    print("Saved diagnostic:", REPORT)
    print("Counts:", findings["counts"])
    print("Reminder: novel-token screening is NOT factual correctness.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
