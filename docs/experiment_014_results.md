# Experiment 014 — Why V3 abstained in every case

**Status:** Diagnosis from the owner's `phase9_failure_diagnostics.md` file, 16 November 2026. V4 improvement is implemented in source, **not yet observed in a local Ollama run**. Historical outputs and human review decisions are preserved.

## Reported evidence (not an inference)

| Reported diagnostic | Result |
|---|---:|
| Previously exposed fictional cases | **24** |
| V3 predicted `uncertain` | **24/24** |
| Missing or invalid old supporting quotes | **0/24** |
| Missing or invalid new supporting quotes | **0/24** |
| `same_entity=unknown` | **24/24** |
| `same_attribute=unknown` | **24/24** |
| `same_assertion=unknown` | **24/24** |
| `old_fact_known_obsolete=unknown` | **24/24** |
| `new_value_known=unknown` | **24/24** |
| `Evidence is insufficient for a firm relation.` warning | **24/24** |
| Any other diagnostic warnings | **0** |

**Finding:** Valid old/new evidence snippets were present for every case, but all five evidence axes were `unknown` in all 24 cases (**120 unknown axis judgments**). This is *not* primarily a failure to quote the input or provide a structured field. V3's conservative rule then chose `uncertain` in all cases. The report alone does not prove why the model chose unknown for each axis; the original raw Ollama messages were not retained in the saved V3 JSON.

## Engineering interpretation

V3 gave the small local model five questions each allowing `unknown`, repeatedly reinforced caution, and then demanded enough positive axes for confident decisions. The run is **consistent with** a model taking the generic escape option instead of comparing semantic evidence. Other possible causes (model size, output formatting, context, prompt complexity) remain unproven. A model issuing valid quotes does not establish that its semantic judgments are reliable.

## Experimental V4 response (new version, not an edit to V3)

- `scripts/auto_review_v4.py` creates only `results/raw/holdout_v2_ai_review_v4.json`, preserving the earlier V3 and Phase 8 files and signoffs.
- Two inherently ambiguous axes (`same_entity`, `same_attribute`) still allow `yes`, `no`, or `unknown`. Three more concrete axes (`same_assertion`, `old_fact_known_obsolete`, `new_value_known`) require `yes` or `no`. Here, `old_fact_known_obsolete=no` means **not established by the statements**, not proof that the old fact is permanently true.
- Few-shot examples are **generic and different from H01–H24**, covering repetition, a clear update, compatible attributes, and ambiguous identity. V4 must still ground its response in exact text excerpts.
- A deterministic rule maps the evidence to `duplicate`, `replaces`, `coexists`, or `uncertain`. Missing/malformed evidence, invalid quotes, contradictory assertions, role mismatches and indefinite referents cannot justify a confident replacement.
- Any proposed `replaces` remains `review_needed`: it is **not** a command to suppress or delete a saved memory. The model makes no SQLite edits.
- V4 saves raw local model text (bounded per case) in a **Git-ignored, local-only** file, so any future all-unknown or malformed-output failure can be traced to actual model responses rather than guessed from normalized values.
- `scripts/compare_v3_v4.py` produces a separate side-by-side behavior report including per-case labels, aggregate unknown axes and whether raw answers were captured. It never loads human labels and never reports accuracy.

## How to verify

```bat
python -m unittest discover -s tests -v
python -m scripts.auto_review_v4 --limit 4
python -m scripts.auto_review_v4
python -m scripts.compare_v3_v4
```

Expected **161** offline tests after adding 11 V4 policy tests and 5 comparator tests. Local execution and real model behaviour are **not yet confirmed**. The V4 command resumes cases and does not re-run prior saved ones.

Upload `results/raw/phase9_v4_diagnostic.md` to compare behavior, or `results/raw/holdout_v2_ai_review_v4.json` if investigating raw model evidence. Avoid uploading any personal memory database.

## Research limitations and next step

Even if V4 produces a mixture of relationship labels, that is only **improved output coverage**, not demonstrated correctness. The 24 old examples are no longer a legitimate independent holdout because they've been used throughout the design. The next meaningful performance step is new fictional profiles, independently collected blind human labels and tests of actual erroneous forgetting / downstream answer quality. Keep the current AI-first human verification workflow separately described as human-supervised AI rather than independent human annotation.

## Subsequent V4 observations — Experiment 015

The user uploaded V3/V4 comparison output: V4 predicted 7 `duplicate`, 17 `uncertain`, 0 `replaces` and 0 `coexists`. This demonstrates improved coverage of definite labels, but **H18 and H20 are unflagged false duplicates** with possible false-skip consequences. A separate non-destructive duplicate audit was added; it is not legitimate to claim greater V4 accuracy from previously exposed scenarios. See [Experiment 015](experiment_015_results.md).
