# MemoryLab Phase 11 — Evidence-required answers (experimental)

## Purpose

Experiment 017 identified a fabricated **Monday** when the selected memories contained no new weekday. The original Phase 10 run otherwise had correct author-defined storage states and the required source facts retrieved. The next engineering target is the **answer-generation grounding and abstention layer**, not another change to the conflict-label classifier.

## Two-step local workflow (Windows)

After **GitHub Desktop → Fetch origin → Pull origin**, in the project terminal:

~~~bat
python -m unittest discover -s tests -v
python -m scripts.audit_phase10_answers
~~~

The expected offline test count is **228**, including 27 new tests in the answer-audit, evidence-answer and comparison modules; actual execution on your Windows system remains unverified.

The audit reads your existing `results/raw/phase10_semantic_reviewed.json` and writes:

- `results/raw/phase10_semantic_reviewed_audit.md` — counts, flags and full answers worth semantic inspection.
- `results/raw/phase10_semantic_reviewed_audit.json` — machine-readable categories and source SHA-256.

It makes **no Ollama calls**, and neither file overwrites earlier results.

To test a different answer-generation path on the SAME fictional data, with your existing local Ollama models running:

~~~bat
python -m scripts.evaluate_answer_evidence --limit 3
python -m scripts.evaluate_answer_evidence
~~~

Both commands are resumable: the second completes the remaining cases without repeating already saved scenarios. Outputs:

- `results/raw/phase11_extractive_reviewed.json` — new experiment's per-question retrieved records, answers, and keyword proxies.
- `results/raw/phase11_extractive_reviewed.md` — summary of the new experimental run.
- `results/raw/phase11_evidence_comparison.md` — original Qwen answers versus evidence-required answers; created when both complete files are present, never overwrites.

## How the extractive guard works

The new `answer_evidence.py` sends the same question and selected active memories to a structured local Qwen request, asking for `supported`, a memory ID, a **verbatim quote**, and an **answer span contained inside that quote**. When the response is unsupported, malformed, or cites text that is not in the selected memory, it returns the existing MemoryLab no-memory-answer string rather than a specific guess.

**This is not a full factual entailment checker.** Real but unrelated evidence might still be cited; a model may extract an *old* day as an answer to a question about the *new* day. An extractive constraint may also reject valid synonyms, multi-fact summaries or calculations. Preserve coverage and abstention counts separately. Do not switch the live app to this mode until a new dataset verifies the tradeoff.

## Evaluation provenance

The existing dataset was designed and inspected within this project. It is useful for regression tests but no longer an unseen independent benchmark. `reviewed` storage uses authored decisions rather than any classifier output. Text-proxy matches are not human-adjudicated correctness; semantic inspection of answers can be more informative but is still part of development, not blinded external verification.

Next, collect **new, fictional, separately reviewed** questions that require both grounded answers and appropriate abstentions. Compare original and extractive modes with clear failure categories: invented specifics, unsupported citations, missing evidence, and over-abstention. Keep the original Phase 10 file and all prior human signoffs immutable.

See [Experiment 017 findings](experiment_017_results.md).
