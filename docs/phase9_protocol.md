# MemoryLab — Phase 9 evidence-first reviewer

## Why this version exists

During Experiment 012, a local `qwen2.5:1.5b` AI reviewer output `replaces` for **all 24** fictional cases, including obvious duplicates and compatible facts. These labels were subsequently inspected and edited, but not independently validated. The new Phase 9 implementation is designed to *reduce unjustified confidence*, not to artificially boost agreement with the user's edited labels.

## How it works

1. Qwen is asked to fill **five independent evidence questions**, not to choose a relationship directly: exact same entity, exact same attribute, same assertion/paraphrase, definite invalidation of the old statement, and a specific new value.
2. The model supplies **literal quoted evidence** from both old and new facts. Missing or invented evidence is flagged and the relation becomes `uncertain`.
3. A transparent conservative rule selects `duplicate` for supported paraphrases, `replaces` for explicitly invalidated old facts, `coexists` for separately compatible facts, and `uncertain` otherwise.
4. A few **generic referent/role warnings** (for example home vs away, office vs basement, and indefinite `one of`) block confident replacement. These are conservative heuristic warnings, not semantic proof.
5. No evidence alone permits an AI-driven memory overwrite. Even supported `replaces` is classified as `needs_review` for storage.

**Important:** The model may still misunderstand the facts or quote misleading snippets. Valid JSON is not factual validity. The deterministic policy does not establish that a model's evidence is true; the whole system remains an experimental diagnostic.

## Beginner instructions (Windows)

1. Update the repository using GitHub Desktop: **Fetch origin → Pull origin**.
2. Open your usual MemoryLab terminal and test the repository:

~~~bat
python -m unittest discover -s tests -v
~~~

Expected test count after Phase 9: **139** (17 new test methods); Windows execution remains unverified.

3. Check that your local Ollama server is running and the existing `qwen2.5:1.5b` model remains installed. Run:

~~~bat
python -m scripts.auto_review_v3
~~~

This reads the **same 24 previously exposed fictional cases** solely for a retrospective regression diagnostic. It does not open your human signoffs or memory database. It writes `results/raw/holdout_v2_ai_review_v3.json`. The script saves after each completed case and resumes unfinished work on the next run.

4. Compare the output with the *original* historical AI draft:

~~~bat
python -m scripts.compare_ai_review_versions
~~~

It reads `results/raw/holdout_v2_ai_review.json` and the new V3 draft; requires the dataset and all case IDs to match; writes **`results/raw/phase9_ai_comparison.md`** and `phase9_ai_comparison.json`. An existing report is preserved rather than overwritten.

5. Open the Markdown report for a summary of AI label distributions, flagged cases and disagreements. Upload the report or new V3 JSON to ChatGPT if you want a case-specific error analysis.

## Compatibility

The v3 reviewer sends Ollama's chat API a strict JSON-schema `format` object. This requires an Ollama server version that accepts JSON schema in `format`. No paid API or Python dependency is added. If your older Ollama version returns an HTTP error, do **not** delete the original results; report the error and update Ollama through official installation methods if appropriate. You may test with `--limit 4` before doing all cases.

## Evaluation integrity and provenance

- **Never** overwrite `results/raw/holdout_v2_ai_review.json`, `holdout_v2_human_signoff.json`, or the previous human-reviewed Markdown report.
- **Never** describe a change in the AI's output distribution as improved accuracy or independent validation. H01–H24 have already been inspected, revised and discussed; they are *not new held-out data*.
- The Phase 9 outputs are AI-generated and do **not** unlock the separate two-human blind evaluator, change previously signed decisions, or prove the user's revisions were factually correct.
- The correct next research step after inspecting behavior differences is to create **fresh fictional profiles**, obtain blinded labels from independent reviewers (or clearly document an AI-assisted process), and evaluate false supersession and downstream answers.

The reviewed data and existing SQLite memory remain local; the project keeps the previous experimental record unchanged.

## Phase 9 run reviewed — evidence failure diagnostics

The uploaded `phase9_ai_comparison.md` reported **24/24 `uncertain`** on the new policy, down from the original **24/24 `replaces`**. Since both methods flagged 24/24 cases, this is a collapse into abstention rather than demonstrated classification improvement. We cannot determine the cause from the comparison table alone. A new offline tool can examine the saved Phase 9 evidence:

~~~bat
python -m scripts.diagnose_phase9
~~~

This writes `results/raw/phase9_failure_diagnostics.md` and changes no existing JSON or SQLite data. Upload that Markdown or the underlying `holdout_v2_ai_review_v3.json` for evidence-level debugging. Six mocked test methods were added, raising the expected offline count to **145**. See [Experiment 013](experiment_013_results.md).

## Experiment 014 — V3 evidence diagnosis and versioned V4 test

The owner-uploaded diagnostic found **valid old/new quotes on all 24 cases**, but **all 120 evidence axes were `unknown`**. That suggests V3 was abstaining semantically rather than failing to format its JSON. The new V4 review version narrows three evidence questions to yes/no while keeping ambiguous entity/attribute evidence open to unknown. It stores raw model output for future debugging and uses a separate local file, never overwriting V3. Run:

~~~bat
python -m scripts.auto_review_v4
python -m scripts.compare_v3_v4
~~~

The comparison is saved as `results/raw/phase9_v4_diagnostic.md`. The expected offline suite now contains **161 tests** (16 new tests for V4 and its comparator). V4 is not yet validated on the user's local Ollama instance and the 24 source cases are previously exposed, not independent held-out data. See [Experiment 014](experiment_014_results.md).

## V4 case review — Experiment 015 safety audit

The user-uploaded V4 diagnostic reported 7 duplicate labels, 17 uncertain, and 17 flagged cases out of 24. The two most important missed warnings were **H18**, where rosemary in a planter was explicitly replaced with lavender, and **H20**, where the home and away jerseys describe separate things. V4 erroneously called both `duplicate` without flagging them. This is why the absence of an AI warning cannot be treated as proof of a safe skip.

The new `python -m scripts.audit_review_v4` command checks saved V4 JSON and writes `results/raw/phase9_v4_safety_audit.md`. It flags change language and distinct role qualifiers without relying on those specific case IDs, and requires explicit approval for all AI-proposed duplicate skips. It doesn't re-run Qwen, modify your reviewer signoffs, or delete memories. Eight mocked tests were added; the expected suite is now **169 tests**. See [Experiment 015 results](experiment_015_results.md).
