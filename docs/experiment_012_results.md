# Experiment 012 — AI-first memory review with human corrections

**Status:** Owner-uploaded run analyzed **16 November 2026**; original three files remain local and are not committed. This experiment measures *agreement between AI drafts and subsequent signoffs* and identifies failure modes; **it is not a blind human-labelled model-accuracy benchmark**.

## Provenance and integrity

- Frozen 24-case fictional dataset: `benchmarks/holdout_v2_cases.json`, dataset SHA-256 `614d99cdd7e6e4c90380b6a3386919af9705b30e795f15d12bad309337210035`.
- AI draft file (private): `results/raw/holdout_v2_ai_review.json`, judged by local Ollama `qwen2.5:1.5b`. SHA-256 of the uploaded raw JSON: `38fa61accde6dccc3e8d988f4e142fbd504094a6618bcb50529c0d9ee631b983`.
- Human signoff file (private): `results/raw/holdout_v2_human_signoff.json`, `method=AI-first, human-reviewed`, `independently_human_labelled=false`. Its `ai_source_sha256` matches the uploaded AI JSON byte-for-byte.
- Exported Markdown file: `MemoryLab_AI_assisted_human_review.md`. Its summary table matches **all 24** machine and final labels plus each saved approval type. There are **24 unique cases**, **24 signoff decisions**, and **24 matching audit events**; this export reports six individual approvals and eighteen human edits. No bulk attestations were recorded.
- The AI draft dates and recorded human signoff times are within **16 November 2026 UTC**. The uploaded files do not prove reviewer independence or externally verified correctness. The assistant inspected and cross-checked the three uploads; it did **not** run the user's Ollama model or Windows environment.

## Quantitative diagnostic results

| Descriptive measure | Value | Interpretation |
|---|---:|---|
| Fictional memory pairs | **24** | All are accounted for in every upload |
| Original AI relation = `replaces` | **24/24** | Single-label collapse in this run; zero AI `duplicate`, `coexists`, or `uncertain` |
| Original AI proposed storage action = `supersede_old` | **24/24** | Unsafe as an automatic storage policy |
| Model proposals marked `needs_review` | **24/24** | Review gate did **not** treat any proposal as ready to execute |
| Safe action = `review_needed` | **24/24** | No storage changes were executed by the reviewer |
| AI cases with missing/invalid evidence-value warnings | **10/24** | Model output/schema reliability issue; absent values were normalised to `unknown` and flagged |
| Individually accepted AI drafts | **6/24** | Explicit individual approval, not independent human annotation |
| Saved human corrections | **18/24** | 75%; an edit does not necessarily change the relation label |
| Bulk attestations | **0/24** | All saved decisions were individual actions |
| Final relation different from AI proposal | **11/24 (45.8%)** | Reviewer disagreed with `replaces` on the relationship label |
| Corrected entries where relation stayed `replaces` | **7/24** | Other evidence/explanations/actions were revised |
| Final relation = `replaces` | **13/24** | Subject to semantic audit; not a verified gold truth |
| Final relation = `coexists` | **6/24** | Human-reviewed but not necessarily infallible |
| Final relation = `duplicate` | **5/24** | Human-reviewed but not necessarily infallible |
| Final relation = `uncertain` | **0/24** | Concerning because some fact pairs lack enough identity/update evidence |

**Eleven changed relation labels:** H01, H05, H07, H09, H11, H12, H14, H17, H19, H23, H24. **Seven other edited entries kept the same relation label:** H06, H08, H13, H15, H18, H20, H22.

These numbers are **not** classifier accuracy, human adjudication accuracy, precision, recall or benchmark improvement. The final answers were reviewed *after* seeing the model's suggestions, so they are susceptible to anchoring. The 13/24 AI–signoff label agreement merely describes how many model outputs were left with their original four-way label.

## Failure analysis

### 1. The automatic AI reviewer strongly overpredicted replacements

Qwen proposed `replaces` and `supersede_old` for **every** case, including independent attributes (bicycle bell vs chain cleaning; desk lamp vs cactus), duplicates (the same dog swimming, the same bus commute, the same hobby), and explicitly separate attributes (home jersey vs away jersey). Generating fluent natural-language explanations did not fix the relation decision.

### 2. The protection against automatic supersession worked in this run

The machine review's `safe_storage_action` was **`review_needed` for all 24 pairs**, despite proposing supersession everywhere. As far as these review scripts are concerned, none of the suggestions mutated SQLite. This does **not** prove that all MemoryLab code paths are universally safe.

### 3. Some signed-off decisions still need semantic rechecking

These are independent **audit flags, not automatic corrections**. The human file and its audit history remain frozen as supplied.

| Priority | Case | Why review again | Defensible alternative to consider |
|---|---|---|---|
| High | **H02** | `My dog Saffron enjoys swimming` and `Saffron, my dog, likes to swim` are paraphrases, but the approved label is `replaces` | `duplicate`; no fact became obsolete |
| High | **H06** | `office printer` versus `basement printer` may refer to different machines; identity is not established | `uncertain` until identity is known; never automatically supersede the office-printer fact |
| High | **H20** | The old statement concerns the **home** jersey; the new change concerns the **away** jersey | `coexists` (different attributes); keep home-jersey fact |
| Medium | **H09** | `one of my clubs` does not identify the nature club; approved explanation recognises that but `same_entity=yes` | `same_entity=unknown`; relation `uncertain` rather than certain coexistence |
| Medium | **H13** | The thermostat was adjusted but no final temperature is stated; `new_value_known=yes` is unsupported | `new_value_known=no`; relation requires further context |
| Medium | **H04**, **H16**, **H21** | Generic `my sister`, `my uncle`, `my friend` may or may not refer to the named person in the older fact | `same_entity=unknown` and consider `uncertain` if identity matters |
| Medium | **H11**, **H17**, **H24** | Coexisting facts have `same_attribute=yes` even though they concern windows/chair, rental/bookcase, bench/parasol | Keep `coexists`, but consider correcting the axis to `same_attribute=no` |
| Medium | **H08** | `I stopped baking` explicitly ends the habit but offers no replacement routine | Keep `replaces`; set `new_value_known=no` if the axis means a specific new value |
| Medium | **H12** | Duplicate bus-commute statements were marked `new_value_known=yes` | Keep `duplicate`; consider `new_value_known=no` |

**Why these flags matter:** The current dashboard checks syntactic consistency (e.g., replacement should match a supersession action), but it cannot automatically verify that the *words* support an asserted referent, attribute, or replacement. Several semantically questionable final labels passed its structural validation. A targeted correction to these cases is preferable to bulk relabelling or silently editing past outputs.

## Reproducibility and constraints

- The three user-uploaded source files agree on provenance and their 24-case summary; no user JSON has been uploaded to GitHub.
- Experiment 012 is **distinct** from Experiments 010–011 and from the future blind two-human evaluation. The 24 Phase 8 cases have now been viewed by the same Qwen judge and a human reviewer. They must **not** later be presented as untouched, independent holdout evaluation data for that judge.
- `24/24 needs_review` reflects the conservative design: all modelled replacements require confirmation, plus invalid-evidence outputs. It is not a measure of how many AI labels were truly wrong.
- Do not compute 'human review accuracy' from the six approvals or thirteen matching labels; there is no independently validated answer key.

## Research interpretation and proposed Phase 9

**Decision:** Keep the evidence gate and human-supervised storage, but do not treat local `qwen2.5:1.5b` as a reliable autonomous adjudicator on this task. The all-`replaces` outputs show that prompt compliance and output quality are not sufficient even on simple fictional pairs.

Priorities: (1) add **semantic QA warnings** for cross-attribute or ambiguous-referent supersession before a human approves; (2) improve structured output enforcement and identify why 10 case responses lacked valid evidence axes; (3) compare at least one genuinely different locally available model or conservative deterministic baseline on **new examples**, without using one model's own drafts as truth; (4) explicitly test downstream false forgetting/answer reliability; (5) create an independent human-labelled set for publishable accuracy claims.

**Recommended immediate user action:** Revisit H02, H06 and H20 in the existing dashboard, followed by other flagged cases if the reviewer agrees. Each correction should generate a new signoff revision/report, preserving the original AI drafts and audit trail. Do not automatically replace or delete any user's memory.
