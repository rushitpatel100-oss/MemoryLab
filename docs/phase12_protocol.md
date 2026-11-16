# Phase 12 — Offline novelty-screening diagnostic

**Goal:** Investigate potentially unsupported factual claims in existing baseline answers without repeating Qwen calls. This is NOT an autonomous safety verifier and does not replace the live answer system.

## Windows steps

After GitHub Desktop: **Fetch origin → Pull origin**, run:

    python -m unittest discover -s tests -v
    python -m scripts.probe_answer_novelty

The expected total is **239 offline test methods** (previously 228 plus 11 new probe tests); local execution is not yet verified. The command reads the existing local Phase 10 reviewed semantic JSON and writes new reports at:

- results/raw/phase12_answer_novelty_probe.md
- results/raw/phase12_answer_novelty_probe.json

It never reads the personal SQLite database, invokes Ollama, or overwrites any original result. It refuses to overwrite an existing report.

## What is checked

The probe compares each baseline answer with the **retrieved** active facts, not all stored facts. It detects unsupported weekdays, numbers, claimed memory IDs absent from the retrieved set, and other novel terms. It normalizes simple plurals and number words (for example Thursdays / Thursday and ten / 10). Abstentions remain a separate category.

A result of **no obvious lexical novelty is not verified correctness**. Wrong old values may be present in a valid memory, an answer can associate the wrong subject with a true fact, and a novel synonym may be entirely acceptable. The heuristic is neither a semantic entailment checker nor a production-quality safety gate.

The method has been designed after viewing these same 14 scenarios, so screening rates on them must not be presented as new blind accuracy. Do not deploy it to silently suppress answers. The next defensible milestone is a new independently reviewed set of fictional questions that includes dates, entities, changed values and justified abstention.

See [Experiment 018](experiment_018_results.md).

## Report received — Experiment 019

The local 28-answer probe report returned **one `unsupported_weekday` (invented Monday in P07/Q2)** and **27 `no_obvious_lexical_novelty`**, including two valid wording variations. Its performance on these exposed cases cannot be treated as independent accuracy. The subsequent [Phase 13 challenge](phase13_protocol.md) provides new curated examples without labels or probe outputs, a probe-blind single-reviewer workflow, and an offline evaluator that only runs after label freeze. See [Experiment 019](experiment_019_results.md).
