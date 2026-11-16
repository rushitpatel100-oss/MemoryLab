# MemoryLab Phase 8 — Blind evaluation protocol

## Purpose

**Shortcut if you don't want to label all 24 cases manually:** use `python -m scripts.auto_review_holdout_v2`. It generates local AI *draft* labels in a separate file and does not overwrite reviewer A/B work. This is useful automated triage, **not independent human validation**. See [automatic review instructions](auto_review.md). The strict human-consensus evaluator below remains unchanged.

Experiment 011 retained conflicting human interpretations of some anonymous subjects and vague updates. Phase 8 is **not a new classifier**: we are first improving the annotation process to avoid taking a label or storage action as established fact when the evidence is incomplete.

### The study is frozen before predictions

- `docs/label_rubric_v2.md`: evidence-first relation and storage rubric.
- `benchmarks/holdout_v2_cases.json`: 24 fresh fictional pairs, **with no answer key or model output**.
- `scripts/review_holdout_v2.py`: two separate, resumable local reviewer files (A and B). The reviewer scripts never run Qwen or open SQLite.
- `scripts/evaluate_holdout_v2.py`: cannot run until both complete label files are locked; compares existing classifier and safety gate on one common Qwen result per pair.

The new 24 examples were authored by the project in light of earlier errors. They are **unseen model-evaluation examples**, but not an externally constructed or statistically representative gold standard. The rubric was also authored within the project. No claim of independent held-out accuracy is justified.

## How to run on Windows

1. GitHub Desktop → Fetch origin → Pull origin. Use the MemoryLab folder in a Python terminal with the project's environment activated.
2. Run the offline unit suite:

   `python -m unittest discover -s tests -v`

   Expect **105 tests** (89 previously, 16 new). These new tests are published but have not been run on the user's Windows machine.
3. **Read [rubric v2](label_rubric_v2.md) first.** It defines the difference between `duplicate`, `replaces`, `coexists`, `uncertain` and their distinct storage actions.
4. Reviewer A (no access to model output or B's answers):

   `python -m scripts.review_holdout_v2 --rater A --limit 4`

   The first prompt per case is R=review / S=skip / Q=quit. Then choose the **four evidence dimensions first** using Y/N/U, choose a relation D/R/C/U, give a short reason, and finally choose storage K/S/R/D. Contradictory answers are **not saved** and must be re-entered; unknown evidence is a valid response.
5. Resume, check, and lock reviewer A when all 24 responses are complete:

   `python -m scripts.review_holdout_v2 --rater A`

   `python -m scripts.review_holdout_v2 --rater A --status`

   `python -m scripts.review_holdout_v2 --rater A --lock`

   If an unfinished review needs correction, use `--rater A --edit H01` on an already answered case. The prior response is preserved locally in a revision history.
6. **Reviewer B should be a different person**, unaware of A's labels and old Qwen predictions. They repeat steps 4–5 but use `--rater B`. The program cannot prove that a different person completed the second file.
7. Only when **both** A and B have `locked=True`, run:

   `python -m scripts.evaluate_holdout_v2`

   Requires running local Ollama `qwen2.5:1.5b`. It does **not** modify SQLite. It writes `results/raw/holdout_v2_results.json` exactly once; it refuses to overwrite a prior file. Both variants use the same raw Qwen prediction per case. The evaluation cannot be used to choose or revise labels before lock.

## Results to report

- A/B agreement count and all disagreement IDs. Do not include disputed cases in a model agreement rate until separately adjudicated.
- For the consensus subset only: raw and gated label matches, false `replaces` suggestions, correctly detected replacements, missed true updates, and uncertain outputs.
- Number of consensus cases in every denominator; 24 is **not** automatically the correct denominator for model-label agreement.
- Model runtime and the exact dataset/label fingerprints. Model calls are not repeated for the gate.
- Clearly distinguish **human-consensus labels** from independently expert-adjudicated ground truth.

## Safeguards and limitations

Both review files and the final model report are under `results/raw/`, already Git-ignored. The review script never reads the other review file. The evaluator reads both only after they are locked. Code does not authenticate reviewers or prevent the same person completing both reviews; to claim inter-rater agreement, document the actual review setup. For a rigorous future benchmark, recruit distinct trained raters, independently sample a new scenario set, adjudicate disagreements blinded to model outputs, and run downstream memory-retention and answer-quality tests.

The Qwen prompt, deterministic gate and SQLite storage behaviour **remain unchanged**. The original Experiment 010 and 011 files are never read, edited or overwritten by Phase 8 tools.

## Optional AI-first verification track (not blind evaluation)

If full human labelling takes too much time, you may instead run `python -m scripts.auto_review_holdout_v2` followed by `python -m streamlit run app_review.py`. This workflow is suitable for annotation triage and producing a human-approved AI report, but is **not** a substitute for the two blind reviewer files required by `evaluate_holdout_v2`. Viewing AI-generated labels before finishing the review contaminates future claims that those same cases were labelled blind. See [human verification](human_verification.md).
