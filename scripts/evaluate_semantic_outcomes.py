"""Phase 10 optional semantic retrieval + Qwen answer development evaluation.

This is an extension of the Phase 10 storage-policy runner. It uses the
EXISTING all-minilm embedding ranker (top 3, min similarity 0.25) and
unchanged answer_generator.generate_answer on temporary fictional memories.
The input answers, storage decisions and benchmark are project authored,
NOT independent model ground truth.

Run the short smoke test, then resume:
    python -m scripts.evaluate_semantic_outcomes --limit 3
    python -m scripts.evaluate_semantic_outcomes

To compare all three policies:
    python -m scripts.evaluate_semantic_outcomes --policy all

Each scenario/policy is saved separately under results/raw. No SQLite
memorylab.db access, no model judgement of conflict labels, no old results
overwritten, and no personal memories are used.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from answer_generator import DEFAULT_CHAT_MODEL, generate_answer
from scripts.evaluate_downstream_memory import (
    POLICIES, RAW_DIR, load_dataset, run_scenario, score_text_answer,
    summarize,
)
from scripts.review_eval_cases import save_review
from semantic_search import find_similar


def select_retrieved(question, active, ranker=find_similar,
                     minimum=0.25, top_k=3):
    """Mirrors app.py: score all active memories, filter, top-three."""
    if not active:
        return []
    ranked = ranker(question, active)
    if not isinstance(ranked, list):
        raise ValueError("Semantic ranker returned an invalid result.")
    return [
        row["memory"] for row in ranked
        if row["similarity"] >= minimum
    ][:top_k]


def run_semantic_scenario(case, policy, *, answer_fn=generate_answer,
                          ranker=find_similar, model=DEFAULT_CHAT_MODEL,
                          minimum=0.25, top_k=3):
    """Run the real embedding search plus answer generator; no user data."""
    if not 0 <= minimum <= 1 or top_k < 1:
        raise ValueError("Invalid retrieval threshold/top-k.")
    outcome = run_scenario(case, policy)
    active = outcome["active_memories"]
    step_fact = {
        x["id"]: x["fact"] for x in case["steps"]
        if x["id"] in outcome["active_steps"]
    }
    for check in outcome["checks"]:
        retrieved = select_retrieved(
            check["question"], active, ranker, minimum, top_k
        )
        check["retrieved_memory_ids"] = [x["id"] for x in retrieved]
        support = check["support_steps"]
        check["support_retrieved"] = (
            all(
                any(item["fact"] == step_fact.get(sid)
                    for item in retrieved)
                for sid in support
            ) if support else None
        )
        answer = answer_fn(
            check["question"], retrieved, model=model
        )
        if not isinstance(answer, str):
            raise ValueError("Answer generator returned invalid text.")
        check["answer"] = answer
        check.update(score_text_answer(check, answer))
    return outcome


def blank_report(digest, policy, model, minimum, top_k):
    return {
        "version": 1,
        "method": "project_authored_semantic_development_not_accuracy",
        "dataset_sha256": digest,
        "policy": policy,
        "model": model,
        "embedding": "all-minilm",
        "minimum": minimum,
        "top_k": top_k,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "results": {},
    }


def load_saved(path, digest, policy, model, minimum, top_k, allowed_ids):
    output = Path(path)
    if not output.exists():
        return blank_report(digest, policy, model, minimum, top_k)
    saved = json.loads(output.read_text(encoding="utf-8"))
    expected = blank_report(digest, policy, model, minimum, top_k)
    for field in ("version", "method", "dataset_sha256", "policy",
                  "model", "embedding", "minimum", "top_k"):
        if saved.get(field) != expected[field]:
            raise ValueError("Existing semantic run has different settings/dataset.")
    if not isinstance(saved.get("results"), dict) or not set(saved["results"]).issubset(allowed_ids):
        raise ValueError("Saved semantic run contains unknown case/policy IDs.")
    return saved


def summarize_semantic(data):
    basic = summarize(data["results"])
    for policy, stats in basic.items():
        rows = [r for r in data["results"].values() if r["policy"] == policy]
        qs = [q for row in rows for q in row["checks"]
              if q["support_retrieved"] is not None]
        stats["support_retrieved"] = sum(
            q["support_retrieved"] is True for q in qs
        )
        stats["retrieval_question_total"] = len(qs)
    return basic


def markdown(data):
    summary = summarize_semantic(data)
    lines = [
        "# Phase 10 — Semantic retrieval and grounded-answer development diagnostic",
        "",
        "**Project-authored synthetic development checks, NOT independent "
        "model accuracy.** The reviewed policy uses scripted decisions, "
        "not a learned or validated AI memory-selection method.",
        "",
        "- Dataset fingerprint: " + data["dataset_sha256"],
        "- Local answer model: " + data["model"],
        "- Embeddings: all-minilm; minimum similarity "
        + str(data["minimum"]) + "; top " + str(data["top_k"]),
        "- All SQLite databases were temporary; no live personal data used",
        "- Answer grading: literal author keywords or known abstention "
        "phrases (a brittle proxy, not semantic correctness)",
        "",
        "## Policy comparison",
        "",
        "| Policy | Scenarios | Required facts stored | Required facts retrieved | "
        "Literal answer-proxy matches | Obsolete facts still active |",
        "|---|---:|---|---|---|---:|",
    ]
    for policy in POLICIES:
        if policy not in summary:
            continue
        stats = summary[policy]
        lines.append(
            "| " + policy + " | " + str(stats["scenarios"])
            + " | " + str(stats["known_support_available"]) + "/"
            + str(stats["known_support_total"])
            + " | " + str(stats["support_retrieved"]) + "/"
            + str(stats["retrieval_question_total"])
            + " | " + str(stats["llm_text_proxy_passes"]) + "/"
            + str(stats["llm_text_proxy_total"])
            + " | " + str(stats["stale_old_steps_active"]) + " |"
        )
    lines += ["", "## Per-question evidence and model responses", ""]
    for key, item in data["results"].items():
        lines += ["### " + key + " — " + item["title"], ""]
        for check in item["checks"]:
            lines += [
                "**" + check["id"] + ":** " + check["question"],
                "- Stored support: " + str(check["support_available"]),
                "- Retrieved support: " + str(check["support_retrieved"]),
                "- Retrieved memory IDs: "
                + str(check["retrieved_memory_ids"]),
                "- Model answer: " + check["answer"].replace("\n", " ")[:700],
                "- Keyword/abstention proxy: "
                + str(check["text_proxy_pass"]),
                "",
            ]
    lines += [
        "## Validity restrictions",
        "",
        "Retrieval and Qwen calls are real local integrations, but the "
        "fact pairs, expected values, and manually scripted memory "
        "actions were created in this project. A good score may reflect "
        "a simple fixture or a keyword without establishing that the "
        "model's answer was true. The same 14 cases must not be reused "
        "as unseen test data after tuning to their failures.",
        "",
        "The pipeline does not infer which old memory to supersede. "
        "It evaluates downstream evidence retention and answers given "
        "a specific storage policy. Human review and fresh independent "
        "test sets are needed before any broad correctness claim.",
        "",
    ]
    return "\n".join(lines)


def run_all_semantic(data, digest, policy, *, output, model,
                     minimum=0.25, top_k=3, limit=None,
                     answer_fn=generate_answer,
                     ranker=find_similar, log=print):
    choices = POLICIES if policy == "all" else (policy,)
    keys = {case["id"] + "_" + p
            for case in data["scenarios"] for p in choices}
    state = load_saved(
        output, digest, policy, model, minimum, top_k, keys
    )
    for case in data["scenarios"][:limit]:
        for p in choices:
            key = case["id"] + "_" + p
            if key in state["results"]:
                continue
            result = run_semantic_scenario(
                case, p, answer_fn=answer_fn,
                ranker=ranker, model=model,
                minimum=minimum, top_k=top_k
            )
            state["results"][key] = result
            save_review(state, output)
            log(key + ": retrieved and answered "
                + str(len(result["checks"])) + " questions.")
    if len(state["results"]) == len(keys):
        report_path = Path(output).with_suffix(".md")
        if not report_path.exists():
            report_path.parent.mkdir(parents=True, exist_ok=True)
            with report_path.open("x", encoding="utf-8") as out:
                out.write(markdown(state))
        log("Complete. Report: " + str(report_path))
    else:
        log(f"Saved: {len(state['results'])}/{len(keys)} scenario/policy runs.")
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", choices=("all",) + POLICIES,
                        default="reviewed")
    parser.add_argument("--model", default=DEFAULT_CHAT_MODEL)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--minimum", type=float, default=0.25)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("Limit must be positive.")
    if not 0 <= args.minimum <= 1 or args.top_k < 1:
        parser.error("Similarity minimum must be 0..1; top_k positive.")
    try:
        data, digest = load_dataset()
        output = RAW_DIR / ("phase10_semantic_" + args.policy + ".json")
        choices = POLICIES if args.policy == "all" else (args.policy,)
        keys = {case["id"] + "_" + p
                for case in data["scenarios"] for p in choices}
        if args.status:
            saved = load_saved(
                output, digest, args.policy, args.model,
                args.minimum, args.top_k, keys
            )
            print(f"Progress: {len(saved['results'])}/{len(keys)}")
            print("Summary:", summarize_semantic(saved))
            return 0
        print("Running real local embedding retrieval and Qwen answers.")
        print("No personal SQLite memory data is read or modified.")
        report = run_all_semantic(
            data, digest, args.policy, output=output,
            model=args.model, minimum=args.minimum, top_k=args.top_k,
            limit=args.limit
        )
        print("Saved:", output)
        print("Summary:", summarize_semantic(report))
        print("Author-defined development indicators, NOT model accuracy.")
        return 0
    except (OSError, ValueError, TypeError, KeyError) as error:
        print("Semantic development run stopped:", error)
        print("Earlier completed scenarios remain saved. Rerun to resume.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
