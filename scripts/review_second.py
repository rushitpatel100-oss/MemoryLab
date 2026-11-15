"""Phase 7: separate, blind human review with structured memory decisions.

A *second person* should run this without seeing the first reviewer's labels,
Qwen predictions, or Experiment 010. This script reads only the public cases
and its OWN local response file. It never calls a model or accesses SQLite.

    python -m scripts.review_second --limit 4
    python -m scripts.review_second
    python -m scripts.review_second --status
    python -m scripts.review_second --lock
"""
import argparse
import json
from pathlib import Path

from scripts.review_eval_cases import (
    LABELS, answers_sha256, load_cases, save_review,
)

ROOT = Path(__file__).resolve().parents[1]
SECOND_FILE = ROOT / "results" / "raw" / "review_v1_second_labels.json"
CHOICES = {"Y": "yes", "N": "no", "U": "unknown"}
ACTIONS = {
    "K": "keep_both",
    "S": "supersede_old",
    "R": "review_needed",
    "D": "skip_duplicate",
}
FIELDS = (
    ("same_entity", "Same person / object / event?"),
    ("same_attribute", "Same specific property or attribute?"),
    ("old_fact_known_obsolete", "Is the older fact demonstrably outdated?"),
    ("new_value_known", "Is a specific new value provided?"),
)


def new_review(dataset_digest):
    return {
        "format_version": 1,
        "dataset_sha256": dataset_digest,
        "locked": False,
        "locked_at": None,
        "answers_sha256": None,
        "answers": {},
    }


def validate_answer(answer):
    if not isinstance(answer, dict):
        raise ValueError("Assessment must be a JSON object.")
    if answer.get("label") not in LABELS.values():
        raise ValueError("Invalid relationship label.")
    if not isinstance(answer.get("reason"), str) or not answer["reason"].strip():
        raise ValueError("Every relationship needs a short explanation.")
    if answer.get("storage_action") not in ACTIONS.values():
        raise ValueError("Invalid storage recommendation.")
    axes = answer.get("axes")
    if not isinstance(axes, dict) or set(axes) != {field for field, _ in FIELDS}:
        raise ValueError("All four structured review fields are required.")
    if any(v not in CHOICES.values() for v in axes.values()):
        raise ValueError("Structured fields must be yes, no or unknown.")


def load_second(path, dataset_digest, valid_ids):
    path = Path(path)
    if not path.exists():
        return new_review(dataset_digest)
    review = json.loads(path.read_text(encoding="utf-8"))
    if review.get("format_version") != 1:
        raise ValueError("Unknown second-review format.")
    if review.get("dataset_sha256") != dataset_digest:
        raise ValueError("The public dataset changed. Existing review preserved.")
    answers = review.get("answers")
    if not isinstance(answers, dict) or not set(answers).issubset(valid_ids):
        raise ValueError("Second review contains invalid case IDs.")
    for entry in answers.values():
        validate_answer(entry)
    if review.get("locked") is True:
        if review.get("answers_sha256") != answers_sha256(answers):
            raise ValueError("Locked second-review labels were modified.")
    return review


def add_assessment(review, case_id, label, reason, axes, action):
    if review["locked"]:
        raise ValueError("Cannot edit locked review.")
    if not isinstance(case_id, str) or not case_id:
        raise ValueError("Case ID required.")
    entry = {
        "label": LABELS.get(label.strip().upper()),
        "reason": reason.strip(),
        "axes": {field: CHOICES.get(value.strip().upper())
                 for field, value in axes.items()},
        "storage_action": ACTIONS.get(action.strip().upper()),
    }
    validate_answer(entry)
    review["answers"][case_id] = entry


def lock_second(review, cases):
    if review["locked"]:
        raise ValueError("Second-review labels already locked.")
    if set(review["answers"]) != {c["id"] for c in cases}:
        raise ValueError("Complete all cases before locking. Check --status.")
    for assessment in review["answers"].values():
        validate_answer(assessment)
    from datetime import datetime, timezone
    review["locked"] = True
    review["locked_at"] = datetime.now(timezone.utc).isoformat()
    review["answers_sha256"] = answers_sha256(review["answers"])


def ask_option(prompt, allowed, input_fn=input, output_fn=print):
    while True:
        choice = input_fn(prompt).strip().upper()
        if choice in allowed:
            return choice
        output_fn("Please choose: " + ", ".join(allowed))


def review_cases(cases, review, limit=None, input_fn=input, output_fn=print,
                 save_fn=None):
    """Review unseen cases, saving each completed response immediately."""
    if review["locked"]:
        output_fn("This review is locked; no edits are allowed.")
        return 0
    if save_fn is None:
        save_fn = lambda record: save_review(record, SECOND_FILE)
    output_fn(
        "SECOND REVIEWER ONLY. Please do not inspect earlier labels, "
        "Experiment 010, or Qwen outputs before locking."
    )
    output_fn(
        "D=duplicate  R=replaces  C=coexists  U=uncertain\n"
        "For each evidence question: Y=yes  N=no  U=unknown.\n"
        "Storage action: K=keep both  S=supersede old  "
        "R=review needed  D=skip duplicate."
    )
    completed = 0
    for case in cases:
        if case["id"] in review["answers"]:
            continue
        if limit is not None and completed >= limit:
            break
        output_fn(
            "\n" + case["id"] + " | topic: " + case["topic"]
            + "\nOLD: " + case["old_fact"]
            + "\nNEW: " + case["new_fact"]
        )
        label = ask_option(
            "Relationship [D/R/C/U] (S=skip, Q=quit): ",
            (*LABELS.keys(), "S", "Q"), input_fn, output_fn
        )
        if label == "Q":
            break
        if label == "S":
            continue
        reason = input_fn("Why? (brief explanation): ").strip()
        while not reason:
            reason = input_fn("Explanation is required: ").strip()
        axes = {}
        for field, prompt in FIELDS:
            axes[field] = ask_option(
                prompt + " [Y/N/U]: ", CHOICES, input_fn, output_fn
            )
        action = ask_option(
            "What should be stored? [K/S/R/D]: ",
            ACTIONS, input_fn, output_fn
        )
        add_assessment(review, case["id"], label, reason, axes, action)
        save_fn(review)
        completed += 1
        output_fn("Saved " + case["id"] + " to the separate review file.")
    return completed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--lock", action="store_true")
    args = parser.parse_args()
    if args.limit is not None and args.limit <= 0:
        parser.error("--limit must be positive.")
    cases, digest = load_cases()
    review = load_second(SECOND_FILE, digest, {c["id"] for c in cases})
    if args.lock:
        lock_second(review, cases)
        save_review(review, SECOND_FILE)
        print("Second-review labels locked. Keep the JSON file unchanged.")
        return 0
    if not args.status:
        review_cases(cases, review, args.limit)
    print(
        f"Second reviewer: {len(review['answers'])}/{len(cases)} complete, "
        f"locked={review['locked']}."
    )
    if len(review["answers"]) == len(cases) and not review["locked"]:
        print("Next: python -m scripts.review_second --lock")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
