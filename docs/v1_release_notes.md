# MemoryLab V1.0 — Release candidate notes

**Release position:** Portfolio release candidate, **not public or tagged** as of 16 November 2026. The repository is still private. No release files or packaged executables are implied.

## Implemented scope

- Local SQLite records with visible active/superseded history.
- Active-memory semantic retrieval via local `all-minilm`.
- Experimental Qwen local answers and visible retrieved memory evidence.
- AI-assisted but **human-approved** selective memory revisions, with atomic transaction checks.
- Safe disposable Streamlit demo mode, including UI and transactional prevention of broad-topic baseline overwrites.
- Offline unit tests, documented synthetic experiments, and local readiness/manual walkthroughs.

## Observed candidate acceptance

- **295 offline unit tests:** owner reported pass.
- **Memory save and history safeguards:** owner reported correct on final repeated demo.
- **Supported-answer example:** owner reported correct.
- **Unsupported-answer example:** owner reported abstention.
- An **earlier manual UI06 walkthrough failed**, showing only a front-desk record active. The exact trigger was not independently determined. An additional two-layer demo-only safeguard was committed, and the owner later reported the save/history check correct.

This is **user-reported local test evidence**, not a remote independent reproduction. No new clean-install audit or Git-history secret scan has been completed here.

## Known scientific limitations

- The Qwen model may invent unsupported details despite a system instruction to use saved evidence. A previously exposed fictional case produced an invented weekday.
- Strict extractive answer mode excessively abstained and is **not shipped as a live safety gate**.
- Lexical token novelty cannot detect wrong-but-familiar values (wrong person, stale name, negation).
- The experimental semantic verifier classified all 32 project-authored candidate answers as supported, missing 22 reviewer-labelled unsupported answers. It is **not shipped as a live decision gate**.
- These project-authored datasets are not independently sourced or representative. We make **no 100% accuracy, production safety, trained utility policy or independent validation claim**.

## Release candidate go/no-go

**Functional gate:** passed according to owner-reported 295 tests and final manual observations.

**Still required for making the repository public or tagging v1.0:** verify setup on a fresh environment; manually inspect tracked files and Git history for credentials/private data; decide whether to add an explicit license; check public screenshots/recording; optionally record the 3–5 minute demo.

Follow [the publication checklist](publication_checklist.md) and [acceptance status](v1_acceptance_status.md). Do not silently treat a private release candidate as a public finished version.
