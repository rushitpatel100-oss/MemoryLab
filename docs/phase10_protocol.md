# Phase 10 — Downstream memory preservation and answer evaluation

**Stage:** Development evaluation framework published; local experiment results pending. **Dataset:** `benchmarks/downstream_memory_v1.json` (14 newly authored fictional scenarios, 28 questions). This is **not independent human-labelled model accuracy** and not a new untouched holdout once development begins.

## The question this phase addresses

Can different memory-retention strategies **preserve needed facts, avoid retaining obsolete facts, and supply appropriate evidence to an answer generator**? Past phases mostly assigned `duplicate/replaces/coexists/uncertain` labels and audited risky suggestions. A correct-looking relationship label is not enough if the next question loses a needed fact.

## Three clearly defined storage policies

| Policy | What it does | Whether it uses the real application code |
|---|---|---|
| `reviewed` | Applies the scenario's **author-scripted** decisions: keep, selectively supersede, or skip a duplicate | Yes, invokes real `memory_store.save_reviewed_memory` with explicit decisions and temporary SQLite |
| `topic_overwrite` | Deactivates **every** earlier active fact in the incoming topic before inserting the new one | Reproduces the broad-topic behaviour of `app.py`'s baseline |
| `append_all` | Keeps every stated fact, even obsolete or repeated ones | Explicit algorithmic baseline, temporary SQLite |

All three use the same sequence of synthetic facts. The reference `reviewed` actions are **provided by the fixture**, so perfect agreement with its expected active set would demonstrate only that the code followed a supplied decision. It would not show whether an autonomous classifier can choose the right decision.

## Quick start on Windows

1. GitHub Desktop: **Fetch origin → Pull origin**.
2. Open the usual terminal in the MemoryLab folder; activate `.venv` if necessary.
3. Run:

~~~bat
python -m unittest discover -s tests -v
python -m scripts.evaluate_downstream_memory
~~~

Expected **201 offline tests** (177 before this phase, 17 storage tests and 7 semantic tests). The offline evaluator uses only standard-library temporary SQLite and has no running-model requirement.

Offline result files:

- `results/raw/phase10_storage_all.json` — per-case policy/active-fact records and evidence availability.
- `results/raw/phase10_storage_all.md` — readable comparison, missing required facts and retained obsolete facts.

4. Optional: run the actual answer generator on all active memories; no embedding retrieval:

~~~bat
python -m scripts.evaluate_downstream_memory --with-llm --policy reviewed
~~~

Result: `results/raw/phase10_llm_reviewed.json` and `.md`. This condition isolates **storage** changes from retrieval errors; all currently active synthetic memories are supplied to `answer_generator.generate_answer`. The same `qwen2.5:1.5b` settings are used, but there is no guarantee of correct answers.

5. Optional: run **real semantic retrieval** with the same local `all-minilm` ranker and answer generator as the application:

~~~bat
python -m scripts.evaluate_semantic_outcomes
~~~

Result: `results/raw/phase10_semantic_reviewed.json` and `.md`. The script uses `find_similar`, filters to similarity 0.25 and keeps the top three, mirroring `app.py` Section 5; then calls `generate_answer`. It separately records **was the fact stored?** and **did retrieval select the supporting fact?**

6. For both optional model modes, append `--limit 3` to run a small subset first, then run the same command without it to resume. To include all three policies, use `--policy all` (which saves different filenames).

Each completed scenario is saved to Git-ignored `results/raw/` before moving on. A rerun skips saved cases, and an incompatible dataset/model or policy configuration refuses to overwrite an existing run. The Markdown output is generated when all selected cases have completed; existing Markdown reports are never overwritten.

## What is and is not scored

**Offline:** Measures exact active-step retention against the authored expected set, missing facts, extra facts, obsolete facts still active and whether a supporting fact is present for an answerable query. It directly tests the application's selective SQLite write function, but *not* the real Qwen classifier.

**Full-memory Qwen:** Records model answers and whether a literal **author-specified answer phrase** appears (or an expected abstention phrase appears). This is an automatic *proxy*, not human-adjudicated factual truth. A keyword inside an incorrect, quoted or negated answer may falsely count as a match.

**Semantic retrieval + Qwen:** Adds whether the required supporting source was among the **retrieved** top-three memories and records the same crude text proxy. An answer can fail because the needed fact was overwritten, because the embedding threshold excluded it or because the model did not use the retrieved information properly. The report separates these modes where possible but does not establish a causal effect without further controlled repeats.

**Do not claim:** independently verified accuracy, generalized improvement, reliable protection against real-world false forgetting, independent label quality, or real user performance. An authored test set is a useful reproducible regression fixture, not a new external gold standard.

## Privacy and safety

- Only **fictional** facts in the committed benchmark are used. Temporary SQLite databases are created and deleted per scenario/policy run. The program never opens `memorylab.db`.
- All stored results go under `results/raw/` and are ignored by Git. Do not commit raw personal memories or API credentials.
- The Phase 10 experiment **does not** automatically accept the V4 reviewer decisions; it uses the synthetic reference decisions to isolate retention outcomes.
- No changes to past H01–H24 reviews, Experiments 010–016, original classifiers, or previous signoffs are required.

## Next steps after you share the reports

Compare which policies lose necessary information or keep obsolete information. Inspect at least the **cases where actual Qwen answers disagree with the keyword proxy**. Document retrieval versus generation failure modes separately. Then design a fresh blinded independently labelled test set, and only after that consider learning a retention policy from downstream utility.
