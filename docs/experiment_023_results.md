# Experiment 023 — Manual UI acceptance revealed an unexpected bulk overwrite

**Date:** 16 November 2026. **Status:** manual UI acceptance FAILED at UI06. Root trigger unconfirmed; V1.0 release BLOCKED pending repeat and acceptance.

## What the owner actually observed

The owner reported these steps passed in the isolated demo walkthrough:

- UI01: saved a fictional Maple Room memory and found it via search.
- UI02: added a fictional digital-projector fact; both were active.
- UI03: superseded the Maple Room location with a Cedar Room update, retaining the projector fact.
- UI04: exact duplicate was blocked.
- UI05: the research-baseline overwrite warning appeared and its button was disabled without acknowledgement.
- **UI06: FAILED.** The user reported: **“no all are suspended except front desk”**. Rather than A (Maple Room) inactive, B (projector) active and C (Cedar Room update) active, apparently all original facts were inactive and the front-desk fact active.

**This is an observed outcome, not a verified root cause.** The current code's broad-topic `save_memory()` updates every record with the same topic to inactive and inserts the proposed fact, which could produce exactly this state **if the Section 1 front-desk baseline save was actually invoked**. However the user earlier reported that its button was disabled. We have not established whether the user clicked again later, an earlier browser session was used, or any unexpected UI event occurred. Do not blame the user, claim a backend bug is proven, or call UI05/UI06 fully validated.

The user had launched isolated MemoryLab demo sessions but also encountered ports 8501 and 8503 occupied. **Before any retry, visually confirm the ISOLATED DEMO MODE banner and that the browser is showing the intended running session.** The launcher environment points to temporary SQLite; the user's exact open browser session has not been independently verified.

## Containment and fix committed

`app.py` now has **two independent checks when `MEMORYLAB_DEMO_MODE=1`**:

1. **UI:** If an existing topic has active facts, the Section 1 baseline bulk-overwrite save button stays disabled **even if** the acknowledgement checkbox is ticked. It explicitly says to use Smart Memory Review.
2. **Transactional backend:** `save_memory()` starts an IMMEDIATE SQLite write transaction, rechecks for an active same-topic record, and returns without changing anything if one exists. It still allows a first saved fact in a new topic. The older bulk-replacement baseline behaviour remains available outside demo mode for explicit research use.

The safeguards are independent of a Streamlit rerun and preserve the human-controlled selective save path. The local release-readiness check now looks for the added demo safeguards. Six additional tests in `tests/test_demo_baseline_protection.py` exercise the actual `save_memory()` function in an isolated SQLite test database, including normalization and first-memory behaviour.

**No live personal database was accessed or edited by the GitHub changes.** The new tests have not been executed on the user's Windows computer.

## Test count and next decision

- Last verified local test run: **276/276 passed** on the earlier code.
- Isolated-demo/manual-report work added **13** tests; UI06 protective fix added **6** more: **295 expected** when run next; execution and results pending.
- **Next action:** stop the currently running demo with Ctrl+C, confirm its temporary data is discarded, pull the updated GitHub changes, and rerun `python -m scripts.v1_release_readiness --check-models`.
- Restart a fresh isolated demo with `python -m scripts.launch_v1_demo` (or the previously working `--port N` if necessary). Confirm **ISOLATED DEMO MODE**. Retest UI01–UI06 before doing UI07/08. For UI05, the demo should refuse bulk overwrite even if a checkbox is selected; do not try to bypass the guard.
- If the browser is not showing the banner, **stop and report that immediately**; don't modify or delete any real `memorylab.db`. The history may need inspection and selective recovery.

Do not declare V1.0 release-ready until a fresh manual acceptance report demonstrates the expected history state and other release gates pass.
