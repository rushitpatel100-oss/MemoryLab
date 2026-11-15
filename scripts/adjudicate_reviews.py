"""Human adjudication of disagreements; preserves both original raters.

Run ONLY after second-review labels have been locked:
  python -m scripts.compare_human_reviews
  python -m scripts.adjudicate_reviews --limit 4
  python -m scripts.adjudicate_reviews
  python -m scripts.adjudicate_reviews --status
  python -m scripts.adjudicate_reviews --lock

Adjudication is not blind (both human labels and rationales are visible).
Qwen is never called and MemoryLab's SQLite database is never used.
"""
import argparse
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
    review["answers"][cid] = value


def lock_adjudication(review):
    if review["locked"]:
        raise ValueError("Already locked.")
    if set(review["answers"]) != set(review["queue_ids"]):
        raise ValueError("Finish every flagged case before locking; check --status.")
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
                           output_fn=print, save_fn=None):
    if review["locked"]:
        output_fn("Adjudication is already locked.")
        return 0
    if save_fn is None:
        save_fn = lambda data: save_review(data, ADJ_FILE)
    done = 0
    output_fn(
        "ADJUDICATION IS NOT BLIND: both human assessments are shown. "
        "No Qwen results are shown."
    )
    for row in rows:
        cid = row["id"]
        if not row["adjudicate"] or cid in review["answers"]:
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
    args = parser.parse_args()
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
    if len(review["answers"]) == len(queue) and not review["locked"]:
        print("Next: python -m scripts.adjudicate_reviews --lock")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
