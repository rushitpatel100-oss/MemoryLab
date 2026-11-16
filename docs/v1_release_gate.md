# MemoryLab V1.0 — Portfolio release gate

**Status: functional release-candidate acceptance reported PASS; publication gate still open.** The earlier UI06 failure is documented. After the additional demo-only overwrite safeguard, the owner reported 295 unit tests passed, correct memory history/saving, a supported answer correct and an unsupported question abstained. This remains user-reported functional evidence, not independent model-accuracy validation. Phase 14 demonstrated that automated semantic verification could accept all 32 curated answers, including 22 reviewer-labelled unsupported ones. We therefore **do not ship any of the experimental answer checkers as an autonomous safety gate**.

## What V1.0 can truthfully claim

- Local-first Python/Streamlit application using SQLite memory history, `all-minilm` semantic retrieval and local `qwen2.5:1.5b` answer generation.
- Manual Smart Memory Review where the user chooses `Keep both` or `Supersede old memory`; atomic storage checks reject duplicate and stale review writes.
- Visible retrieved evidence and clear warnings about unsafe duplicate or replacement suggestions.
- Reproducible documented experiments with honest failure cases: excessive automatic supersession, all-uncertain classification, false duplicate skips, fabricated weekday, over-abstention and all-supported semantic verification.

**Cannot claim yet:** a learned utility-based memory policy, independently verified factual accuracy, safe automatic memory suppression, robust semantic entailment, production-grade security/reliability, or a peer-reviewed scientific result.

## Step 1 — Pull and check the local environment

In GitHub Desktop, select **Fetch origin → Pull origin**. In the terminal inside the MemoryLab folder, activate the project's virtual environment if required. Then run:

```bat
python -m scripts.v1_release_readiness --check-models
```

This one command runs the **offline unit test suite**, checks key source and privacy files, exercises selective SQLite saving inside a **temporary database**, verifies the guarded research-baseline UI is present, checks installed Streamlit, and checks only your **local** Ollama tags for `qwen2.5:1.5b` and `all-minilm`.

The uploaded earlier report verified 276 unit tests and seven engineering checks; the owner subsequently **reported all 295 tests passed** on the safeguard revision. A fresh-environment install still needs validation before publication.

Each run writes its own Git-ignored file, e.g. `results/raw/v1_release_readiness_001.md`, then `_002.md`, without overwriting prior runs. **A PASS only means these engineering checks passed. It does not mean the LLM is accurate or the entire app is ready for publication.**

Optional quick diagnostic without unit tests or model calls:

```bat
python -m scripts.v1_release_readiness --skip-tests
```

## Step 2 — Isolated manual product smoke test

Use the new disposable app launcher rather than opening your normal memory database:

```bat
python -m scripts.launch_v1_demo
```

Follow [eight fictional manual checks](v1_manual_acceptance.md): initial save, coexistence, selective supersession, duplicate blocking, baseline warning, history, semantic retrieval/answer, and an unsupported-answer observation. The final observation is NOT a model-accuracy certification.

Stop the demo with Ctrl+C and run:

```bat
python -m scripts.record_v1_manual_qa
```

Upload its unique Git-ignored `results/raw/v1_manual_acceptance_001.md` report; do not guess unperformed checks. The demo database is temporary and is removed when the launcher exits.
## Step 3 — Portfolio and privacy checks

- Use fictional examples in screenshots, test databases and demo recordings. Review every file to be published for personal memory contents, credentials and contact information.
- Confirm the `.gitignore` exclusions are effective: `results/raw/`, `*.db`, secrets and local `.env` files. Ignore rules do **not** retroactively remove files from Git history.
- Put a short 3–5 minute demo, an architecture diagram, setup instructions and a transparent table of positive and negative experimental results in the README or a linked V1.0 overview.
- Mark the memory conflict suggestions and answer generation **experimental**, with human approval and evidence inspection required. Avoid presenting the 32 curated cases as independent accuracy.
- Run the project from a clean environment and confirm first-time setup. Check any Windows-specific dependencies before distributing.

## Go / no-go

**Go (local functional V1.0 candidate):** owner-reported 295-test pass and manual save/review/history and answer checks; this condition is met by the latest owner report. **Go (public repository/tag):** also requires clean setup, manual source/history privacy review, acceptable screenshots and accurate claims; these are still pending.

**No-go:** failed data-integrity unit tests, UI can silently replace active memories, personal data enters Git, missing setup instructions, or claims that experimental verifiers can ensure truthful answers.

**Separate future research goal:** independently prepared fictional examples with two blinded annotators and disagreement resolution, repeated end-to-end storage/retrieval/answer measurements, and transparent error analysis.

Do **not** create a v1.0 Git tag until these checks are actually completed.


## Functional acceptance and portfolio package

The final owner-reported functional pass is documented in [V1 acceptance status](v1_acceptance_status.md). The concise [portfolio README](../README.md), [architecture diagram](architecture_v1.md), [Windows quickstart](windows_quickstart.md), [demo storyboard](demo_storyboard.md), [release notes](v1_release_notes.md) and [publication checklist](publication_checklist.md) are now the release-facing documents. Historical failures remain preserved under the research journal.


## Clean installation and limited historic screen (owner update)

After the initial 295-test functional acceptance, the owner performed a fresh copy/fresh virtual-environment check and pasted **six PASS results**: project layout, privacy exclusion patterns, guarded baseline UI, temporary reviewed storage, Python 3.14.5 and Streamlit, and offline test suite. No optional model-tag result was included in that paste. In parallel, a screen of available changed-text diffs on all **104 commits on the sole `main` branch** produced no matches for several common token/private-key/credential formats, user-profile paths, or sensitive changed filenames. **This cannot certify absence of all personal or proprietary content.** Human privacy inspection and licence/publication consent are still required; keep the repo private and untagged.
