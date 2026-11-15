# Version 4 Phase 4 — Two-stage conflict classification

## Motivation

The first Qwen-only approach tended to predict `replaces` even for compatible home/work facts. In owner-reported Experiment 007, 16 author-labelled development cases matched only 10/16, including 2/4 expected coexistence cases and 0/4 disputed expected uncertainty cases. The four duplicates were handled by a local rule.

Rather than simply tailoring another prompt to those same 16 cases, the experimental approach splits the decision.

## How the two stages work

1. **Existing exact-duplicate rule:** If normalised same-topic text matches an active memory, return `duplicate` immediately, without Qwen.
2. **Stage 1 (attribute scope):** Ask Qwen whether two statements concern **independent** properties/roles, the **same** specific property, or an **unclear** referent. A shared topic alone does not establish a shared attribute.
3. **Independent:** Suggest `coexists` and stop. **Unclear:** Suggest `uncertain` and stop.
4. **Same attribute:** Call Qwen again for a focused decision: `duplicate`, `replaces`, `coexists`, or `uncertain`. A vague change without an explicit new value should generally remain `uncertain`, but the distinction is subject to rubric review.
5. **Human review:** The classifier returns suggestions and a visible trace. Only the user can approve supersession. No code automatically changes a memory based on the model.

Invalid model output yields `uncertain`, not `replaces`. Network errors surface to the user without modifying memory data. The pipeline never checks truth independently.

## Run the offline unit tests (Windows)

~~~bat
python -m unittest discover -s tests -v
~~~

The full suite now contains **42 tests** (up from 30). The new tests use mocked local inference to verify stage routing and scoring, not model correctness.

## In-app demo

Open **7. Smart Memory Review**, choose **Two-stage experimental** under **Classification method**, enter a fictional topic and new fact, and click **Review possible conflicts**. Inspect the proposed relationship and **See decision steps**. Do not click Save if simply evaluating the classifier.

The single-pass option is still available and existing stored memories remain unchanged. Both classifiers compare records sharing the same exact topic and use the original human-reviewed storage action.

## Paired comparison

A new set of **16 synthetic fictional examples** (four per label) is in [conflict_eval_v1.json](../benchmarks/conflict_eval_v1.json). They deliberately differ from the original 16 development examples. However, the author created them after seeing prior failures, and their labels have not been independently reviewed; this is an evaluation *candidate*, not definitive held-out evidence.

Run four cases first:

~~~bat
python -m scripts.compare_classifiers --limit 4
~~~

Then all sixteen:

~~~bat
python -m scripts.compare_classifiers
~~~

Optionally keep detailed local results:

~~~bat
python -m scripts.compare_classifiers --output results/raw/staged_comparison.json
~~~

The command compares both methods on the **same examples** and prints:

- Agreement with author-expected labels (descriptive, not population accuracy).
- **False replacements:** number of items expected to be anything other than `replaces`, but predicted `replaces` (the most harmful suggestion for memory retention).
- **Coexistence false replacements:** subset where independent facts were incorrectly suggested as replacements.
- Total inference time for baseline versus staged.

**Caveats:** Calls execute baseline first, staged second; warm-up/order effects can bias latency. Local temperatures are set to zero but inference is not necessarily perfectly reproducible. Some uncertain labels are subjective. A larger independently labelled, shuffled and repeated comparison is needed before making improvement claims. Neither method should auto-supersede memories.

## No new dependencies

Uses only Python's standard library plus existing Streamlit and the local Ollama `qwen2.5:1.5b` model. No database migrations. No paid API or subscriptions.

## First comparison — Experiment 008

The owner ran four cases from the separate evaluation candidate. Baseline matched **3/4** author labels, staged matched **2/4**; baseline made one false replacement suggestion, staged made two. The experimental approach did not show an advantage in this run. See [Experiment 008](experiment_008_results.md) for exact predictions, elapsed timings, and the request to inspect stage traces in the full 16-case run.
