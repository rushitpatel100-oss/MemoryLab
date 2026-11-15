# Experiment 008 — Initial four-case paired classifier comparison

**Evidence:** User-reported local output of `python -m scripts.compare_classifiers --limit 4`. This is a synthetic, author-labelled comparison candidate, not a held-out accuracy estimate. The assistant did not rerun Qwen locally.

| Case | Expected | Baseline | Two-stage | Baseline (s) | Staged (s) |
|---|---|---|---|---:|---:|
| E01 | duplicate | duplicate (match) | duplicate (match) | 0.00 | 0.00 |
| E02 | coexists | coexists (match) | replaces (miss) | 5.74 | 4.67 |
| E03 | replaces | replaces (match) | replaces (match) | 2.29 | 4.80 |
| E04 | uncertain | replaces (miss) | replaces (miss) | 2.43 | 4.96 |

**Agreement with initial labels:** baseline 3/4; staged 2/4. **False replacement suggestions:** baseline 1; staged 2. **Coexistence falsely labelled replacement:** baseline 0; staged 1.

**Total elapsed time for paired conditions:** baseline 10.457s, staged 14.429s. Staged was approximately 38% slower in this single small ordered run; baseline executes first and timing can be affected by model warm-up/cache effects.

## Interpretation

- **E01:** An identical formatting-normalised repeat was caught by the deterministic local rule; not evidence about Qwen.
- **E02:** Studying marine biology and practising cello after school are compatible independent facts. The baseline rightly classified `coexists`; the staged model classified `replaces`. Given the staged code path, a replacement requires Stage 1 to pass through `same_attribute` and Stage 2 to suggest `replaces`. The trace was not provided, so we have not seen Qwen's explanation for either stage.
- **E03:** Repainting a bicycle from red to blue explicitly updates its colour. Both models matched the expected `replaces` label.
- **E04:** An aunt named Farah working at a hospital and a generic statement that 'my aunt changed jobs' may concern different people. The expected `uncertain` is reasonable, but requires an explicit labelling rubric. Both classifiers suggested `replaces`.

## Next steps

1. Keep both classifier implementations and the original expected labels unchanged for now; don't optimise based on only four examples.
2. Run all 16 comparison cases with the JSON trace export:

   `python -m scripts.compare_classifiers --output results/raw/staged_comparison.json`

3. Inspect `staged_trace`, `baseline_reason`, and `staged_reason` to locate whether each error originated in attribute-scope classification or same-attribute update assessment.
4. Evaluate false supersession and cost/latency alongside agreement with author labels. Independently adjudicate ambiguous examples before general conclusions.

The runner does not read or write `memorylab.db`. The output is saved locally under a Git-ignored folder. Human approval remains mandatory for any memory deactivation.
