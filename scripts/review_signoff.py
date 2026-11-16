"""Provenance-preserving signoff for AI-generated Phase 8 labels.

Only an explicit user action can approve a draft. Bulk and per-case review
are distinguishable from edits. AI-generated answers never become independent
human ground truth. This module never invokes Qwen or modifies memorylab.db.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from scripts.auto_review_holdout_v2 import OUTPUT as AI_OUTPUT
from scripts.review_eval_cases import save_review
from scripts.review_holdout_v2 import (
    ACTIONS_FOR_LABEL, consistency_warnings, load_local_cases,
)

ROOT = Path(__file__).resolve().parents[1]
SIGNOFF_FILE = ROOT / "results" / "raw" / "holdout_v2_human_signoff.json"
REPORT_DIR = ROOT / "results" / "raw"
AXES = ("same_entity", "same_attribute",
        "old_fact_known_obsolete", "new_value_known")
EVIDENCE = {"yes", "no", "unknown"}
LABELS = set(ACTIONS_FOR_LABEL)
ACTIONS = set(ACTIONS_FOR_LABEL.values())


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def load_ai_drafts(path=AI_OUTPUT, cases=None, digest=None):
    """Only accept a completed and explicitly AI-generated review file."""
    if cases is None or digest is None:
        cases, digest = load_local_cases()
    raw = Path(path).read_bytes()
    content = json.loads(raw)
    ids = {c["id"] for c in cases}
    if (
        content.get("dataset_sha256") != digest
        or content.get("reviewer_type") != "automated_llm_not_human"
        or content.get("independent_ground_truth") is not False
        or not isinstance(content.get("judge_model"), str)
    ):
        raise ValueError("Invalid AI provenance or changed dataset.")
    answers = content.get("answers")
    if not isinstance(answers, dict) or set(answers) != ids:
        raise ValueError(
            "Finish AI triage before reviewing the report. "
            + str(len(answers) if isinstance(answers, dict) else 0)
            + "/" + str(len(cases)) + " cases present."
        )
    for cid, item in answers.items():
        if (not isinstance(item, dict)
            or item.get("reviewer_type") != "automated_llm_not_human"
            or item.get("provisional_label") not in LABELS
            or not isinstance(item.get("reason"), str)
            or not item["reason"].strip()
            or not isinstance(item.get("axes"), dict)
            or set(item["axes"]) != set(AXES)
            or any(item["axes"][k] not in EVIDENCE for k in AXES)
            or item.get("model_storage_action") not in ACTIONS
            or item.get("triage") not in ("draft", "needs_review")):
            raise ValueError("Invalid AI draft for " + cid)
    return content, hashlib.sha256(raw).hexdigest()


def draft_decision(ai_item):
    return {
        "label": ai_item["provisional_label"],
        "reason": ai_item["reason"],
        "axes": dict(ai_item["axes"]),
        "storage_action": ai_item["model_storage_action"],
    }


def validate_decision(decision):
    if not isinstance(decision, dict) or decision.get("label") not in LABELS:
        raise ValueError("Choose a supported relationship.")
    if not isinstance(decision.get("reason"), str) or not decision["reason"].strip():
        raise ValueError("A clear explanation is required.")
    axes = decision.get("axes")
    if not isinstance(axes, dict) or set(axes) != set(AXES):
        raise ValueError("All four evidence checks are required.")
    if any(axes[k] not in EVIDENCE for k in AXES):
        raise ValueError("Evidence must be yes, no or unknown.")
    if decision.get("storage_action") not in ACTIONS:
        raise ValueError("Choose a valid storage action.")
    problems = consistency_warnings(decision)
    if problems:
        raise ValueError("; ".join(problems))


def empty_signoff(digest, ai_sha, model):
    return {
        "version": 1,
        "method": "AI-first, human-reviewed",
        "independently_human_labelled": False,
        "dataset_sha256": digest,
        "ai_source_sha256": ai_sha,
        "model": model,
        "decisions": {},
        "audit": [],
    }


def load_signoff(path, digest, ai_sha, model, ids):
    path = Path(path)
    if not path.exists():
        return empty_signoff(digest, ai_sha, model)
    data = json.loads(path.read_text(encoding="utf-8"))
    if (data.get("version") != 1
        or data.get("method") != "AI-first, human-reviewed"
        or data.get("independently_human_labelled") is not False
        or data.get("dataset_sha256") != digest
        or data.get("ai_source_sha256") != ai_sha
        or data.get("model") != model):
        raise ValueError(
            "The AI source or dataset changed after review began. "
            "Original signoffs remain saved and are not overwritten."
        )
    decisions = data.get("decisions")
    if (not isinstance(decisions, dict)
        or not set(decisions).issubset(ids)
        or not isinstance(data.get("audit"), list)):
        raise ValueError("Signoff file has invalid content.")
    for cid, record in decisions.items():
        if record.get("method") not in ("individual", "corrected", "bulk_attested"):
            raise ValueError("Unknown review method in " + cid)
        validate_decision(record["final"])
    return data


def approve_one(data, cid, decision, draft, mode=None):
    validate_decision(decision)
    original = draft_decision(draft)
    if mode is None:
        mode = "individual" if decision == original else "corrected"
    if mode not in ("individual", "corrected", "bulk_attested"):
        raise ValueError("Invalid approval type.")
    if mode == "bulk_attested" and decision != original:
        raise ValueError("Bulk approval cannot silently edit an AI draft.")
    entry = {
        "final": {
            "label": decision["label"],
            "reason": decision["reason"].strip(),
            "axes": dict(decision["axes"]),
            "storage_action": decision["storage_action"],
        },
        "method": mode,
        "reviewed_at": utcnow(),
    }
    data["audit"].append({
        "case_id": cid, "action": mode, "at": entry["reviewed_at"],
        "previous": data["decisions"].get(cid),
        "new": entry,
    })
    data["decisions"][cid] = entry


def approve_unflagged(data, ai_report, ids, attested=False):
    """Bulk approval is a user attestation, NOT independent human labelling."""
    if not attested:
        raise ValueError("Please attest that you reviewed the report.")
    count = 0
    for cid in ids:
        if cid in data["decisions"]:
            continue
        ai = ai_report["answers"][cid]
        if ai["triage"] != "draft":
            continue
        decision = draft_decision(ai)
        try:
            validate_decision(decision)
        except ValueError:
            continue
        approve_one(data, cid, decision, ai, mode="bulk_attested")
        count += 1
    return count


def review_stats(data, cases):
    counts = {"individual": 0, "corrected": 0, "bulk_attested": 0}
    for row in data["decisions"].values():
        counts[row["method"]] += 1
    return {
        "total": len(cases), "approved": len(data["decisions"]),
        "remaining": len(cases) - len(data["decisions"]),
        **counts,
    }


def markdown_report(cases, ai_report, signoff):
    """Report AI provenance, each draft, each final decision, and signoff type."""
    if set(signoff["decisions"]) != {case["id"] for case in cases}:
        raise ValueError("Every case needs explicit human signoff first.")
    stats = review_stats(signoff, cases)
    lines = [
        "# MemoryLab — AI-assisted, human-reviewed annotation report",
        "",
        "AI generated the initial labels and explanations. A human reviewer "
        "approved the drafts or corrected them, including bulk-attested cases.",
        "",
        "**This is not independent human annotation or validated accuracy.** "
        "Bulk-attested cases are not individually approved. Human oversight "
        "does not transform AI drafts into an independent evaluation set.",
        "",
        "- Model: " + ai_report["judge_model"],
        "- Dataset fingerprint: " + ai_report["dataset_sha256"],
        "- AI output fingerprint: " + signoff["ai_source_sha256"],
        "- Approved: " + str(stats["approved"]) + "/" + str(stats["total"]),
        "- Individually approved: " + str(stats["individual"]),
        "- Human-corrected: " + str(stats["corrected"]),
        "- Bulk-attested: " + str(stats["bulk_attested"]),
        "",
        "## Summary",
        "| Case | AI label | Final label | Approval type |",
        "|---|---|---|---|",
    ]
    for c in cases:
        cid = c["id"]
        ai = ai_report["answers"][cid]
        final = signoff["decisions"][cid]
        lines.append(
            "| " + cid + " | " + ai["provisional_label"] + " | "
            + final["final"]["label"] + " | " + final["method"] + " |"
        )
    lines += ["", "## Individual case details", ""]
    for c in cases:
        cid = c["id"]
        ai = ai_report["answers"][cid]
        final = signoff["decisions"][cid]
        d = final["final"]
        lines += [
            "### " + cid + " — " + c["topic"], "",
            "**Old:** " + c["old_fact"],
            "**New:** " + c["new_fact"],
            "**AI-generated label:** " + ai["provisional_label"],
            "**AI-generated explanation:** " + ai["reason"],
            "**Original AI warnings:** "
            + ", ".join(ai.get("flags", [])) if ai.get("flags") else
            "**Original AI warnings:** None",
            "**Human-reviewed label:** " + d["label"],
            "**Final explanation:** " + d["reason"],
            "**Evidence:** " + ", ".join(k + "=" + d["axes"][k] for k in AXES),
            "**Storage suggestion (NOT executed):** " + d["storage_action"],
            "**Human action:** " + final["method"], "",
        ]
    lines += [
        "## Scope",
        "All facts here are fictional. No SQLite memories were modified. "
        "AI suggestions, bulk human attestation and individual human edits "
        "must remain identifiable in any portfolio claim.", ""
    ]
    return "\n".join(lines)


def write_report(cases, ai, signoff, folder=REPORT_DIR):
    markdown = markdown_report(cases, ai, signoff)
    revision = hashlib.sha256(json.dumps(
        {"source": signoff["ai_source_sha256"],
         "decisions": signoff["decisions"]},
        sort_keys=True).encode("utf-8")).hexdigest()[:12]
    path = Path(folder) / ("holdout_v2_human_reviewed_" + revision + ".md")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with path.open("x", encoding="utf-8") as f:
            f.write(markdown)
    return path


def save_signoff(data, path=SIGNOFF_FILE):
    save_review(data, path)
