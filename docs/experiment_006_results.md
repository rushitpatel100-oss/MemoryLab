# Experiment 006 — First four-label classifier development smoke test

**Status:** Owner-reported live run of the locally installed MemoryLab prototype. Not a held-out performance estimate.

## Configuration

- Command: `python -m scripts.run_conflict_benchmark --limit 4`
- Development dataset: `benchmarks/conflict_cases.json` version 0.1, first four synthetic cases
- Model: local Ollama `qwen2.5:1.5b`, temperature 0, JSON output requested
- Duplicate handling: local, deterministic formatting-normalised text rule, before LLM inference
- Observation: one manual run; environment and model-version hash not independently collected

## Results (verbatim labels/counts from owner)

| ID | Expected | Predicted | Result | Source | Elapsed |
| --- | --- | --- | --- | --- | --- |
| D01 | duplicate | duplicate | PASS | local_rule | 0.0s |
| C01 | coexists | replaces | MISS | qwen | 5.804s |
| R01 | replaces | replaces | PASS | qwen | 2.285s |
| U01 | uncertain | replaces | MISS per current label | qwen | 2.244s |

**Development-label agreement:** 2/4. This is **not** held-out accuracy.

**Source breakdown:** 1 `local_rule`; 3 `qwen`. The model itself matched 1 of the 3 author-assigned labels in this single run, but this fraction is too small and the U01 label is contestable.

Confusion counts (rows expected, columns predicted):

| Expected \ Predicted | coexists | duplicate | replaces | uncertain |
| --- | ---: | ---: | ---: | ---: |
| coexists | 0 | 0 | 1 | 0 |
| duplicate | 0 | 1 | 0 | 0 |
| replaces | 0 | 0 | 1 | 0 |
| uncertain | 0 | 0 | 1 | 0 |

## Error analysis

**C01 (clear error):** OLD="I have moved from Bristol to York." NEW="I work in London." Both can be true: the information is about residence versus work. Qwen incorrectly predicted `replaces`. The current prompt already contains a nearly identical coexistence example; therefore this failure is not simply fixed by adding the example again. Do not change the benchmark or prompt just to force a pass.

**U01 (label ambiguity):** OLD="Alex's appointment is on Tuesday." NEW="The appointment was moved." The current expected label is `uncertain`, citing unspecified referent and new date. However, the definite phrase "the appointment" may naturally refer to Alex's appointment; if so the Tuesday schedule has been superseded even though the new date is unknown. Qwen's `replaces` may be defensible. Flag this item for independent adjudication; **keep the original 0.1 expected label and recorded score unchanged** for reproducibility.

**D01:** The exact-ish duplicate was detected without model inference. It verifies the deterministic path, not Qwen's duplicate reasoning.

**R01:** A clear explicit location update was correctly classified as replacing, for this one observation.

## Next experiment

1. Freeze and retain version 0.1 of the four-case output as a baseline.
2. Run all 16 development cases without changing the prompt or expected labels. Record per-case failures and the confusion matrix.
3. Review disputed `uncertain` labels separately and make a versioned adjudicated test set, rather than silently relabelling previously reported cases.
4. Only after broader error analysis, compare alternatives (structured attribute/time reasoning, stronger local model where feasible, or narrower deterministic rules) on an **unseen** synthetic test set.
5. Keep human approval for supersession. Inference output is not authority to remove user facts.
