"""Phase 8: separately label fictional cases with the frozen rubric v2.

Run these ON EACH REVIEWER'S OWN SESSION, without viewing model output:
  python -m scripts.review_holdout_v2 --rater A --limit 4
  python -m scripts.review_holdout_v2 --rater A
  python -m scripts.review_holdout_v2 --rater A --status
  python -m scripts.review_holdout_v2 --rater A --lock

Reviewer B replaces A with B. Never run Qwen until BOTH are locked.
Neither review program accesses SQLite or the other reviewer's labels.
"""
import argparse
import copy
from datetime import datetime, timezone
from pathlib import Path

from scripts.review_eval_cases import load_cases, save_review
from scripts.review_second import (
    ACTIONS, CHOICES, FIELDS, LABELS,
    add_assessment, ask_option, load_second, lock_second,
)

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "benchmarks" / "holdout_v2_cases.json"
REVIEW_PATHS = {
    "A": ROOT / "results" / "raw" / "holdout_v2_rater_A.json",
    "B": ROOT / "results" / "raw" / "holdout_v2_rater_B.json",
}
ACTIONS_FOR_LABEL = {
    "duplicate": "skip_duplicate",
    "replaces": "supersede_old",
    "coexists": "keep_both",
    "uncertain": "review_needed",
}


def consistency_warnings(assessment):
    """Warn on contradictory labels/actions; never infer ground truth."""
    axes = assessment["axes"]
    label = assessment["label"]
    action = assessment["storage_action"]
    warnings = []
    if action != ACTIONS_FOR_LABEL[label]:
        warnings.append(
            f"'{label}' should normally use '{ACTIONS_FOR_LABEL[label]}', "
            f"not '{action}'."
        )
    if label in {"duplicate", "replaces"} and (
        axes["same_entity"] != "yes" or axes["same_attribute"] != "yes"
    ):
        warnings.append(
            "Duplicate/replacement requires the same established entity "
            "and specific attribute."
        )
    if label == "replaces" and axes["old_fact_known_obsolete"] != "yes":
        warnings.append(
            "Replacement requires evidence that the old fact is outdated."
        )
    if label == "duplicate" and axes["old_fact_known_obsolete"] == "yes":
        warnings.append(
            "A repeated fact is not an outdated fact; check the relation."
        )
    if label == "coexists" and axes["old_fact_known_obsolete"] == "yes":
        warnings.append(
            "Coexisting facts should not establish the old one is outdated."
        )
    return warnings


def load_local_cases():
    """Use the frozen Phase 8 case file, never the Experiment 010 dataset."""
    return load_cases(CASES)


def load_rater(rater, cases=None, digest=None):
    if rater not in REVIEW_PATHS:
        raise ValueError("Choose rater A or B.")
    if cases is None or digest is None:
        cases, digest = load_local_cases()
    return load_second(
        REVIEW_PATHS[rater], digest, {case["id"] for case in cases}
    )


def prompt_one(case, input_fn=input, output_fn=print):
    output_fn(
        "\n" + case["id"] + " | topic: " + case["topic"]
        + "\nOLD: " + case["old_fact"]
        + "\nNEW: " + case["new_fact"]
    )
    axes = {}
    for key, question in FIELDS:
        axes[key] = ask_option(
            question + " [Y/N/U]: ", CHOICES, input_fn, output_fn
        )
    label = ask_option(
        "Relation D=duplicate, R=replaces, C=coexists, U=uncertain: ",
        LABELS, input_fn, output_fn
    )
    reason = input_fn("Explain briefly: ").strip()
    while not reason:
        reason = input_fn("Please enter an explanation: ").strip()
    action = ask_option(
        "Storage K=keep, S=supersede, R=review, D=skip duplicate: ",
        ACTIONS, input_fn, output_fn
    )
    value = {
        "label": LABELS[label], "reason": reason,
        "axes": {key: CHOICES[code] for key, code in axes.items()},
        "storage_action": ACTIONS[action],
    }
    return value


def review_interactive(cases, review, rater, limit=None,
                       edit_id=None, input_fn=input, output_fn=print,
                       save_fn=None):
    """Do not save invalid contradictory answers; allow revising unlocked."""
    if review["locked"]:
        output_fn("Review is locked. No edits allowed.")
        return 0
    if edit_id is not None and edit_id not in review["answers"]:
        raise ValueError("Can only edit a case previously answered.")
    if save_fn is None:
        save_fn = lambda data: save_review(data, REVIEW_PATHS[rater])
    output_fn(
        f"Phase 8 reviewer {rater}. Read docs/label_rubric_v2.md. "
        "Do not inspect the other reviewer's labels or Qwen predictions."
    )
    written = 0
    for case in cases:
        cid = case["id"]
        if edit_id is not None:
            if cid != edit_id:
                continue
        elif cid in review["answers"]:
            continue
        if limit is not None and written >= limit:
            break
        if edit_id is not None:
            output_fn("Previous decision: " + str(review["answers"][cid]))
        choice = ask_option(
            f"\n{cid}: R=review this case; S=skip; Q=quit: ",
            ("R", "S", "Q"), input_fn, output_fn
        )
        if choice == "Q":
            break
        if choice == "S":
            continue
        proposal = prompt_one(case, input_fn=input_fn, output_fn=output_fn)
        warnings = consistency_warnings(proposal)
        if warnings:
            output_fn("The response was NOT saved. Please review these issues:")
            for issue in warnings:
                output_fn(" - " + issue)
            output_fn("Run this command again to re-answer that case.")
            continue
        if cid in review["answers"]:
            review.setdefault("revision_history", []).append({
                "case_id": cid,
                "previous": copy.deepcopy(review["answers"][cid]),
                "revised_at": datetime.now(timezone.utc).isoformat(),
            })
        review["answers"][cid] = proposal
        save_fn(review)
        written += 1
        output_fn("Saved " + cid + " locally.")
    return written


def lock_rater(review, cases):
    """Require complete, internally consistent decisions before freezing."""
    for cid, answer in review["answers"].items():
        issues = consistency_warnings(answer)
        if issues:
            raise ValueError(
                f"Resolve contradictory evidence for {cid}: " + "; ".join(issues)
            )
    lock_second(review, cases)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rater", choices=("A", "B"), required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--lock", action="store_true")
    parser.add_argument("--edit", metavar="CASE_ID")
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive.")
    if args.edit and (args.lock or args.status or args.limit):
        parser.error("--edit cannot be combined with other review actions.")
    cases, digest = load_local_cases()
    review = load_rater(args.rater, cases, digest)
    if args.lock:
        try:
            lock_rater(review, cases)
        except ValueError as error:
            print("Cannot lock:", error)
            return 1
        save_review(review, REVIEW_PATHS[args.rater])
        print(f"Reviewer {args.rater} labels locked. Keep them unchanged.")
        return 0
    if not args.status:
        edit_id = args.edit.upper() if args.edit else None
        if edit_id and edit_id not in review["answers"]:
            print("Cannot edit unanswered case:", edit_id)
            return 1
        review_interactive(
            cases, review, args.rater,
            limit=1 if edit_id else args.limit, edit_id=edit_id
        )
    print(
        f"Rater {args.rater}: {len(review['answers'])}/{len(cases)} labelled; "
        f"locked={review['locked']}."
    )
    if len(review["answers"]) == len(cases) and not review["locked"]:
        print(
            f"Next: python -m scripts.review_holdout_v2 "
            f"--rater {args.rater} --lock"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
