"""Phase 13: reviewer labels for a fresh project-curated answer challenge.

No AI answers, probe warnings, or ground-truth labels are displayed by
this module. A separate UI calls it to collect single-reviewer judgments
BEFORE a diagnostic report can be generated. The cases are authored
within MemoryLab: blinded *to the probe*, not independently sourced.

No Ollama, network, personal memory DB or changes to earlier results.
"""
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "benchmarks" / "answer_claims_v1.json"
SIGNOFF = ROOT / "results" / "raw" / "phase13_answer_signoff.json"
LABELS = ("supported", "unsupported", "uncertain")
METHOD = "project_curated_single_reviewer_blind_to_probe"


def now():
    return datetime.now(timezone.utc).isoformat()


def load_dataset(path=DATASET):
    raw = Path(path).read_bytes()
    data = json.loads(raw)
    if not isinstance(data, dict) or data.get("version") != 1:
        raise ValueError("Invalid Phase 13 dataset/version.")
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("Expected nonempty challenge cases.")
    ids = set()
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("id"), str):
            raise ValueError("Invalid case ID.")
        if case["id"] in ids:
            raise ValueError("Repeated case ID.")
        ids.add(case["id"])
        if not all(isinstance(case.get(k), str) and case[k].strip()
                   for k in ("question", "candidate_answer")):
            raise ValueError("Missing candidate answer or question.")
        memories = case.get("retrieved_memories")
        if not isinstance(memories, list) or not memories:
            raise ValueError("Every case requires source memories.")
        mids = set()
        for mem in memories:
            if (not isinstance(mem, dict)
                or not isinstance(mem.get("id"), int)
                or isinstance(mem["id"], bool)
                or mem["id"] in mids
                or not isinstance(mem.get("fact"), str)
                or not mem["fact"].strip()):
                raise ValueError("Invalid source memory.")
            mids.add(mem["id"])
        if any(key in case for key in ("gold_label", "truth", "probe_status")):
            raise ValueError("Review cases must not embed ground truth or probe status.")
    return data, hashlib.sha256(raw).hexdigest()


def new_signoff(digest):
    return {
        "format_version": 1,
        "dataset_sha256": digest,
        "review_method": METHOD,
        "independent_source_ground_truth": False,
        "blind_to_probe_output": True,
        "created_at": now(),
        "locked_at": None,
        "decisions": {},
        "audit_events": [],
    }


def load_signoff(path, digest, case_ids):
    target = Path(path)
    if not target.exists():
        return new_signoff(digest)
    saved = json.loads(target.read_text(encoding="utf-8"))
    if (saved.get("format_version") != 1
        or saved.get("dataset_sha256") != digest
        or saved.get("review_method") != METHOD
        or saved.get("independent_source_ground_truth") is not False
        or saved.get("blind_to_probe_output") is not True):
        raise ValueError("Existing signoff has incompatible provenance/dataset.")
    decisions = saved.get("decisions")
    events = saved.get("audit_events")
    if (not isinstance(decisions, dict) or not set(decisions).issubset(case_ids)
        or not isinstance(events, list)):
        raise ValueError("Invalid saved review IDs or audit structure.")
    for cid, record in decisions.items():
        if (not isinstance(record, dict)
            or record.get("label") not in LABELS
            or not isinstance(record.get("rationale", ""), str)):
            raise ValueError("Malformed label: " + cid)
    for event in events:
        if (not isinstance(event, dict)
            or event.get("case_id") not in case_ids
            or event.get("label") not in LABELS):
            raise ValueError("Malformed audit event.")
    if saved.get("locked_at") is not None and (
        not isinstance(saved["locked_at"], str)
        or set(decisions) != case_ids
    ):
        raise ValueError("A locked signoff must contain every case.")
    return saved


def record_decision(signoff, case_id, label, rationale, case_ids):
    if signoff.get("locked_at") is not None:
        raise ValueError("Reviews are locked; original signoff preserved.")
    if case_id not in case_ids or label not in LABELS:
        raise ValueError("Invalid case ID or label.")
    if not isinstance(rationale, str):
        raise ValueError("Rationale must be text.")
    rationale = rationale.strip()
    if label == "uncertain" and not rationale:
        raise ValueError("Explain why the evidence is uncertain.")
    timestamp = now()
    entry = {"label": label, "rationale": rationale, "reviewed_at": timestamp}
    signoff["decisions"][case_id] = entry
    signoff["audit_events"].append({"case_id": case_id, **entry})
    return signoff


def lock_signoff(signoff, case_ids):
    if signoff.get("locked_at") is not None:
        raise ValueError("Already locked.")
    if set(signoff["decisions"]) != case_ids:
        raise ValueError("Every case must be reviewed before locking.")
    signoff["locked_at"] = now()
    return signoff


def save_signoff(signoff, path=SIGNOFF):
    """Atomically replace the local draft; prior decisions stay in audit."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(signoff, indent=2, ensure_ascii=False) + "\n"
    tempname = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=".phase13_", suffix=".tmp", delete=False
        ) as out:
            tempname = out.name
            out.write(payload)
            out.flush()
            os.fsync(out.fileno())
        os.replace(tempname, path)
    finally:
        if tempname is not None and Path(tempname).exists():
            Path(tempname).unlink()


def main():
    data, digest = load_dataset()
    path = SIGNOFF
    ids = {case["id"] for case in data["cases"]}
    saved = load_signoff(path, digest, ids)
    print(f"Phase 13: {len(saved['decisions'])}/{len(ids)} human decisions.")
    print("Locked:", bool(saved.get("locked_at")))
    print("Open review UI: python -m streamlit run app_answer_challenge.py")
    print("No model/probe scores are revealed before labels are locked.")


if __name__ == "__main__":
    main()
