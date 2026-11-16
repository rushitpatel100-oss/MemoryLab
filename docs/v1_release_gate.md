# MemoryLab V1.0 — Portfolio release gate

**Status: release candidate preparation; not yet a verified/tagged release.** Phase 14 demonstrated that automated semantic verification could accept all 32 curated answers, including 22 reviewer-labelled unsupported ones. We therefore **do not ship any of the experimental answer checkers as an autonomous safety gate**.

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

Expected total: **276 offline unit-test methods** (264 before Experiment 021, plus 4 UI guard tests and 8 readiness tests). The test suite has **not** been executed on your Windows environment during this update. It can reveal failures; do not infer success from the expected count.

Each run writes its own Git-ignored file, e.g. `results/raw/v1_release_readiness_001.md`, then `_002.md`, without overwriting prior runs. **A PASS only means these engineering checks passed. It does not mean the LLM is accurate or the entire app is ready for publication.**

Optional quick diagnostic without unit tests or model calls:

```bat
python -m scripts.v1_release_readiness --skip-tests
```

## Step 2 — Manual product smoke test

Launch:

```bat
python -m streamlit run app.py
```

Using **fictional facts only**, verify the following and record failures:

1. Save a first memory in a new topic. View it in active search and memory history.
2. Use **Smart Memory Review** to add a different attribute to that topic. Select **Keep both** and confirm both remain active.
3. Update a specific old attribute. Explicitly confirm the matching subject, matching attribute and that the old fact is outdated; supersede only that memory. Other active facts must remain.
4. Attempt an exact duplicate and confirm that the atomic store rejects it without changes.
5. Verify the **research baseline** warns that it deactivates every active same-topic memory, and that its save button is disabled until the user acknowledges the risk. Prefer the selective-review path instead.
6. With local Ollama running, ask one question supported by active facts; inspect the retrieved memory evidence. Also ask one deliberately unsupported question and **document whether it answers or abstains**. Do not conceal hallucinations in the demo.

## Step 3 — Portfolio and privacy checks

- Use fictional examples in screenshots, test databases and demo recordings. Review every file to be published for personal memory contents, credentials and contact information.
- Confirm the `.gitignore` exclusions are effective: `results/raw/`, `*.db`, secrets and local `.env` files. Ignore rules do **not** retroactively remove files from Git history.
- Put a short 3–5 minute demo, an architecture diagram, setup instructions and a transparent table of positive and negative experimental results in the README or a linked V1.0 overview.
- Mark the memory conflict suggestions and answer generation **experimental**, with human approval and evidence inspection required. Avoid presenting the 32 curated cases as independent accuracy.
- Run the project from a clean environment and confirm first-time setup. Check any Windows-specific dependencies before distributing.

## Go / no-go

**Go (portfolio V1.0):** offline unit suite and readiness check pass, no regression in manual save/review/history flows, local answer demo works with limitations disclosed, and privacy/reproducibility checks are done.

**No-go:** failed data-integrity unit tests, UI can silently replace active memories, personal data enters Git, missing setup instructions, or claims that experimental verifiers can ensure truthful answers.

**Separate future research goal:** independently prepared fictional examples with two blinded annotators and disagreement resolution, repeated end-to-end storage/retrieval/answer measurements, and transparent error analysis.

Do **not** create a v1.0 Git tag until these checks are actually completed.
