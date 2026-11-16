"""Phase 10: downstream memory-state and answer development evaluation.

This is NOT an independent model-accuracy benchmark. The new fictional
scenarios and expected answers were project-authored; reviewed decisions
are scripted, not predicted by a model. ALL writes use temporary SQLite
files, never memorylab.db.

Run offline state comparison (no model):
    python -m scripts.evaluate_downstream_memory

Optionally call the EXISTING local Qwen answer generator with all active
memories, one condition at a time:
    python -m scripts.evaluate_downstream_memory --with-llm --policy reviewed
    python -m scripts.evaluate_downstream_memory --with-llm --policy all

Progress is saved after every completed scenario; rerun to resume.
Optional --limit 3 runs three scenarios per policy for an initial smoke test.
Outputs are in Git-ignored results/raw/phase10_<mode>_<policy>.json/.md.
"""
import argparse
import hashlib
import json
import re
import sqlite3
import tempfile
from collections import Counter
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from answer_generator import DEFAULT_CHAT_MODEL, NO_MEMORY_ANSWER, generate_answer
from memory_store import save_reviewed_memory
from scripts.review_eval_cases import save_review

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "benchmarks" / "downstream_memory_v1.json"
RAW_DIR = ROOT / "results" / "raw"
POLICIES = ("reviewed", "append_all", "topic_overwrite")
RELATIONS = ("initial", "replaces", "coexists", "duplicate", "uncertain")

SCHEMA_SQL = (
    "CREATE TABLE memories ("
    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
    "topic TEXT NOT NULL, fact TEXT NOT NULL, "
    "created_at TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1)"
)


def load_dataset(path=DATASET):
    raw = Path(path).read_bytes()
    data = json.loads(raw)
    if not isinstance(data, dict) or data.get("version") != 1:
        raise ValueError("Expected Phase 10 dataset format version 1.")
    cases = data.get("scenarios")
    if not isinstance(cases, list) or not cases:
        raise ValueError("At least one scenario is required.")
    seen = set()
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("id"), str):
            raise ValueError("Malformed scenario.")
        if case["id"] in seen:
            raise ValueError("Duplicate scenario identifier: " + case["id"])
        seen.add(case["id"])
        steps = case.get("steps")
        questions = case.get("checks")
        if not isinstance(steps, list) or not steps or not isinstance(questions, list) or not questions:
            raise ValueError("Each scenario needs steps and checks.")
        known, skipped, superseded = set(), set(), set()
        for index, step in enumerate(steps):
            if not isinstance(step, dict) or not all(
                isinstance(step.get(k), str) and step[k].strip()
                for k in ("id", "topic", "fact", "relation")
            ):
                raise ValueError("Every step needs a nonempty id, topic, fact, relation.")
            sid = step["id"]
            rel = step["relation"]
            if sid in known or rel not in RELATIONS:
                raise ValueError("Repeated step or unsupported relation in " + case["id"])
            if (index == 0) != (rel == "initial"):
                raise ValueError("Only the first step may be initial.")
            targets = step.get("supersede", [])
            if not isinstance(targets, list) or len(set(targets)) != len(targets):
                raise ValueError("Invalid supersede target list.")
            if rel == "replaces":
                if not targets or not set(targets).issubset(known - skipped - superseded):
                    raise ValueError("Replacement must name earlier active step IDs.")
                superseded.update(targets)
            elif targets:
                raise ValueError("Only a replacement step can name superseded memories.")
            if rel == "duplicate":
                skipped.add(sid)
            known.add(sid)
        expected = case.get("expected_active")
        if not isinstance(expected, list) or len(set(expected)) != len(expected):
            raise ValueError("expected_active must be a unique list.")
        inferred = known - skipped - superseded
        if set(expected) != inferred:
            raise ValueError(
                f"{case['id']}: expected_active must match authored step actions."
            )
        checks_seen = set()
        for check in questions:
            if not isinstance(check, dict) or not all(
                isinstance(check.get(k), str) and check[k].strip()
                for k in ("id", "question")
            ):
                raise ValueError("Each answer check needs id and question.")
            if check["id"] in checks_seen:
                raise ValueError("Repeated question ID in " + case["id"])
            checks_seen.add(check["id"])
            supports = check.get("support_steps")
            if not isinstance(supports, list) or not set(supports).issubset(known):
                raise ValueError("Question references an unknown fact step.")
            abstain = check.get("expect_abstention") is True
            phrases = check.get("expected_phrases", [])
            if (not isinstance(phrases, list)
                or any(not isinstance(p, str) or not p.strip() for p in phrases)
                or (abstain and phrases) or (not abstain and not phrases)):
                raise ValueError("Provide answer phrases OR expect_abstention.")
    return data, hashlib.sha256(raw).hexdigest()


def sql_active(path, topic=None):
    with closing(sqlite3.connect(path)) as conn:
        if topic is None:
            rows = conn.execute(
                "SELECT id,topic,fact FROM memories WHERE active=1 ORDER BY id"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id,topic,fact FROM memories "
                "WHERE active=1 AND topic=? ORDER BY id", (topic,)
            ).fetchall()
    return [{"id": mid, "topic": t, "fact": f} for mid, t, f in rows]


def sql_insert(path, topic, fact, *, overwrite=False):
    with closing(sqlite3.connect(path)) as conn, conn:
        if overwrite:
            conn.execute(
                "UPDATE memories SET active=0 WHERE active=1 AND topic=?",
                (topic,)
            )
        cursor = conn.execute(
            "INSERT INTO memories(topic,fact,created_at,active) "
            "VALUES(?,?,?,1)",
            (topic, fact, "synthetic_step")
        )
        return cursor.lastrowid


def load_into_temporary_store(case, policy):
    """Apply scripted policies; real reviewed writes use memory_store.py."""
    if policy not in POLICIES:
        raise ValueError("Unsupported policy.")
    with tempfile.TemporaryDirectory(prefix="memorylab_phase10_") as tmp:
        db_path = str(Path(tmp) / "test.sqlite3")
        with closing(sqlite3.connect(db_path)) as conn, conn:
            conn.execute(SCHEMA_SQL)
        step_to_mid = {}
        for step in case["steps"]:
            topic = step["topic"].strip().lower()
            fact = step["fact"].strip()
            if policy == "reviewed":
                if step["relation"] == "duplicate":
                    # An explicitly authored human-like decision, NOT a model.
                    # Deliberately skip a semantic repeat without DB mutation.
                    continue
                current = sql_active(db_path, topic)
                ids = [memory["id"] for memory in current]
                target_ids = {
                    step_to_mid[sid] for sid in step.get("supersede", [])
                }
                decisions = {
                    mid: "supersede" if mid in target_ids else "keep"
                    for mid in ids
                }
                mid = save_reviewed_memory(
                    topic, fact, decisions, ids, db_path=db_path
                )
            elif policy == "topic_overwrite":
                # Same broad-topic overwrite semantics as app.py's baseline.
                mid = sql_insert(db_path, topic, fact, overwrite=True)
            else:
                mid = sql_insert(db_path, topic, fact)
            step_to_mid[step["id"]] = mid
        active = sql_active(db_path)
        mids = {mem["id"] for mem in active}
        active_steps = [
            step["id"] for step in case["steps"]
            if step["id"] in step_to_mid and step_to_mid[step["id"]] in mids
        ]
        return active, active_steps


def phrase_present(answer, phrase):
    """Simple lexical proxy for an answer; NOT semantic truth checking."""
    normalized = " ".join(answer.casefold().split())
    p = " ".join(phrase.casefold().split())
    return bool(re.search(r"(?<!\w)" + re.escape(p) + r"(?!\w)", normalized))


def is_abstention(answer):
    answer = answer.casefold()
    indicators = (
        NO_MEMORY_ANSWER.casefold(), "don't have enough information",
        "do not have enough information", "is not specified",
        "not enough information", "not provided", "not mentioned",
        "cannot determine", "can't determine", "doesn't say",
        "not in the memories", "not established", "unclear from",
        "don't know", "do not know",
    )
    return any(text in answer for text in indicators)


def score_text_answer(check, answer):
    """Strict proxy: literal keywords or an abstention phrase, not accuracy."""
    if check.get("expect_abstention") is True:
        return {
            "text_proxy_pass": is_abstention(answer),
            "rule": "contains_recognized_abstention_phrase",
        }
    return {
        "text_proxy_pass": (
            any(phrase_present(answer, p) for p in check["expected_phrases"])
            and not is_abstention(answer)
        ),
        "rule": "includes_author_keyword_and_no_abstention_phrase",
    }


def run_scenario(case, policy, *, answer_fn=None, model=DEFAULT_CHAT_MODEL):
    """One self-contained scenario, isolated from all user memory data."""
    active, active_steps = load_into_temporary_store(case, policy)
    expected = set(case["expected_active"])
    actual = set(active_steps)
    superseded = {
        sid for step in case["steps"] for sid in step.get("supersede", [])
    }
    result = {
        "scenario": case["id"], "title": case["title"],
        "policy": policy,
        "expected_active_steps": case["expected_active"],
        "active_steps": active_steps,
        "missing_expected_steps": sorted(expected - actual),
        "unexpected_active_steps": sorted(actual - expected),
        "stale_old_steps_active": sorted(superseded & actual),
        "exact_active_state": expected == actual,
        "active_memories": active,
        "checks": [],
    }
    for check in case["checks"]:
        support = check["support_steps"]
        row = {
            "id": check["id"], "question": check["question"],
            "expected_phrases": check.get("expected_phrases", []),
            "expect_abstention": check.get("expect_abstention") is True,
            "support_steps": support,
            "support_available": (
                set(support).issubset(actual) if support else None
            ),
        }
        if answer_fn is not None:
            answer = answer_fn(
                check["question"], active, model=model
            )
            if not isinstance(answer, str):
                raise ValueError("Answer generator returned non-string data.")
            row["answer"] = answer
            row.update(score_text_answer(check, answer))
        result["checks"].append(row)
    return result


def summarize(results):
    """Separate storage-state measures from lexical answer-proxy measures."""
    output = {}
    for policy in POLICIES:
        rows = [r for r in results.values() if r["policy"] == policy]
        if not rows:
            continue
        queries = [c for r in rows for c in r["checks"]]
        supported = [c for c in queries if c["support_available"] is not None]
        graded = [c for c in queries if "text_proxy_pass" in c]
        output[policy] = {
            "scenarios": len(rows),
            "state_exact": sum(r["exact_active_state"] for r in rows),
            "missing_expected_steps": sum(
                len(r["missing_expected_steps"]) for r in rows
            ),
            "unexpected_active_steps": sum(
                len(r["unexpected_active_steps"]) for r in rows
            ),
            "stale_old_steps_active": sum(
                len(r["stale_old_steps_active"]) for r in rows
            ),
            "questions": len(queries),
            "known_support_available": sum(
                c["support_available"] is True for c in supported
            ),
            "known_support_total": len(supported),
            "llm_text_proxy_passes": sum(
                c["text_proxy_pass"] is True for c in graded
            ),
            "llm_text_proxy_total": len(graded),
        }
    return output


def make_report(data):
    summary = summarize(data["results"])
    lines = [
        "# Phase 10 — Synthetic downstream memory outcome development report",
        "",
        "**Not independent model accuracy.** Cases, review decisions and expected "
        "answer keywords were authored inside MemoryLab. The scripted "
        "reviewed policy is a reference implementation check, NOT an "
        "autonomous learned classifier.",
        "",
        "- Dataset SHA-256: " + data["dataset_sha256"],
        "- Answer model: " + (
            data["model"] if data["with_llm"] else "not called (offline)"
        ),
        "- Policies: " + ", ".join(data["policies"]),
        "- Storage: temporary SQLite databases, no user records accessed",
        "- Retrieval: all active facts passed to the unchanged answer "
        "generator; embedding similarity/retrieval is NOT tested",
        "- Answer scoring: literal author keyword and abstention-phrase "
        "proxies; not judged semantic correctness",
        "",
        "## Policy comparison",
        "",
        "| Policy | Scenarios | Exact active sets | Missing required facts | "
        "Extra active facts | Obsolete facts retained | "
        "Available answer support | Text-proxy matches |",
        "|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for policy in data["policies"]:
        if policy not in summary:
            continue
        row = summary[policy]
        proxy = (
            f"{row['llm_text_proxy_passes']}/{row['llm_text_proxy_total']}"
            if row["llm_text_proxy_total"] else "not run"
        )
        lines.append(
            f"| {policy} | {row['scenarios']} | {row['state_exact']} "
            f"| {row['missing_expected_steps']} | {row['unexpected_active_steps']} "
            f"| {row['stale_old_steps_active']} "
            f"| {row['known_support_available']}/{row['known_support_total']} "
            f"| {proxy} |"
        )
    lines += ["", "## Case details", ""]
    for key, item in data["results"].items():
        lines += [
            f"### {key}: {item['title']}",
            "",
            f"- Expected active source steps: {', '.join(item['expected_active_steps'])}",
            f"- Actual active source steps: {', '.join(item['active_steps'])}",
            f"- Missing: {', '.join(item['missing_expected_steps']) or 'none'}",
            f"- Extra: {', '.join(item['unexpected_active_steps']) or 'none'}",
            f"- Outdated steps still active: {', '.join(item['stale_old_steps_active']) or 'none'}",
            "",
        ]
        for q in item["checks"]:
            lines.append(
                f"**{q['id']}** {q['question']} "
                f"(support retained: {q['support_available']})"
            )
            if "answer" in q:
                lines.append(
                    "Model answer: "
                    + q["answer"].replace("\n", " ")[:700]
                    + " | literal proxy pass: " + str(q["text_proxy_pass"])
                )
            lines.append("")
    lines += [
        "## Interpretation limits and next research step",
        "",
        "The reviewed policy receives *author-approved* storage actions. Its "
        "success in retaining author-specified facts does not demonstrate "
        "that Qwen can choose those actions; that is a separate evaluation. "
        "Using the same cases to design and tune a model would invalidate "
        "a subsequent blind holdout claim.",
        "",
        "The optional Qwen calls use full active memory context, without "
        "embeddings or similarity thresholds. Changes in generated answers "
        "can be caused by model behavior as well as memory state, not "
        "retrieval accuracy. Keyword matching can misgrade negation, "
        "paraphrases, historical references or unsupported statements. "
        "Any meaningful quality claims need blind independent labels, "
        "a human audit of generated answers, and testing the complete "
        "retrieval pipeline.",
        "",
    ]
    return "\n".join(lines)


def new_result(digest, policies, model, with_llm):
    return {
        "version": 1,
        "method": "project_authored_development_not_independent_accuracy",
        "dataset_sha256": digest,
        "policies": list(policies),
        "model": model if with_llm else None,
        "with_llm": with_llm,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "results": {},
    }


def load_result(path, digest, policies, model, with_llm, allowed_keys):
    path = Path(path)
    if not path.exists():
        return new_result(digest, policies, model, with_llm)
    saved = json.loads(path.read_text(encoding="utf-8"))
    expected = new_result(digest, policies, model, with_llm)
    for k in ("version", "method", "dataset_sha256", "policies",
              "model", "with_llm"):
        if saved.get(k) != expected[k]:
            raise ValueError(
                "Existing Phase 10 file has different configuration/dataset. "
                "Refusing to mix or overwrite research runs."
            )
    if (not isinstance(saved.get("results"), dict)
            or not set(saved["results"]).issubset(allowed_keys)):
        raise ValueError("Phase 10 file contains unknown result keys.")
    return saved


def run_all(dataset, digest, policies, *, answer_fn=None,
            model=DEFAULT_CHAT_MODEL, limit=None, output=None, log=print):
    """Resume per (scenario,policy) and save one completed scenario at a time."""
    if output is None:
        raise ValueError("Specify a local output path.")
    allowed = {
        case["id"] + "_" + policy
        for case in dataset["scenarios"] for policy in policies
    }
    state = load_result(
        output, digest, policies, model,
        answer_fn is not None, allowed
    )
    for case in dataset["scenarios"][:limit]:
        for policy in policies:
            key = case["id"] + "_" + policy
            if key in state["results"]:
                continue
            row = run_scenario(
                case, policy, answer_fn=answer_fn, model=model
            )
            state["results"][key] = row
            save_review(state, output)
            log(
                f"{key}: active={row['active_steps']} "
                f"exact={row['exact_active_state']}"
            )
    if len(state["results"]) == len(allowed):
        md = Path(output).with_suffix(".md")
        if not md.exists():
            md.parent.mkdir(parents=True, exist_ok=True)
            with md.open("x", encoding="utf-8") as out:
                out.write(make_report(state))
            log(f"Finished. Markdown report: {md}")
        else:
            log(f"Finished. Existing Markdown preserved: {md}")
    else:
        log(f"Progress saved: {len(state['results'])}/{len(allowed)} scenario/policy runs")
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--with-llm", action="store_true",
                        help="Call the existing local Qwen answer generator.")
    parser.add_argument("--policy", choices=("all",) + POLICIES, default="all")
    parser.add_argument("--model", default=DEFAULT_CHAT_MODEL)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive.")
    try:
        data, sha = load_dataset()
        policies = POLICIES if args.policy == "all" else (args.policy,)
        mode = "llm" if args.with_llm else "storage"
        output = args.output or RAW_DIR / f"phase10_{mode}_{args.policy}.json"
        keys = {
            case["id"] + "_" + p
            for case in data["scenarios"] for p in policies
        }
        if args.status:
            current = load_result(
                output, sha, policies, args.model, args.with_llm, keys
            )
            print(f"Progress: {len(current['results'])}/{len(keys)}")
            print("Current summary:", summarize(current["results"]))
            return 0
        print("Synthetic development run. No live memorylab.db will be used.")
        print("Answer model:", args.model if args.with_llm else "disabled")
        state = run_all(
            data, sha, policies,
            answer_fn=generate_answer if args.with_llm else None,
            model=args.model, limit=args.limit, output=output
        )
        print("Results:", output)
        print("Summary:", summarize(state["results"]))
        print("Author-defined checks only; NOT independent accuracy.")
        return 0
    except (OSError, ValueError, TypeError, KeyError, sqlite3.Error) as err:
        print("Phase 10 stopped:", err)
        print("Earlier completed scenarios remain saved. Rerun to resume.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
