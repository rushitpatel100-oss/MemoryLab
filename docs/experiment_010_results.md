# Experiment 010 — First label-first replacement-gate comparison

**Source:** MemoryLab owner-provided local JSON export `review_v1_results.json` from the Phase 6 review workflow, timestamped **2026-11-15 11:33:29 UTC**. The local model was **Ollama `qwen2.5:1.5b`**. The assistant inspected the exported results; it did **not** execute local Ollama itself.

**Dataset:** `benchmarks/review_v1_cases.json`, 20 fictional cases, SHA-256 `c23de988a620b541c336517cbcda54094fc7e0a061a08bd51620e229c8fc2bd9`. The GitHub dataset intentionally contains no expected labels; evaluation uses a local, complete, locked human review file (`review_v1_labels.json`). The attached export contains the labels but not the reviewer's original explanation text or the label-lock timestamp. We therefore describe this as **one reviewer, labels collected before scoring through the workflow**, not independent multi-rater adjudication.

## Results: both conditions reuse the same Qwen predictions

| ID | Locked reviewer label | Raw Qwen | Gated |
|---|---|---|---|
| B01 | coexists | coexists | coexists |
| B02 | coexists | replaces | uncertain |
| B03 | replaces | replaces | replaces |
| B04 | coexists | coexists | coexists |
| B05 | coexists | coexists | coexists |
| B06 | replaces | replaces | replaces |
| B07 | uncertain | replaces | uncertain |
| B08 | duplicate | duplicate | duplicate |
| B09 | coexists | coexists | coexists |
| B10 | coexists | replaces | uncertain |
| B11 | replaces | replaces | replaces |
| B12 | duplicate | replaces | uncertain |
| B13 | replaces | replaces | replaces |
| B14 | coexists | coexists | coexists |
| B15 | replaces | replaces | uncertain |
| B16 | replaces | replaces | replaces |
| B17 | coexists | coexists | coexists |
| B18 | coexists | replaces | uncertain |
| B19 | replaces | replaces | replaces |
| B20 | coexists | coexists | coexists |

| Metric | Original single-pass Qwen | Qwen + deterministic evidence gate |
|---|---:|---:|
| Agreement with locked human labels | 15/20 (75%) | 15/20 (75%) |
| False `replaces` against human non-replacement labels | 5 | **0** |
| Labelled `coexists` but predicted `replaces` | 3 | **0** |
| Human-labelled genuine replacements recognized | 7/7 | 6/7 |
| Genuine replacements not recognized | 0/7 | 1/7 |
| Output `uncertain` | 0 | 6 |

The raw Qwen label was obtained **once per case**, then the local evidence gate reclassified its output. The owner reported 20 `qwen` sources and **51.835 seconds** cumulative model time. That is *shared* inference time, not the sum of two model runs. This experiment does not support a claim that the guard increases overall label agreement or downstream task accuracy.

### What changed, case by case

- **B02 (reviewer: `coexists`)**: dog Peanut wears a red collar; new note says the dog's collar was replaced, without stating its new colour. Qwen's `replaces` became gate `uncertain`. A collar replacement does not automatically prove the previously recorded colour is false, but the true current colour may be unknown.
- **B07 (reviewer: `uncertain`)**: a named cousin Iris lives in Brighton; an unnamed cousin is said to have moved to Oxford. Gate `uncertain` matches the reviewer because identity cannot be assumed.
- **B10 (reviewer: `coexists`)**: telescope storage in cabinet three vs an unspecified device being moved. Gate `uncertain` avoids deactivating the telescope fact. `Uncertain` may be a better category than `coexists` here, because the identity of the moved device is unknown.
- **B12 (reviewer: `duplicate`)**: learning to play drums vs learning drums. Qwen incorrectly predicted `replaces`; the gate returns `uncertain`, avoiding risky supersession but still missing the duplicate label.
- **B15 (reviewer: `replaces`)**: a Tuesday chess-club meeting vs unspecified changed meeting details. The guard returns `uncertain`, losing one match with the human replacement label. The new time and even which details changed are unspecified; this warrants label-rubric adjudication.
- **B18 (reviewer: `coexists`)**: Nora volunteers at the library vs one of several volunteers taking another role. The gate returns `uncertain` rather than assuming the unnamed volunteer is Nora.

Five raw false replacement suggestions became `uncertain`, not necessarily the correct `coexists` or `duplicate` label; only **B07** became an exact match that was previously incorrect. Conversely **B15** became incorrect against its locked label. Thus total agreement stayed **15/20**.

## Annotation quality and interpretive cautions

- **B04 (label `coexists`)**: `I enjoy mystery novels.` and `Mystery novels are something I enjoy.` appear to be paraphrased duplicate facts. Both systems' agreement on `coexists` matches the stored human label but not a clear semantic duplicate reading. Preserve the locked label for the original score, and queue independent adjudication.
- **B10 and B18 (label `coexists`)**: Both involve ambiguous unspecified subjects; `uncertain` can be more defensible than asserting proven coexistence.
- **B02 and B15:** Replacement of an object or changes to unspecified meeting details are not necessarily identical to changing the old *attribute value*. The rubric must distinguish **known invalidation of old information** from **known replacement value**.
- The reviewer's labels are heavily imbalanced (10 `coexists`, 7 `replaces`, 2 `duplicate`, 1 `uncertain`), with no multi-rater disagreement statistics. A 20-item one-shot comparison cannot establish general safety or broad reliability.
- The examples were created within the project after earlier model-error analysis, although this dataset was newly labelled before its first scoring. They are **not a fully independent, externally designed held-out benchmark**.

## Conclusion and next decision

The evidence gate shows a **desirable risk trade-off** on this small synthetic set: all five model suggestions to supersede a fact contrary to reviewer labels were converted to cautious review. It did so without extra Qwen calls, but it also made one human-labelled replacement uncertain and did not improve overall agreement.

**Freeze the present model, gate, dataset and original labels for reproducibility.** Next prioritize an independent rubric-adjudication pass on B02, B04, B10, B12, B15 and B18 (and B07 for reference identity) before designing another learned or rule-based policy. The adjudication should record `same_entity`, `same_attribute`, `old_fact_known_obsolete`, `new_value_known`, and a proposed storage action separately; retain the original label and amended review side-by-side. Then evaluate future changes on an entirely fresh synthetic holdout with at least two raters, and report false supersession, missed real updates, abstention rate and downstream answer impact.

**Safety:** Neither evaluation method modified SQLite. Automatic supersession remains prohibited in section 7; a human must explicitly confirm changing any active memory. The old section 1 overwrite baseline remains deliberately unsafe for conflict-aware storage.

**No fees:** No new paid services, APIs or packages were introduced in Experiment 010.
