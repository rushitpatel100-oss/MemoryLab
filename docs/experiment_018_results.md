# Experiment 018 — Phase 11 extractive-answer over-abstention

**Date:** 16 November 2026. **Decision:** Do not deploy the extractive evidence mode in the live app. It stopped one unsupported answer but refused most supported questions.

## Provenance

- Owner-uploaded Phase 11 comparison Markdown SHA-256: 868c5200237fa87f968cbdf3b90fc95be8552537f1733ffffc13e659c1f19544
- Owner-uploaded extractive JSON SHA-256: 03c3e3f1e437a5ae07c3590cadd2af6e273e9156693001e3cfd0a3aa190e47de
- Saved original Phase 10 baseline SHA-256: 3cdd6901ae7788d6766023c341e697efadb7cfadc75852434d3bea36c90cb275
- Fourteen project-authored fictional scenarios and 28 questions. Storage decisions are scripted, not autonomously predicted. These data have been examined and are not an independent human-labelled blind benchmark.

## Observed comparison

| Measure | Original Qwen | Extractive-evidence Qwen |
|---|---:|---:|
| Questions | 28 | 28 |
| Keyword/abstention proxy matches | **25** | **5** |
| Exact no-information responses | **0** | **24** |
| Specific responses to the one authored-unanswerable question | **1** | **0** |
| Abstentions on 27 authored-answerable questions | **0** | **23** |
| Specific answers on answerable questions | **27** | **4** |

Extractive mode returned specific replies only for **P05/Q1 (Orchid Hall), P08/Q1 and P08/Q2 (Sunbeam), P11/Q1 (thyme)**. It abstained on supported cases involving a printing press, telescope, film screening and more. It correctly withheld a guessed weekday on P07/Q2 but lost almost all useful answer coverage.

Phase 10 previously demonstrated all 14 authored active-memory states matched and all 27 authored-answerable supports were both stored and retrieved. The extractive JSON retains that evidence selection. The regression is therefore at the answer-generation or evidence-validation layer, not memory storage.

**Unknown exact cause:** The saved extractive JSON has final answer strings, not the underlying Ollama supported/quote/answer_span response or a validator rejection reason. Therefore we cannot determine whether 24 abstentions came from supported=false, malformed output, fabricated quote, a wrong memory ID, or another rejection.

## Engineering response

1. Preserve the original Phase 10 and Phase 11 runs, and keep the live Qwen answer generator unchanged.
2. Add a separate **Phase 12 offline novelty probe** on saved baseline answers to flag unsupported day names, numeric claims, invented memory citations and other novel wording. The probe cannot prove truth or semantic relevance.
3. Preserve raw model replies and rejection reasons in any future verifier experiments to distinguish model uncertainty from validator errors.
4. Evaluate any promising next method on newly authored, frozen and independently reviewed fictional questions, including unanswerable prompts, stale old values and genuine paraphrases.

An improved refusal rate must not be equated with safer or more accurate answering. These project-authored cases are development diagnostics, not independently validated general-model accuracy.