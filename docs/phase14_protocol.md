# Phase 14 — Optional local semantic answer verification

**Goal:** Explore whether checking *what a candidate answer means* against its retrieved factual context works better than looking for novel words. This is research only, not a replacement for the live answer generator.

## Why this phase

On the 32-case project-curated challenge, the Phase 12 novelty probe flagged **10 of 22 reviewer-labelled unsupported answers** and missed **12**. It also flagged **3 of 9 reviewer-labelled supported answers**. Its failures cluster around outdated values, entity swaps, negation and unsupported specifics that reuse existing words. See [Experiment 020](experiment_020_results.md).

## Run on Windows

After updating the clone with GitHub Desktop **Fetch origin → Pull origin**, run:

```bat
python -m unittest discover -s tests -v
python -m scripts.evaluate_semantic_verifier --limit 4
```

Expected total test methods: **264** (253 from prior phases plus 11 Phase 14 tests). These tests have not yet been executed on the user's Windows machine.

The first four cases act as a smoke test. If Ollama's local `qwen2.5:1.5b` is running and accepts structured JSON schema, finish the remaining cases by running:

```bat
python -m scripts.evaluate_semantic_verifier
```

The command checks that `results/raw/phase13_answer_signoff.json` exists and **all 32 reviewer labels are locked**. It uses the matching dataset SHA and frozen signoff SHA to prevent mixing changed inputs. It does **not** send any human labels to Qwen, and it **does not need another manual 32-case review**.

## Separate local outputs

- `results/raw/phase14_semantic_verifier.json` — progress saved after every fictional case; contains the model's raw JSON response, normalized verdict, memory quote, explanation and validation issues.
- `results/raw/phase14_semantic_verifier_comparison.md` — written only after all 32 answers are processed; shows the frozen human-review labels, the original lexical warnings, the semantic verdict and whether the verifier detected, missed or deferred on each case.

Old Phase 12/13 results and locked signoffs are never overwritten. Results go under Git-ignored `results/raw/`. The scripts do not open `memorylab.db`, call any cloud provider, or change `app.py`.

## How the model and evidence audit work

Each local Qwen request includes only the fictional retrieved memory records, its question and its prewritten candidate answer. It returns `supported`, `unsupported` or `uncertain`, a memory ID, a verbatim supporting or contradictory quote where applicable, and a reason. The original raw model message is saved for later debugging.

Invalid output, fabricated evidence quotes, and unsupported positive-evidence claims become *uncertain* in the normalized research verdict; their raw claims remain visible. An unsupported claim arising from *absence* of a needed fact may legitimately have no supporting quote. The system reports deferrals separately, because over-abstention caused severe coverage loss in Phase 11.

**Critical limit:** This verification relies on a small LLM, and a genuine quote can be irrelevant or temporally misapplied. Prompt examples are generic but the challenge's error categories were already discussed. Good-looking results here would still be development diagnostics, not independent model accuracy. Do not use either method to automatically block or discard a real memory or answer.

## What to inspect next

After the comparison finishes, examine whether the local verifier catches the 12 lexical misses **without** rejecting C05/C06/C08 or blindly abstaining. In particular, review entity bindings, stale versus current values, and unknowns. Then construct an independently curated *new* holdout with multiple blind reviewers before a production or portfolio accuracy claim.

Upload `phase14_semantic_verifier_comparison.md` for analysis.
