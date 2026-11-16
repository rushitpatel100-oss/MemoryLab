# MemoryLab V1.0 — Functional acceptance status

**Status: final manual checks reported PASS by the owner; release/publication audit pending.**

## Chronological record

1. An earlier automated readiness report showed **276 unit tests passing and seven engineering checks passing** on the older release-candidate revision.
2. In an earlier isolated demo walkthrough, UI01–UI05 were reported passing, but UI06 history **failed**: the front-desk test fact was apparently the only active one. The exact action that triggered this state was not proven.
3. The code was updated to prevent broad-topic baseline overwrites on existing topics **during isolated demo sessions**, with both a disabled UI action and an atomic SQLite-level rejection. Six additional tests were added.
4. On the subsequent complete local acceptance run, the owner supplied:
    - **295-test readiness suite:** passed
    - **Memory history and save safeguards:** correct
    - **Supported question:** correct
    - **Unsupported question:** abstained
5. We therefore record **functional candidate acceptance as owner-reported PASS**, with the prior failure and corrective work retained for transparency.

## What this result establishes

A full local unit-test run and the user's manual demo checks passed on their Windows environment. It is reasonable to proceed with **portfolio documentation and release packaging**.

## What this result does not establish

- No separate upload of the latest 295-test readiness report was provided here; the 295-test outcome is a **direct owner report**.
- A single supported and unsupported question is **not** an independent factual-accuracy estimate, reliability stress test or guarantee that Qwen always abstains.
- A subsequent clean clone and Python virtual environment on the owner's Windows PC produced **six reported PASS engineering checks**: project layout, privacy exclusions, baseline guard, temporary SQLite save/rollback, Python 3.14.5/Streamlit, and offline unit tests. The final optional local Ollama-model-tag PASS line was **not included** in the pasted output. A programmatic pattern scan of available diffs for 104 commits on `main` found no known credential-format flags but does not constitute a complete content/privacy audit.
- This file does not assert that the GitHub repo is public, licensed or tagged `v1.0`.

## Next publication checks

Finish the remaining [privacy/history, licence, and clean-demo checks](publication_checklist.md), then optionally [record the portfolio demonstration](demo_storyboard.md). No additional experimental model phases are required for the local V1.0 research-demonstrator scope.
