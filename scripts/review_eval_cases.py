"""Blind human labelling for fictional MemoryLab evaluation cases.

Instructions:
  python -m scripts.review_eval_cases --limit 4
  python -m scripts.review_eval_cases
  python -m scripts.review_eval_cases --status
  python -m scripts.review_eval_cases --lock

Never calls Qwen or reads your SQLite memory database.
All votes stay in Git-ignored results/raw/ and can be resumed.
"""
import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES_FILE = ROOT / "benchmarks" / "review_v1_cases.json"
LABELS_FILE = ROOT / "results" / "raw" / "review_v1_labels.json"
LABELS = {"D": "duplicate", "R": "replaces",
          "C": "coexists", "U": "uncertain"}

RUBRIC = (
    "D — Duplicate: new fact repeats the same information.\n"
    "R — Replaces: new fact clearly makes the SAME specific old fact outdated.\n"
    "C — Coexists: different facts can both remain true.\n"
    "U — Uncertain: identity, time, attribute, or updated value is unclear.\n"
    "S — Skip this case for now; Q — Quit and keep completed work."
)


def load_cases(path=CASES_FILE):
    raw = Path(path).read_bytes()
    data = json.loads(raw)
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("Case file must contain a nonempty cases list.")
    ids = []
    for case in cases:
        if not isinstance(case, dict) or not all(
            isinstance(case.get(field), str) and case[field].strip()
            for field in ("id", "topic", "old_fact", "new_fact")
        ):
            raise ValueError("Each case needs id, topic, old_fact and new_fact.")
        if any(key in case for key in ("expected", "label", "prediction")):
            raise ValueError("Blind cases cannot contain answer labels.")
        ids.append(case["id"])
    if len(set(ids)) != len(ids):
        raise ValueError("Case IDs must be unique.")
    return cases, hashlib.sha256(raw).hexdigest()


def empty_review(digest):
    return {"format_version": 1, "dataset_sha256": digest,
            "locked": False, "locked_at": None,
            "answers_sha256": None, "answers": {}}


def answers_sha256(answers):
    """Detect accidental edits to an already-locked review."""
    data = json.dumps(
        answers, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def load_review(path, digest, case_ids):
    path = Path(path)
    if not path.exists():
        return empty_review(digest)
    saved = json.loads(path.read_text(encoding="utf-8"))
    if saved.get("dataset_sha256") != digest:
        raise ValueError("The case file changed; existing labels were not overwritten.")
    answers = saved.get("answers")
    if saved.get("format_version") != 1 or not isinstance(answers, dict):
        raise ValueError("Unrecognised label file format.")
    if not set(answers).issubset(case_ids):
        raise ValueError("Labels refer to unknown case IDs.")
    for value in answers.values():
        if not isinstance(value, dict):
            raise ValueError("Invalid answer format.")
        if (value.get("label") not in LABELS.values()
                or not isinstance(value.get("reason"), str)
                or not value["reason"].strip()):
            raise ValueError("Each saved label needs a permitted label and a reason.")
    if saved.get("locked") is True and saved.get("answers_sha256") != answers_sha256(answers):
        raise ValueError("Locked label content changed; evaluation stopped.")
    return saved


def save_review(data, path=LABELS_FILE):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    os.replace(tmp, path)


def record_label(review, case_id, answer, reason):
    """Pure validation; does not save or call any LLM."""
    if review["locked"]:
        raise ValueError("Labels are locked and cannot be changed.")
    label = LABELS.get(answer.upper().strip())
    if label is None or not reason.strip():
        raise ValueError("Choose D/R/C/U and enter a brief reason.")
    review["answers"][case_id] = {
        "label": label, "reason": reason.strip()
    }


def lock_review(review, cases):
    if review["locked"]:
        raise ValueError("Already locked.")
    if set(review["answers"]) != {c["id"] for c in cases}:
        raise ValueError(
            "Finish all case labels before locking. Use --status to check."
        )
    review["locked"] = True
    review["locked_at"] = datetime.now(timezone.utc).isoformat()
    review["answers_sha256"] = answers_sha256(review["answers"])


def run_interactive(cases, review, limit=None, input_fn=input, output_fn=print):
    if review["locked"]:
        output_fn("Labels already locked. No edits allowed.")
        return 0
    done = 0
    output_fn("Blind human review — do not run Qwen until labels are locked.")
    output_fn(RUBRIC)
    for case in cases:
        if case["id"] in review["answers"]:
            continue
        if limit is not None and done >= limit:
            break
        output_fn(
            f"\n{case['id']} | topic: {case['topic']}\n"
            f"OLD: {case['old_fact']}\nNEW: {case['new_fact']}"
        )
        while True:
            choice = input_fn("Your label [D/R/C/U/S/Q]: ").strip().upper()
            if choice in LABELS or choice in {"S", "Q"}:
                break
            output_fn("Please type D, R, C, U, S or Q.")
        if choice == "Q":
            break
        if choice == "S":
            continue
        reason = input_fn("Why? (short reason required): ").strip()
        while not reason:
            reason = input_fn("Please add a short reason: ").strip()
        record_label(review, case["id"], choice, reason)
        save_review(review)
        done += 1
        output_fn(f"Saved {case['id']} locally.")
    return done


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None,
                        help="Review at most this many new cases per session.")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--lock", action="store_true",
                        help="Freeze the completed labels before model evaluation.")
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive.")
    cases, digest = load_cases()
    review = load_review(LABELS_FILE, digest, {c["id"] for c in cases})
    if args.lock:
        lock_review(review, cases)
        save_review(review)
        print("All labels locked. It is now safe to run model evaluation.")
        return 0
    if not args.status:
        run_interactive(cases, review, args.limit)
    print(
        f"Review progress: {len(review['answers'])}/{len(cases)} labelled; "
        f"locked={review['locked']}. Local file: {LABELS_FILE}"
    )
    if len(review["answers"]) == len(cases) and not review["locked"]:
        print("Next: python -m scripts.review_eval_cases --lock")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
