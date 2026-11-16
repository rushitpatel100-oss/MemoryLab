# Experiment 019 — Phase 12 novelty screen and Phase 13 labelled challenge

**Date:** 16 November 2026. **Input:** owner-uploaded `phase12_answer_novelty_probe.md`. **Status:** 28 prior development answers screened; new answer-support challenge and blinded-review tools published, but no Phase 13 labels or evaluation results yet.

## Observed Phase 12 result

| Saved baseline answer status | Count |
|---|---:|
| `no_obvious_lexical_novelty` | **27/28** |
| `unsupported_weekday` | **1/28** |

**P07/Q2:** The question asks for the *new* gardening-committee meeting weekday, but the source only says that the committee meets Friday evenings and that an unspecified committee changed its day. Baseline Qwen invented **Monday**. The probe flagged the unsupported weekday `monday` because it does not occur in retrieved active memory facts.

The probe did **not** flag the valid paraphrase `the blue one` (P04/Q1) or plural `Thursdays` (P06/Q1). Prior assistant semantic inspection found these supported. Nevertheless, this 28-answer result is **not an independent accuracy estimate**: the probe was built *after* seeing the baseline answers and intentionally used their failure modes.

## Why a new challenge matters

A lexical novelty rule can miss false answers made entirely of words present in the source. Examples include answering with an outdated weekday from a `moved from A to B` fact, confusing home and away jersey colours, conflating two people, and dropping a critical negation. It may also flag harmless synonyms absent from the memory text. These failure modes must be evaluated separately before any use as a production answer gate.

## Phase 13 implementation — curated, not independent source data

`benchmarks/answer_claims_v1.json` contains **32 newly authored fictional source/answer pairs**, deliberately spanning literal support, paraphrase, fabricated numbers and weekdays, stale values, wrong entities and attributes, negated claims and ambiguous referents. The dataset includes **no truth labels and no novelty-probe outputs**.

`app_answer_challenge.py` is a simple local Streamlit review interface. It shows the candidate answer and its fictional retrieved evidence, but keeps detector results hidden. A reviewer assigns `supported`, `unsupported`, or `uncertain` (with a reason required for `uncertain`). Individual edits are retained in an audit log. The review can be locked **only after all 32 cases are individually labelled**. This creates local `results/raw/phase13_answer_signoff.json`, which is Git-ignored.

Only after the labels are locked, `scripts.evaluate_answer_challenge` compares the saved judgements with the unchanged `check_answer()` lexical novelty probe, reporting true/false positives, misses, and per-case warnings. Reviewer `uncertain` entries are excluded from binary precision/recall and counted separately. Outputs are new local `phase13_probe_evaluation.json` and `.md` files. Neither script contacts Ollama or opens the user's SQLite memories, and original Phase 10–12 files remain intact.

**Provenance caveat:** The candidate answers and examples were authored inside the project, and the user provides a **single** review of their factual support. Blinding is *to the probe output*, **not** to the authored answers or the fact that they were curated to challenge specific heuristics. Even after manual signoff this is **not independently sourced ground truth, model accuracy or representative precision/recall**. It is a stress test of a cheap detector, not a measurement of Qwen's answer accuracy.

## Local commands (after GitHub Desktop pull)

```bat
python -m unittest discover -s tests -v
python -m streamlit run app_answer_challenge.py
```

Review every case, then check the attestation box and click **Freeze all 32 reviews**. Close the review dashboard and run:

```bat
python -m scripts.evaluate_answer_challenge
```

Expected offline test count: **253** (239 before this stage, plus 14 new tests). The complete Windows test suite has not been run here. The scoring command fails without the frozen signoff and will not overwrite previous reports.

## Interpretation and subsequent research

Use the result to characterize **false negatives on stale facts, entity swaps, negation and question leakage**, and false positives on legitimate paraphrases. Do not deploy the novelty probe as an autonomous guard solely because it catches a known invented day. A subsequent release-quality evaluation requires independently collected fictional tasks and, ideally, two reviewers with disagreements resolved before examining model outputs.
