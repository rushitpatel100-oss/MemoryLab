# Experiment 017 — Phase 10 semantic answers: real unsupported claim

**Date:** 16 November 2026. **Status:** Owner-uploaded Phase 10 semantic results analysed; answer-audit code and an opt-in evidence-required answer experiment published. **Phase 11 results not yet observed.**

## Input and provenance

- Owner-provided file: `phase10_semantic_reviewed.json`, SHA-256 `3cdd6901ae7788d6766023c341e697efadb7cfadc75852434d3bea36c90cb275`.
- Dataset fingerprint in the supplied file: `75191a19db362a9f8f40575d8bf3d66ec97bb67c061662a301525d4ff05ab4b6`.
- Mode: **scripted `reviewed` selective storage** through temporary SQLite, local `all-minilm` embeddings with similarity threshold **0.25** and top **3**, then `qwen2.5:1.5b` answer generation.
- These are **project-authored fictional development** questions with supplied reference memory actions, not blind independent human annotations or autonomous relation-classifier accuracy. The uploaded source file remains unmodified and was not committed.

## Recorded quantitative findings

| Measure | Result | What it means |
|---|---:|---|
| Completed scenarios | **14/14** | One saved reviewed-policy run per authored scenario |
| Generated answers | **28/28** | Two follow-up questions per scenario |
| Authored active memory state matches | **14/14** | The *scripted storage actions* produced the expected active sets |
| Required supporting facts still active | **27/27** | All 27 authored-answerable questions retained the needed facts |
| Required supporting facts retrieved | **27/27** | All 27 were in the selected top-three evidence |
| Keyword/abstention text proxy | **25/28** | The original strict lexical checker rejected three answers |
| Semantic inspection of 28 responses | **27 appear supported**, **1 clearly unsupported** | Assistant review on the same authored cases; **not independently validated accuracy** |

### Two lexical false negatives

**P04 Q1 — Sky Club telescope.** Memory: `Sky Club has a blue telescope.` Qwen: `Based on the memory records provided, the telescope belonging to Sky Club is the blue one.` The checker demanded the exact phrase `blue telescope`; this is a sensible paraphrase and should not be counted as a known factual error.

**P06 Q1 — Robotics club day.** Memory: `The robotics club gathers every Thursday.` Qwen: `The robotics club gathers on Thursdays.` The checker required `Thursday` as an isolated literal token; pluralization should not imply a factual failure.

### One genuine unsupported generation

**P07 Q2 — Gardening committee's new weekday.** Active memories: `The gardening committee meets on Friday evenings.` and `One of my committees changed its meeting day.` The user question asks: `What is the new weekday for the gardening committee?` Qwen replied: `The new weekday for the gardening committee is Monday.`

Neither source identifies which committee changed, nor gives a new weekday. The generated Monday is **unsupported**, even though both memories were stored and retrieved correctly. This is an **answer-generation grounding/abstention failure**, not a demonstrated storage or retrieval failure.

## Actions taken

1. Added **`scripts/audit_phase10_answers.py`**, an offline file-level audit that distinguishes (i) lexical matches that remain unverified, (ii) wording mismatches for semantic inspection, (iii) specific answers when the authored scenario expects abstention, (iv) missing stored evidence, and (v) retrieval misses. It creates separate `phase10_semantic_reviewed_audit.md` and `.json`, fingerprints the original source, and never calls Ollama or mutates it.
2. Added **`answer_evidence.py`**, an **opt-in experimental extractive answer function**. The model must return a source memory ID, exact supporting quote and answer text span. A malformed or unsupported response becomes an explicit abstention. This is a syntactic quote check, **not** a semantic entailment proof; a real quote could still be irrelevant or an old value could be mistaken for a new value.
3. Added **`scripts/evaluate_answer_evidence.py`** to run the experimental answer mode on the same synthetic Phase 10 scenarios and compare with the saved unmodified baseline; all new outputs use `phase11_*` filenames. The original answer generator and live `app.py` remain unchanged.
4. Added **27 offline test methods** across these new modules. Existing 201 tests plus 9 answer-audit tests, 12 evidence-answer tests and 6 comparison tests imply **228 expected tests** after this change. Tests and real Phase 11 Ollama outputs have not been run on the user's Windows computer in this session.

## How to reproduce

```bat
python -m unittest discover -s tests -v
python -m scripts.audit_phase10_answers
python -m scripts.evaluate_answer_evidence --limit 3
python -m scripts.evaluate_answer_evidence
```

With the existing local Phase 10 JSON present, the audit writes `results/raw/phase10_semantic_reviewed_audit.md`. Phase 11 writes `results/raw/phase11_extractive_reviewed.json` and `.md`; after all cases complete, it also writes `results/raw/phase11_evidence_comparison.md`. Run each command from the MemoryLab project directory after GitHub Desktop pull. Both experiment stages preserve original files and save results per scenario.

## Interpretation and next research milestone

This diagnosis isolates one fabricated answer despite 27/27 supporting facts retrieved for answerable questions. The reviewed storage policy was given fixture-authored actions and is **not** a learned decision policy. A better keyword score or more abstentions in Phase 11 alone would not prove semantic truth or generalized reliability; excessive abstention could make MemoryLab less helpful.

Because the 14 scenarios have now informed answer-guard design, **future claims require new and independently reviewed fictional answerability scenarios**. Test both false specific answers and missed legitimate answers, evaluate actual citations/quote relevance, and obtain explicitly attributed human verification for contested outputs. Preserve historical baselines, prevent any unreviewed memory suppression, and do not claim broad hallucination elimination.
