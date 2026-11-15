# Experiment 005A — Irrelevant memory test

**Status:** Manual experiment completed; observations reported by the project owner. The assistant did not execute the experiment or inspect the local database.

## Setup

- **Prompt (as instructed):** "What city do I currently live in?"
- **Selected synthetic memory (as instructed):** topic `snack`, fact "My favourite snack is apple slices."
- **Model:** Local Qwen through the Memory Impact Lab; exact model revision and locally selected memory were not independently verified
- **Ground truth available to the model:** No city information in the selected memory
- **Conditions:** Both calls use the same question. One receives no memory, and the other receives the irrelevant snack memory.

## Observations

| Condition | Reported exact answer | Elapsed |
|---|---|---:|
| Without memory | "I don't have enough information in the saved memories to answer that." | 5.60s |
| With irrelevant memory | "I don't have enough information in the saved memories to answer that." | 2.15s |

## Interpretation

Both conditions **abstained appropriately** in this individual case. Providing the irrelevant snack memory did not cause an invented city in this observed run.

**Limits:** This is one user-reported qualitative example, not a hallucination-rate measurement. Differences in sequential-call timings should not be interpreted as a memory-related latency improvement: warm-up, cache, and system load are uncontrolled.

## Next test

Proceed to Experiment 005B: create a deliberately stale `location` memory for a fictional person whose independently specified current city is York. Compare the unsupported-by-ground-truth Bristol answer (if produced) against the later correct York update. Document exact outputs, not only whether the pilot passed.
