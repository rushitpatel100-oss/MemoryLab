"""MemoryLab V1.0 release-readiness check; never opens the user memory DB.

One command:
    python -m scripts.v1_release_readiness

Checks the project layout, Git privacy exclusions, guarded baseline UI,
an isolated temporary SQLite selective-review scenario, installed Streamlit,
and the offline unit-test suite. Optionally check localhost Ollama models:

    python -m scripts.v1_release_readiness --check-models

Creates a unique numbered Markdown report under Git-ignored results/raw/.
A PASS is an engineering smoke-check, NOT a claim of model accuracy or
production readiness. Manual review, app UI smoke testing, and independent
holdout evaluation remain necessary.
"""
import argparse
import importlib.util
import json
import sqlite3
import subprocess
import sys
import tempfile
import urllib.request
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from memory_store import save_reviewed_memory

ROOT = Path(__file__).resolve().parents[1]
RESULT_DIR = ROOT / "results" / "raw"
SCHEMA = (
    "CREATE TABLE memories (id INTEGER PRIMARY KEY AUTOINCREMENT, "
    "topic TEXT NOT NULL, fact TEXT NOT NULL, created_at TEXT NOT NULL, "
    "active INTEGER NOT NULL DEFAULT 1)"
)
REQUIRED = (
    "app.py", "requirements.txt", "memory_store.py",
    "memory_review_safety.py", "answer_generator.py",
    "semantic_search.py", "tests", "README.md",
    "docs/experiment_021_results.md", "docs/v1_release_gate.md",
)


def project_layout(root=ROOT):
    missing = [name for name in REQUIRED if not (Path(root) / name).exists()]
    return (not missing, "Required project paths present." if not missing
            else "Missing paths: " + ", ".join(missing))


def privacy_exclusions(root=ROOT):
    ignore = Path(root) / ".gitignore"
    if not ignore.exists():
        return False, ".gitignore is missing."
    contents = ignore.read_text(encoding="utf-8")
    required = ("results/raw/", "*.db", "*.sqlite3", ".env", ".streamlit/secrets.toml")
    missing = [name for name in required if name not in contents]
    return (not missing, "Local result and database patterns configured."
            if not missing else "Missing ignore patterns: " + ", ".join(missing))


def guarded_baseline_ui(root=ROOT):
    path = Path(root) / "app.py"
    if not path.exists():
        return False, "app.py missing."
    code = path.read_text(encoding="utf-8")
    required = (
        "if baseline_existing:", "baseline_confirmed = st.checkbox(",
        "disabled=bool(baseline_existing) and not baseline_confirmed",
        "or demo_bulk_overwrite_blocked,",
        "ISOLATED DEMO SAFEGUARD",
        "new_id = save_reviewed_memory(",
    )
    missing = [value for value in required if value not in code]
    return (not missing, "Baseline overwrite acknowledgement and human reviewed writes found."
            if not missing else "Missing UI safeguards: " + ", ".join(missing))


def isolated_review_smoke():
    """Run the real selective storage API with an ephemeral test database."""
    with tempfile.TemporaryDirectory(prefix="memorylab_release_") as folder:
        db = str(Path(folder) / "fictional.sqlite3")
        with closing(sqlite3.connect(db)) as conn, conn:
            conn.execute(SCHEMA)
        first = save_reviewed_memory(
            "model studio", "The studio has a printing press.",
            {}, [], db_path=db,
        )
        second = save_reviewed_memory(
            "model studio", "The studio has a drying rack.",
            {first: "keep"}, [first], db_path=db,
        )
        third = save_reviewed_memory(
            "model studio", "The studio replaced the printing press with a laser cutter.",
            {first: "supersede", second: "keep"},
            [first, second], db_path=db,
        )
        with closing(sqlite3.connect(db)) as conn:
            rows = conn.execute(
                "SELECT id,active FROM memories ORDER BY id"
            ).fetchall()
        if rows != [(first, 0), (second, 1), (third, 1)]:
            return False, "Selective supersession retained an unexpected fact set."
        try:
            save_reviewed_memory(
                "model studio", "The studio has a drying rack.",
                {second: "keep", third: "keep"},
                [second, third], db_path=db,
            )
        except ValueError as error:
            if "Duplicate" not in str(error):
                return False, "Duplicate was rejected for an unexpected reason."
        else:
            return False, "Duplicate was unexpectedly inserted."
        try:
            save_reviewed_memory(
                "model studio", "Another new fact.",
                {second: "keep"}, [second], db_path=db,
            )
        except ValueError as error:
            if "changed" not in str(error):
                return False, "Stale-review protection failed unexpectedly."
        else:
            return False, "An outdated review was unexpectedly accepted."
        with closing(sqlite3.connect(db)) as conn:
            total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        if total != 3:
            return False, "A rejected write changed the database."
    return True, "Temporary SQLite: keep/coexist/supersede and duplicate/stale-review rollback passed."


def runtime_environment():
    if sys.version_info < (3, 10):
        return False, f"Python {sys.version.split()[0]} is too old (need 3.10+)."
    if importlib.util.find_spec("streamlit") is None:
        return False, "Streamlit not installed in the active Python environment."
    return True, "Python " + sys.version.split()[0] + " and Streamlit found."


def local_ollama_model_check():
    """Optional local-only HTTP check: never downloads or calls a model."""
    try:
        with urllib.request.urlopen(
            "http://127.0.0.1:11434/api/tags", timeout=6
        ) as response:
            data = json.load(response)
    except (OSError, ValueError, TypeError) as error:
        return False, "Local Ollama did not respond: " + str(error)
    names = {
        item.get("name", "").casefold()
        for item in data.get("models", [])
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    needed = {
        "qwen2.5:1.5b": any(n == "qwen2.5:1.5b" for n in names),
        "all-minilm": any(n.startswith("all-minilm") for n in names),
    }
    missing = [name for name, present in needed.items() if not present]
    if missing:
        return False, "Missing local Ollama models: " + ", ".join(missing)
    return True, "Qwen 2.5 1.5B and all-minilm tags detected locally."


def unit_tests(root=ROOT, timeout=240):
    """Run the actual offline unittest suite, not just count test files."""
    try:
        run = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
            cwd=root, text=True, capture_output=True, timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return False, "Could not finish offline tests: " + str(error)
    output = (run.stderr or run.stdout or "").strip()
    return (run.returncode == 0,
            ("Offline tests passed. " if run.returncode == 0 else
             "Offline tests failed. ") + output[-2800:])


def build_report(checks):
    successes = sum(bool(item["passed"]) for item in checks)
    title = (
        "PASS — engineering checks completed"
        if successes == len(checks)
        else "NOT READY — at least one release check failed"
    )
    lines = [
        "# MemoryLab V1.0 — Local release readiness",
        "",
        "**" + title + "**",
        "",
        "Generated: " + datetime.now(timezone.utc).isoformat(),
        "",
        "| Engineering check | Result | Detail |",
        "|---|---|---|",
    ]
    for item in checks:
        lines.append(
            "| " + item["name"] + " | "
            + ("PASS" if item["passed"] else "FAIL") + " | "
            + item["detail"].replace("|", "/").replace("\n", " ")[:700]
            + " |"
        )
    lines += [
        "",
        "## Release gate interpretation",
        "",
        "Even a green engineering result does **not** mean the system is "
        "production-ready or that its LLM memory answers are accurate. "
        "Phase 14 semantic verification classified all 32 curated answers "
        "as supported and detected zero of the 22 reviewer-labelled "
        "unsupported answers. Do not deploy it as an answer gate.",
        "",
        "Complete manual UI checks: creating a fictional first memory, adding "
        "a compatible fact using Smart Memory Review, selectively superseding "
        "a known obsolete fact, rejecting duplicates, viewing history, "
        "semantic retrieval, and an unanswered question. Document the "
        "unverified answer-generation risks.",
        "",
        "Before a public portfolio V1.0 release, confirm example-only screenshots, "
        "a clean README, privacy exclusions, reproducible local setup, and "
        "an explicit experimental/research disclaimer. Independent "
        "blind evaluation remains a separate research milestone.",
        "",
        "No personal database or user memories were read by this check. "
        "Its SQLite exercise was isolated in a temporary directory.",
        "",
    ]
    return "\n".join(lines)


def next_report_path(folder=RESULT_DIR):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    for counter in range(1, 10000):
        path = folder / f"v1_release_readiness_{counter:03d}.md"
        if not path.exists():
            return path
    raise RuntimeError("Too many readiness reports; select a fresh workspace.")


def run_checks(*, with_models=False, skip_tests=False):
    checks = []
    for name, fn in (
        ("Project layout", project_layout),
        ("Privacy exclusions", privacy_exclusions),
        ("Guarded research baseline UI", guarded_baseline_ui),
        ("Temporary SQLite reviewed storage", isolated_review_smoke),
        ("Python and Streamlit environment", runtime_environment),
    ):
        try:
            passed, detail = fn()
        except (OSError, ValueError, sqlite3.Error) as error:
            passed, detail = False, str(error)
        checks.append({"name": name, "passed": bool(passed), "detail": detail})
    if not skip_tests:
        passed, detail = unit_tests()
        checks.append({"name": "Offline test suite", "passed": bool(passed), "detail": detail})
    if with_models:
        passed, detail = local_ollama_model_check()
        checks.append({"name": "Local Ollama model tags", "passed": bool(passed), "detail": detail})
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-models", action="store_true",
                        help="Also query LOCAL Ollama model tags (no inference).")
    parser.add_argument("--skip-tests", action="store_true",
                        help="Skip the offline test suite for quick diagnostics.")
    args = parser.parse_args()
    checks = run_checks(with_models=args.check_models, skip_tests=args.skip_tests)
    report = build_report(checks)
    destination = next_report_path()
    with destination.open("x", encoding="utf-8") as out:
        out.write(report)
    for item in checks:
        print(("PASS" if item["passed"] else "FAIL")
              + "  " + item["name"] + ": " + item["detail"][:260])
    print("Saved:", destination)
    print("All passed:", all(item["passed"] for item in checks))
    print("This is a local engineering readiness check, not model accuracy.")
    return 0 if all(item["passed"] for item in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
