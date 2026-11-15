# Experiment 007 — All 16 development cases (unchanged classifier)

**Status:** Owner-reported local run of MemoryLab after Experiment 006. Data are fictional; predictions were not independently rerun by the assistant. This is NOT a held-out research accuracy estimate.

## Reproducibility

- Command: `python -m scripts.run_conflict_benchmark`
- Dataset: `benchmarks/conflict_cases.json`, version 0.1, 16 author-labelled synthetic cases
- Local model: Ollama `qwen2.5:1.5b`, temperature 0, JSON response; model hash not recorded
- Classifier: four-way (`duplicate`, `replaces`, `coexists`, `uncertain`), with formatting-normalised duplicate short-circuit
- One pass, without changing model instructions between Experiment 006 and Experiment 007

## Results (owner-reported labels and elapsed durations)

| ID | Expected | Predicted | Source | Seconds | Evaluation |
|---|---|---|---|---:|---|
| D01 | duplicate | duplicate | local_rule | 0.0 | PASS |
| C01 | coexists | replaces | qwen | 2.589 | MISS |
| R01 | replaces | replaces | qwen | 2.44 | PASS |
| U01 | uncertain | replaces | qwen | 2.422 | MISS |
| D02 | duplicate | duplicate | local_rule | 0.0 | PASS |
| C02 | coexists | coexists | qwen | 2.482 | PASS |
| R02 | replaces | replaces | qwen | 2.312 | PASS |
| U02 | uncertain | replaces | qwen | 2.501 | MISS |
| D03 | duplicate | duplicate | local_rule | 0.0 | PASS |
| C03 | coexists | coexists | qwen | 2.446 | PASS |
| R03 | replaces | replaces | qwen | 2.417 | PASS |
| U03 | uncertain | replaces | qwen | 2.489 | MISS |
| D04 | duplicate | duplicate | local_rule | 0.0 | PASS |
| C04 | coexists | replaces | qwen | 2.401 | MISS |
| R04 | replaces | replaces | qwen | 2.394 | PASS |
| U04 | uncertain | replaces | qwen | 2.457 | MISS |

**Agreement with original development labels: 10/16 (62.5%).** Four duplicate cases were decided by the deterministic rule; the remaining **12 Qwen calls matched 6/12 (50%)** author labels. Do not attribute the 4/4 duplicate performance to Qwen.

**Classifier source counts:** `local_rule: 4`; `qwen: 12`. Qwen predicted `replaces` ten times and `coexists` twice in this one run; none of its calls predicted `uncertain` or `duplicate`.

### Confusion counts (rows = expected; columns = predicted)

| Expected / Predicted | coexists | duplicate | replaces | uncertain |
|---|---:|---:|---:|---:|
| coexists | 2 | 0 | 2 | 0 |
| duplicate | 0 | 4 | 0 | 0 |
| replaces | 0 | 0 | 4 | 0 |
| uncertain | 0 | 0 | 4 | 0 |

## Qualitative error analysis

- **C01 — likely clear classification mistake.** Residence in York and employment in London can coexist. Label `replaces` would wrongly encourage superseding a valid location fact.
- **C04 — likely clear classification mistake.** Working as a designer and volunteering as a football coach can coexist; they describe different roles. Qwen predicted `replaces`.
- **U01, U02, U03, U04 — disputed development labels.** All four currently expect `uncertain`, but several new statements imply that the same item (appointment/deadline/reservation/address) has been updated, despite withholding the replacement value. Under a policy of suppressing stale details, `replaces` might be defensible; under a policy of requiring a fully specified new fact, `uncertain` is defensible. Do not silently relabel or erase the misses. Resolve the difference by defining precisely what the relation labels mean, preferably using an independently reviewed rubric and a new versioned dataset.
- **R01–R04 — 4/4 against authored labels** for explicit updates; this does not establish general replacement classification accuracy.
- **D01–D04 — 4/4 against authored labels** for formatting-normalised repeats; all were bypasses of local Qwen inference.

## Research decision

**Do not tune the same prompt simply to chase 16/16 on this development set.** The priority is reducing false supersession: Qwen has predicted `replaces` for independent facts that should coexist, so human review must remain mandatory before deactivating a fact.

Recommended follow-up: create a label rubric that separates **relation** (same attribute vs independent) from **update completeness** (new value known vs unknown) and **storage action** (keep, supersede, or review). Then label unseen synthetic examples independently, freeze a holdout set, and compare an attribute-aware staged classifier against the present Qwen single-label baseline. Preserve v0.1 and Experiment 006/007 as immutable baselines.
