"""Record a human V1.0 UI acceptance walkthrough as a Markdown report.

Run AFTER closing the isolated demo:
    python -m scripts.record_v1_manual_qa

The questions must be answered from actually observing the running
Streamlit app. This script NEVER connects to a database, accesses Ollama,
or simulates a passing UI test. Every run writes a NEW numbered report.
Use only fictional examples and do not paste private user memories.
"""
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULT_DIR = ROOT / "results" / "raw"

CHECKS = (
    ("UI01", "First fictional memory", "New topic saved; appears in active search."),
    ("UI02", "Compatible fact remains", "Added a different attribute via Smart Memory Review; both facts remain active."),
    ("UI03", "Selective supersession", "Updated one old attribute; the other active attribute remains."),
    ("UI04", "Duplicate protection", "Exact duplicate was refused and memory history did not gain a duplicate."),
    ("UI05", "Baseline warning", "Section 1 warned about same-topic bulk supersession; button disabled without acknowledgement."),
    ("UI06", "History and active status", "Superseded fact visible as inactive; newer and compatible facts active."),
    ("UI07", "Retrieval and supported answer", "Semantically retrieved relevant evidence and inspected Qwen answer against facts."),
    ("UI08", "Unsupported question observation", "Record Qwen's actual response to a question NOT established by memory, even if hallucinated."),
)
REGULAR = ("pass", "fail", "not_tested")
OBSERVATION = ("observed", "fail", "not_tested")


def valid_entry(case_id, status, notes):
    codes = {case[0] for case in CHECKS}
    if case_id not in codes:
        raise ValueError("Unknown UI acceptance check.")
    allowed = OBSERVATION if case_id == "UI08" else REGULAR
    if status not in allowed:
        raise ValueError("Unsupported status for this manual check.")
    if not isinstance(notes, str):
        raise ValueError("Manual notes must be text.")
    if status in ("fail", "observed") and not notes.strip():
        raise ValueError("Describe what happened on failures or observations.")
    return {
        "id": case_id, "status": status, "notes": notes.strip(),
    }


def report_text(entries):
    ids = {c[0] for c in CHECKS}
    if set(e["id"] for e in entries) != ids or len(entries) != len(CHECKS):
        raise ValueError("Report requires one recorded result for every check.")
    findings = {e["id"]: e for e in entries}
    operational = [findings[x[0]] for x in CHECKS if x[0] != "UI08"]
    passed = sum(e["status"] == "pass" for e in operational)
    failed = sum(e["status"] == "fail" for e in operational)
    remaining = sum(e["status"] == "not_tested" for e in operational)
    title = (
        "Operational UI checks passed (manual attestation only)"
        if passed == len(operational) else
        "Manual UI acceptance incomplete or failed"
    )
    lines = [
        "# MemoryLab V1.0 — Manual UI acceptance record",
        "",
        "**" + title + "**",
        "",
        "Recorded: " + datetime.now(timezone.utc).isoformat(),
        "",
        "**Provenance:** User-entered observations of a local fictional-data "
        "demo. This script does not execute the app or independently verify "
        "its behaviour. The seven functional checks differ from the eighth "
        "answer-reliability observation; they do not certify LLM truthfulness.",
        "",
        f"- Functional checks passed: {passed}/7",
        f"- Functional checks failed: {failed}/7",
        f"- Functional checks not tested: {remaining}/7",
        "",
        "| Check | What to verify | Recorded result |",
        "|---|---|---|",
    ]
    for cid, name, expected in CHECKS:
        row = findings[cid]
        lines.append("| " + cid + " — " + name
                     + " | " + expected.replace("|", "/")
                     + " | " + row["status"] + " |")
    lines += ["", "## Actual observations", ""]
    for cid, name, _ in CHECKS:
        entry = findings[cid]
        lines += [
            "### " + cid + ": " + name,
            "",
            "**Result:** " + entry["status"],
            "",
            "**Notes:** " + (entry["notes"] or "(No notes provided.)"),
            "",
        ]
    lines += [
        "## Release interpretation", "",
        "Do not mark the project release-ready merely because these manual "
        "records show PASS. Automated checks, privacy review, clean install, "
        "and clear experimental limitations are separate gates. Even a "
        "fully documented unsupported question does not prove the answer "
        "model reliably abstains. This report must not contain personal "
        "memory text, credentials or real user data.",
        "",
    ]
    return "\n".join(lines)


def next_output(folder=RESULT_DIR):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    for count in range(1, 10000):
        path = folder / f"v1_manual_acceptance_{count:03d}.md"
        if not path.exists():
            return path
    raise RuntimeError("Too many manual acceptance reports.")


def collect(prompt=input, say=print):
    entries = []
    say("MemoryLab V1.0 manual QA — report actual observations, never guesses.")
    say("Use only fictional facts. You can mark anything not tested.")
    for cid, name, expected in CHECKS:
        say("")
        say(cid + ": " + name)
        say("Expected / observe: " + expected)
        statuses = OBSERVATION if cid == "UI08" else REGULAR
        while True:
            status = prompt("Outcome (" + "/".join(statuses) + "): ").strip().lower()
            if status in statuses:
                break
            say("Choose one of: " + ", ".join(statuses))
        while True:
            notes = prompt("What happened? (brief notes; no real memories): ").strip()
            try:
                entries.append(valid_entry(cid, status, notes))
                break
            except ValueError as error:
                say(str(error))
    return entries


def main():
    try:
        entries = collect()
        destination = next_output()
        with destination.open("x", encoding="utf-8") as out:
            out.write(report_text(entries))
    except (OSError, ValueError, KeyboardInterrupt, EOFError) as error:
        print("Manual QA not saved:", error)
        return 1
    print("Saved new manual acceptance report:", destination)
    print("Upload the report for release verification. It is not automatic UI proof.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
