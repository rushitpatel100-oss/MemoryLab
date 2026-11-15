# V4 Phase 3 — Four-way conflict classification benchmark

## Research question

Can the MemoryLab system distinguish **duplicate**, **replaces**, **coexists**, and **uncertain** relationships between facts assigned the same topic?

- **Duplicate** — both facts state the same information (e.g. identical London work facts).
- **Replaces** — new information clearly updates the same attribute (e.g. moved from Bristol to York).
- **Coexists** — different facts can both be true (e.g. lives in York and works in London).
- **Uncertain** — missing referent or time information prevents a clear classification.

A deterministic case/spacing/Unicode/trailing-punctuation rule recognises **normalised exact repeats** before calling Qwen. It is not semantic equivalence. The local Qwen model is used for other examples; its four-label predictions can still be incorrect.

## Fictional development dataset

[benchmarks/conflict_cases.json](../benchmarks/conflict_cases.json) contains **16 fictional cases**: four per label, interleaved so that the first four cover every label. Each case includes a rationale and an **author-chosen expected label**. The labels are not independently adjudicated; some uncertain examples may be contestable.

This is a small **development diagnostic**, not a blinded, held-out study.

## Running locally on Windows

From the cloned project folder in the existing virtual environment:

~~~bat
python -m unittest discover -s tests -v
python -m scripts.run_conflict_benchmark --limit 4
~~~

The first command runs entirely offline with mocked Ollama responses. The second calls your local Ollama/Qwen for non-identical cases. Run all 16:

~~~bat
python -m scripts.run_conflict_benchmark
~~~

If you want to save a JSON report to an ignored local folder:

~~~bat
python -m scripts.run_conflict_benchmark --output results/raw/conflicts.json
~~~

The benchmark doesn't read or edit `memorylab.db`. Its counts and confusion matrix measure **agreement with the small supplied development labels**, not general accuracy. All software remains free.

## Evaluation notes

Track per-class errors, repeated trials, model/configuration, ambiguous cases, and the local deterministic-rule versus Qwen proportions. Before any research claims, create labelled examples from entirely new synthetic user profiles, get independent label reviews, freeze evaluation criteria, and evaluate on an unseen test set. A successful manual demonstration or four-case smoke test is not sufficient to claim a novel memory policy.

## First live development-run observation

The project owner ran the first four synthetic cases: **2/4 agreed with the original expected labels**. D01 and R01 passed; C01 failed because Qwen suggested `replaces` for compatible residence and work facts; U01 was marked a miss against the supplied `uncertain` label, but that label is itself contestable. Qwen predicted `replaces` for every one of its three calls. The duplicate pass came from the deterministic rule, not from Qwen. See [Experiment 006](experiment_006_results.md) for exact case outcomes, confusion counts and annotation concerns. This is one owner-reported development run, not a reliable accuracy estimate.
