"""Human adjudication of disagreements; preserves both original raters.

Run ONLY after second-review labels have been locked:
  python -m scripts.compare_human_reviews
  python -m scripts.adjudicate_reviews --limit 4
  python -m scripts.adjudicate_reviews
  python -m scripts.adjudicate_reviews --status
  python -m scripts.adjudicate_reviews --edit B04
  python -m scripts.adjudicate_reviews --lock

Adjudication is not blind (both human labels and rationales are visible).
Qwen is never called and MemoryLab's SQLite database is never used.
"""
import argparse
import copy
import json
from datetime import datetime, timezone
from pathlib import Path

from scripts.review_eval_cases import (
    LABELS, answers_sha256, load_cases, save_review,
)
from scripts.review_second import ACTIONS, CHOICES, FIELDS, ask_option
from scripts.compare_human_reviews import build_comparison, locked_reviews

ROOT = Path(__file__).resolve().parents[1]
ADJ_FILE = ROOT / "results" / "raw" / "review_v1_adjudication.json"
FINAL_FILE = ROOT / "results" / "raw" / "review_v1_adjudicated_summary.json"


def new_adjudication(digest, first, second, queue):
    return {
        "format_version": 1,
        "dataset_sha256": digest,
        "first_answers_sha256": first["answers_sha256"],
        "second_answers_sha256": second["answers_sha256"],
        "queue_ids": [r["id"] for r in queue],
        "locked": False,
        "locked_at": None,
        "answers_sha256": None,
        "revision_history": [],
        "answers": {},
    }


def validate_final(value):
    if not isinstance(value, dict):
        raise ValueError("Invalid adjudication entry.")
    if value.get("final_label") not in set(LABELS.values()) | {"deferred"}:
        raise ValueError("Choose D, R, C, U or X (defer).")
    if not isinstance(value.get("reason"), str) or not value["reason"].strip():
        raise ValueError("Every adjudication needs a rationale.")
    axes = value.get("axes")
    if not isinstance(axes, dict) or set(axes) != {field for field, _ in FIELDS}:
        raise ValueError("Adjudication requires all four evidence dimensions.")
    if any(v not in CHOICES.values() for v in axes.values()):
        raise ValueError("Evidence dimensions must be yes, no, or unknown.")
    if value.get("storage_action") not in ACTIONS.values():
        raise ValueError("Invalid storage recommendation.")
    if value["final_label"] == "deferred" and value["storage_action"] != "review_needed":
        raise ValueError("Deferred cases must remain in human review.")


def consistency_warnings(assessment):
    """Detect contradictory storage recommendations, not semantic truth."""
    label = assessment["final_label"]
    action = assessment["storage_action"]
    axes = assessment["axes"]
    problems = []
    if label == "duplicate" and action not in ("skip_duplicate", "review_needed"):
        problems.append(
            "Duplicate facts should be skipped, not kept twice or superseded."
        )
    if label in ("coexists", "uncertain", "deferred") and action == "supersede_old":
        problems.append(
            "Cannot supersede an old memory from a coexistence or unknown label."
        )
    if label == "replaces" and action == "skip_duplicate":
        problems.append(
            "A genuine replacement should not be marked as a duplicate."
        )
    if action == "supersede_old" and not all(
        axes[field] == "yes"
        for field in ("same_entity", "same_attribute", "old_fact_known_obsolete")
    ):
        problems.append(
            "Superseding requires verified same entity, same attribute, "
            "and an outdated old value."
        )
    return problems


def load_adjudication(path, digest, first, second, queue):
    path = Path(path)
    expected = new_adjudication(digest, first, second, queue)
    if not path.exists():
        return expected
    saved = json.loads(path.read_text(encoding="utf-8"))
    for key in ("format_version", "dataset_sha256", "first_answers_sha256",
                "second_answers_sha256", "queue_ids"):
        if saved.get(key) != expected[key]:
            raise ValueError("Human review evidence changed; prior adjudication preserved.")
    answers = saved.get("answers")
    if not isinstance(answers, dict) or not set(answers).issubset(expected["queue_ids"]):
        raise ValueError("Adjudication has invalid case IDs.")
    for entry in answers.values():
        validate_final(entry)
    if saved.get("locked") is True and saved.get("answers_sha256") != answers_sha256(answers):
        raise ValueError("Locked adjudication was edited.")
    return saved


def record_final(review, cid, label, reason, axes, action):
    if review["locked"]:
        raise ValueError("Adjudication is locked.")
    if cid not in review["queue_ids"]:
        raise ValueError("Case is not on adjudication queue.")
    code = label.strip().upper()
    value = {
        "final_label": "deferred" if code == "X" else LABELS.get(code),
        "reason": reason.strip(),
        "axes": {field: CHOICES.get(v.strip().upper())
                 for field, v in axes.items()},
        "storage_action": ACTIONS.get(action.strip().upper()),
    }
    validate_final(value)
    if cid in review["answers"]:
        review.setdefault("revision_history", []).append({
            "case_id": cid,
            "previous": copy.deepcopy(review["answers"][cid]),
            "revised_at": datetime.now(timezone.utc).isoformat(),
        })
    review["answers"][cid] = value


def lock_adjudication(review):
    if review["locked"]:
        raise ValueError("Already locked.")
    if set(review["answers"]) != set(review["queue_ids"]):
        raise ValueError("Finish every flagged case before locking; check --status.")
    warnings = [
        cid for cid, answer in review["answers"].items()
        if consistency_warnings(answer)
    ]
    if warnings:
        raise ValueError(
            "Review conflicting storage decisions before locking: "
            + ", ".join(warnings)
            + ". Use: python -m scripts.adjudicate_reviews --edit "
            + warnings[0]
        )
    review["locked"] = True
    review["locked_at"] = datetime.now(timezone.utc).isoformat()
    review["answers_sha256"] = answers_sha256(review["answers"])


def build_final_summary(rows, review):
    """Keep original votes; distinguish adjudicated from unexamined agreement."""
    if review["locked"] is not True:
        raise ValueError("Cannot publish an unlocked adjudication summary.")
    output = []
    for row in rows:
        cid = row["id"]
        item = {
            "id": cid,
            "first_label": row["first"]["label"],
            "second_label": row["second"]["label"],
        }
        if cid in review["answers"]:
            decision = review["answers"][cid]
            item["status"] = (
                "deferred" if decision["final_label"] == "deferred"
                else "adjudicated"
            )
            item["final_label"] = (
                None if decision["final_label"] == "deferred"
                else decision["final_label"]
            )
            item["reason"] = decision["reason"]
            item["axes"] = decision["axes"]
            item["storage_action"] = decision["storage_action"]
        else:
            if row["disagreement"] or row["pre_registered_priority"]:
                raise ValueError("Flagged case missing adjudication.")
            item["status"] = "agreed_not_adjudicated"
            item["final_label"] = row["first"]["label"]
            item["reason"] = "Both initial reviewers agreed; not examined in adjudication."
        output.append(item)
    return output


def adjudicate_interactive(rows, review, limit=None, input_fn=input,
                           output_fn=print, save_fn=None, edit_id=None):
    if review["locked"]:
        output_fn("Adjudication is already locked.")
        return 0
    if save_fn is None:
        save_fn = lambda data: save_review(data, ADJ_FILE)
    if edit_id is not None and edit_id not in review["answers"]:
        raise ValueError("Cannot edit an unanswered case; complete it first.")
    done = 0
    output_fn(
        "ADJUDICATION IS NOT BLIND: both human assessments are shown. "
        "No Qwen results are shown."
    )
    for row in rows:
        cid = row["id"]
        if edit_id is not None:
            if cid != edit_id:
                continue
        elif not row["adjudicate"] or cid in review["answers"]:
            continue
        if limit is not None and done >= limit:
            break
        output_fn(
            "\n" + cid + " | " + row["topic"]
            + "\nOLD: " + row["old_fact"]
            + "\nNEW: " + row["new_fact"]
            + "\nReviewer 1: " + row["first"]["label"]
            + " — " + row["first"]["reason"]
            + "\nReviewer 2: " + row["second"]["label"]
            + " — " + row["second"]["reason"]
            + "\nR2 dimensions: " + json.dumps(row["second"]["axes"])
        )
        if edit_id is not None:
            output_fn(
                "Previous saved decision: "
                + json.dumps(review["answers"][cid], ensure_ascii=False)
            )
        code = ask_option(
            "Adjudicated label [D/R/C/U] / X=defer / Q=quit: ",
            (*LABELS.keys(), "X", "Q"), input_fn, output_fn
        )
        if code == "Q":
            break
        reason = input_fn("Why? (brief explanation): ").strip()
        while not reason:
            reason = input_fn("Explanation is required: ").strip()
        if code == "X":
            axes = {field: "U" for field, _ in FIELDS}
            action = "R"
        else:
            axes = {
                field: ask_option(
                    prompt + " [Y/N/U]: ", CHOICES, input_fn, output_fn
                )
                for field, prompt in FIELDS
            }
            action = ask_option(
                "Recommended storage [K/S/R/D]: ",
                ACTIONS, input_fn, output_fn
            )
        record_final(review, cid, code, reason, axes, action)
        save_fn(review)
        done += 1
        output_fn("Saved adjudication for " + cid + ".")
    return done


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--lock", action="store_true")
    parser.add_argument(
        "--edit", metavar="CASE_ID",
        help="Revisit an already answered case before the review is locked."
    )
    args = parser.parse_args()
    if args.edit is not None and (args.lock or args.status or args.limit is not None):
        parser.error("--edit cannot be combined with --limit, --status or --lock.")
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive.")
    try:
        cases, digest = load_cases()
        first, second = locked_reviews(cases, digest)
        rows, _ = build_comparison(cases, first, second)
        queue = [r for r in rows if r["adjudicate"]]
        review = load_adjudication(ADJ_FILE, digest, first, second, queue)
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
        print("Cannot adjudicate yet:", exc)
        return 1
    if args.edit:
        case_id = args.edit.upper()
        if review["locked"] or case_id not in review["answers"]:
            print("Cannot edit: case missing or adjudication already locked.")
            return 1
        adjudicate_interactive(rows, review, limit=1, edit_id=case_id)
        print("Revised case", case_id)
        return 0
    if args.lock:
        try:
            lock_adjudication(review)
        except ValueError as exc:
            print("Cannot lock:", exc)
            return 1
        save_review(review, ADJ_FILE)
        summary = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "dataset_sha256": digest,
            "first_answers_sha256": first["answers_sha256"],
            "second_answers_sha256": second["answers_sha256"],
            "adjudication_answers_sha256": review["answers_sha256"],
            "rows": build_final_summary(rows, review),
        }
        FINAL_FILE.parent.mkdir(parents=True, exist_ok=True)
        FINAL_FILE.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print("Locked and exported adjudication summary:", FINAL_FILE)
        return 0
    if not args.status:
        adjudicate_interactive(rows, review, args.limit)
    print(
        f"Adjudication: {len(review['answers'])}/{len(queue)} flagged cases, "
        f"locked={review['locked']}. Local file: {ADJ_FILE}"
    )
    for cid, assessment in review["answers"].items():
        for message in consistency_warnings(assessment):
            print(
                f"Please review {cid}: {message} "
                f"Run: python -m scripts.adjudicate_reviews --edit {cid}"
            )
    if len(review["answers"]) == len(queue) and not review["locked"]:
        print("Next: python -m scripts.adjudicate_reviews --lock")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
