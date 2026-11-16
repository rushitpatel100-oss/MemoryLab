# MemoryLab 🧠

**A local-first research project exploring adaptive memory for LLM assistants.**

MemoryLab investigates an important GenAI engineering question: **when should an assistant retrieve, update, or suppress a remembered fact?** We are building simple baselines first, then comparing them against a proposed utility-based memory policy.

> **Current status: Experiment 015 — V4 behavior reviewed; false-duplicate suppression identified.** In 24 previously exposed fictional cases, V4 returned **7 `duplicate` and 17 `uncertain`**, with no `replaces` or `coexists`. **H18 and H20 were unflagged, incorrect duplicate proposals**, so accepting AI-generated `skip_duplicate` suggestions without verification could silently drop an update or distinct fact. A new offline audit requires confirmation before treating any V4 duplicate as skippable. Existing V4 outputs, earlier reports, human signoffs and SQLite memories are preserved. These results are **diagnostics, not independent accuracy**. See [Experiment 015](docs/experiment_015_results.md).

## Features

1. **Store a memory** under a topic in a local SQLite database.
2. **Update a topic** by marking older facts superseded (history remains visible).
3. **Search active memories** using exact/partial topic matching.
4. **Semantic search** with Ollama's local `all-minilm` embeddings and cosine similarity.
5. **Ask MemoryLab** a natural-language question; retrieve candidate memories and pass them to `qwen2.5:1.5b` running on Ollama.
6. **Inspect retrieved evidence**, including memory IDs and similarity scores.
7. **Memory Impact Lab (pilot):** run two Qwen calls, with and without one selected memory, and inspect both answers.
8. **Smart Memory Review (experimental):** classifies four relationships and blocks exact duplicate writes; compatible and conflicting facts still need user review.
9. **Development benchmark:** 16 fictional examples (four per label), local inference, a confusion matrix, and optional JSON export.
10. **Two-stage conflict experiment:** compare attributes first, evaluate updates only when appropriate, and compare against the unchanged single-pass baseline on a separate 16-case fictional dataset.
11. **Replacement-evidence safeguard (experimental):** checks for explicit old-to-new value changes and requires three confirmations before any reviewed supersession.
12. **Blind evaluation workflow:** manually label 20 new fictional cases before seeing model predictions, lock the labels, then score raw versus guarded recommendations.
13. **Multi-reviewer adjudication (Phase 7):** a second reviewer independently labels 20 cases and four evidence dimensions, followed by a disagreement queue and separately saved adjudication decisions.

**Important limits:** Section 1 still treats all facts under one exact topic as replacements. Section 7 can save multiple facts under one topic, but only compares **exactly matching topics**. Its deterministic duplicate rule handles formatting-only repeats, not all semantic paraphrases; Qwen's suggestions can still be wrong. Similarity is *not* a probability that a memory is true. A small LLM can still make mistakes or ignore grounding instructions. Don't use real private information while developing or documenting experiments.

## Setup on Windows (Python 3.14 / 16 GB RAM)

All components run locally. The app uses no cloud AI API, credit card, or paid inference.

In GitHub Desktop, open the cloned **MemoryLab** repository in VS Code. Open a **Command Prompt (cmd)** terminal inside the folder.

If the cloned folder doesn't have its own Python environment yet:

~~~bat
py -3.14 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
~~~

If you already created `.venv`, simply activate it. For other Python versions, replace `-3.14` with your installed version.

### 1. Install or confirm Ollama

Download Ollama for Windows from https://ollama.com/download.

In Command Prompt, pull the two free local models:

~~~bat
ollama pull all-minilm
ollama pull qwen2.5:1.5b
ollama list
~~~

`all-minilm` creates embeddings; `qwen2.5:1.5b` generates the answer. They serve different purposes. The 1.5B chat model is intended for modest hardware and can run on CPU if GPU acceleration isn't available. The first inference may be slower.

### 2. Run offline tests

~~~bat
python -m unittest discover -s tests -v
~~~

These tests mock Ollama network calls. They validate request formatting, empty-input handling, vector ranking, and basic output parsing; they do **not** prove that Qwen generates correct answers.

### 3. Launch

~~~bat
python -m streamlit run app.py
~~~

Visit http://localhost:8501 if the browser doesn't open by itself.

### 4. Try Version 3

Start with a new, **fictional** test fact:

- **Topic:** `job`
- **Information:** `I work as a GenAI engineer.`
- Click **Save memory**.

Go to **5. Ask MemoryLab**, enter `What is my profession?`, and click **Generate answer from memory**.

An expected answer is something like *"You work as a GenAI engineer."* Open **See retrieved memory evidence** to inspect the memory used. Exact wording is model-dependent; test whether the answer is supported, not whether it matches the example verbatim.

**Next validation: negative control.** With only a `job` or `hobby` memory saved, ask `What is my favourite colour?` (or another fact you did not store). A grounded response should admit that the saved memories do not establish the answer. Check *See retrieved memory evidence* to see whether an unrelated memory was selected. If Qwen guesses a colour or invents supporting evidence, record this as a **grounding failure**. If no memory meets the similarity threshold and the application declines to call Qwen, record this as a **retrieval-stage abstention**, not proof that Qwen itself refused to hallucinate.

If the app says no relevant memories met the threshold, decrease the experimental similarity slider or add a more relevant memory. The default threshold of `0.25` is a starting heuristic, **not a calibrated confidence cutoff**.

If the app reports that Ollama is unavailable, confirm it is running and that both models appear in `ollama list`.


## First research experiment: positive vs negative control

Run two manual scenarios on a **synthetic** profile and record what happens.

| Test | Saved memory | Question | Expected behaviour |
|---|---|---|---|
| Positive control | topic: hobby; fact: "My favourite hobby is photography." | What hobby do I enjoy? | Answer "photography" based on memory evidence |
| Negative control | Same hobby memory only (no location saved) | What city do I live in? | Report missing evidence, or have retrieval abstain |

Track: retrieved memories, similarity scores, whether Qwen was called, answer, whether the answer is supported, and the type of failure. This qualitative check is a **pilot**, not a research benchmark. Do not claim an accuracy percentage from two examples.

The next phase will automate controlled "with vs. without memory" experiments over synthetic scenarios, with explicit scoring criteria and repeatable results.

## Try the memory-impact pilot (V4 Phase 1)

This small, **manual** experiment is not yet a learned policy. The no-memory baseline genuinely calls Qwen with an empty evidence list rather than returning a fixed fallback.

1. In **1. Add a memory**, save fictional topic `hobby`: `My favourite hobby is photography.`
2. Scroll to **6. Memory Impact Lab**.
3. Select that memory and ask `What hobby do I enjoy?`.
4. Click **Run with/without-memory experiment**. Both conditions use the same Qwen model and settings.
5. Read the two results side by side and manually decide which answer is supported by the fictional fact.
6. Optionally download the JSON result. It includes the memory and answer texts, so **don't commit it or publish it with personal data**.

See [the guided pilot](docs/ablation_pilot.md), [Experiment 004 results](docs/experiment_004_results.md), and [Experiment 005 protocol](docs/experiment_005_protocol.md).


### Windows SQLite file-lock fix (Python 3.14)

If early V4 installations showed `PermissionError: [WinError 32]` during unit-test `tearDown`, the root cause was SQLite connections that were committed but not explicitly **closed**. The context manager `with sqlite3.connect(...) as conn` manages transactions, not connection closure. Version 4 now uses `contextlib.closing` alongside the transaction context manager in the app, test fixtures, and reviewed-memory store. Re-run `python -m unittest discover -s tests -v` after pulling this fix; the expected result is 20 passing tests. This fix has not yet been verified on the user's Windows machine.

## Try Smart Memory Review — V4 Phase 2

No new models or packages are needed. In section **7. Smart Memory Review**, propose a new fact and click **Review possible conflicts**. Qwen provides a recommendation for each active memory in the exact same topic; **Keep both** is selected by default. Confirm each action before saving. Section 1 remains a deliberately simplistic overwrite baseline.

Follow the [conflict-review experiment guide](docs/conflict_review.md) to test Bristol → York updates and simultaneous work/home locations. The second test revealed an `uncertain` label for compatible facts; this is documented as a classification error and motivated a prompt revision. The first prototype limits same-topic reviews to at most 10 active memories.

## Test four-way classification — V4 Phase 3

The new relationships are **Duplicate**, **Replaces**, **Coexists**, and **Uncertain**. A normalised identical active fact with the same topic is detected locally, without asking Qwen, and the SQLite write is rejected even if the UI is bypassed. Matching ignores letter case, repeated spaces, Unicode compatibility, and simple trailing punctuation. The existing records are **not migrated or deleted**.

In **section 7**, enter topic `test_location` and fact `I work in London.` if this fact is already active. The display should show **duplicate (local_rule)** and **Save reviewed memory** should be disabled. If Qwen calls a *paraphrase* a duplicate, the UI instead asks for explicit confirmation before allowing a save. The local normalisation cannot prove that two differently worded facts mean the same thing.

Run offline tests:

~~~bat
python -m unittest discover -s tests -v
~~~

Try a small balanced benchmark (one example from each class):

~~~bat
python -m scripts.run_conflict_benchmark --limit 4
~~~

Run all 16 fictional development cases:

~~~bat
python -m scripts.run_conflict_benchmark
~~~

Optional result export (the folder is gitignored):

~~~bat
python -m scripts.run_conflict_benchmark --output results/raw/conflicts.json
~~~

The benchmark only calls the local classifier, **never your SQLite database**, and does not upload anything. It is an **author-labelled development smoke test**, not a held-out accuracy result. See the [benchmark guide](docs/conflict_benchmark.md), [case definitions](benchmarks/conflict_cases.json), and [Experiments 006](docs/experiment_006_results.md) and [007](docs/experiment_007_results.md) for live results and disputed labels.

## Compare classifiers — V4 Phase 4

**The original classifier remains the baseline.** In section **7. Smart Memory Review**, select **Two-stage experimental** under **Classification method** before proposing a memory. It asks local Qwen to identify whether claims address **independent attributes**, the **same attribute**, or an **unclear relationship**. If independent, it proposes **Coexists**. If unclear, it proposes **Uncertain**. Only same-attribute comparisons move to a second Qwen call about whether the new fact duplicates, replaces, coexists with, or leaves the old one uncertain.

This is a decision-support experiment, **not automated truth verification or memory deletion**. Every supersession still requires your explicit selection. The model's intermediate judgments can be wrong, and the staged method may be slower because it sometimes calls Qwen twice.

Pull the latest commit in GitHub Desktop, then run the offline unit tests:

~~~bat
python -m unittest discover -s tests -v
~~~

The new suite is expected to have **42 tests**. They mock Ollama and **do not prove** the new classifier performs better in reality.

Compare **both** classifiers on the first four cases of a **separate synthetic evaluation candidate**:

~~~bat
python -m scripts.compare_classifiers --limit 4
~~~

Then evaluate all 16, without changing the prompts between runs:

~~~bat
python -m scripts.compare_classifiers
~~~

Optional JSON export, ignored by Git:

~~~bat
python -m scripts.compare_classifiers --output results/raw/staged_comparison.json
~~~

The comparison code **never opens or edits your SQLite memory database**. It reports matches with author labels, how often non-replacement facts were wrongly marked `replaces`, and cumulative local inference time. It does **not** make an unqualified accuracy claim. The new cases were constructed after seeing development errors, so they are not independently labelled or a definitive blind test.

Read [the staged-classifier protocol](docs/staged_classifier.md), [the new 16 cases](benchmarks/conflict_eval_v1.json), and [Experiment 008](docs/experiment_008_results.md) for the first four-case comparative observations.

## Replacement-evidence safeguard — V4 Phase 5

The review interface now has three methods: **Single-pass baseline**, **Safety-gated experimental**, and **Two-stage experimental**. The safety-gated method uses the same single Qwen call as the baseline plus a local text check. It never makes another model call. When Qwen suggests `replaces` without a narrow `from old value to new value` transition anchored to text in the older fact, the suggestion becomes `uncertain` and the raw Qwen prediction remains visible.

Even a detected transition is **only a text signal**. It does not establish the same subject, attribute, or factual truth. All supersession choices in section 7 now require fresh manual checks for **same subject**, **same specific attribute**, and **actual outdatedness**. The safe default remains **Keep both**. The existing section 1 overwrite baseline is deliberately unchanged.

On Windows after **Fetch origin → Pull origin**, run:

~~~bat
python -m unittest discover -s tests -v
~~~

Expected: **54 tests** (42 previous, 12 added), using mocked calls only. Then test the safeguard on the first four previously seen synthetic examples:

~~~bat
python -m scripts.compare_replacement_gate --limit 4
~~~

Run all 16 and save a local report if useful:

~~~bat
python -m scripts.compare_replacement_gate --output results/raw/gate.json
~~~

The script never opens the SQLite database and calls Qwen **once per case**, not once for each variant. It reports both false replacement suggestions and **genuine replacements missed** by the narrow gate. The examples were already inspected when the rule was designed; this is not a held-out accuracy estimate. See the [replacement-gate protocol](docs/replacement_gate.md).

## Phase 6 — Blind review before model evaluation

The earlier experimental scores were measured on examples we had already discussed. To reduce that bias, this phase provides **20 new fictional fact pairs without expected labels** in `benchmarks/review_v1_cases.json`.

**Important:** The owner has now completed a first label-locked evaluation on all 20 cases. Those labels are separate from the code author's but **not independently adjudicated by multiple experts**. Keep them unchanged for reproducibility; use the steps below only for a fresh local workflow.

After pulling from GitHub Desktop, run the offline tests first:

~~~bat
python -m unittest discover -s tests -v
~~~

Expected suite size: **63 tests**. These use mocked responses; the new workflow hasn't yet been run on your Windows laptop.

**Start with only four review cases:**

~~~bat
python -m scripts.review_eval_cases --limit 4
~~~

You will see each old and new fictional fact. Choose a relationship using **D** (duplicate), **R** (replaces), **C** (coexists), or **U** (uncertain), and enter a short reason. You can skip or quit; your completed labels are saved automatically. No Qwen call occurs during review.

**Resume later, review status and lock when finished:**

~~~bat
python -m scripts.review_eval_cases
python -m scripts.review_eval_cases --status
python -m scripts.review_eval_cases --lock
~~~

Locking is refused if any case is unlabelled or the dataset has changed. Only **after locking**, run:

~~~bat
python -m scripts.evaluate_review_v1
~~~

The evaluator calls local Qwen once per pair and applies the gate to that **same** response. It reports agreement with your labels, incorrect replacement suggestions, missed genuine updates, and a confusion matrix in the saved JSON.

The labels and results stay under `results/raw/`, excluded from GitHub, and neither script reads or writes your SQLite memories. Details are in [the blinded-review protocol](docs/blind_review.md) and the [Experiment 010 results](docs/experiment_010_results.md).

## Phase 7 — Second reviewer and adjudication

**This is the next research milestone, not another model update.** Experiment 010 identified some disputed original labels, so we are collecting a **second person's independent judgements** before changing either classifier. The local Python tools never call Qwen or change saved memories.

**A separate person** should use this review workflow on the same 20 fictional examples **without seeing** the first reviewer's labels or Experiment 010 predictions. The program keeps the second review in a different local file and records: relation label, short reason, same entity, same attribute, whether the old fact is known outdated, whether a new value is known, and a proposed storage action. A second pass by the same person is useful for testing but **does not count as independent agreement**.

First pull in GitHub Desktop and run the offline tests:

~~~bat
python -m unittest discover -s tests -v
~~~

**Expected test count: 83**, including 20 Phase 7 review tests. They mock model access. This release has not yet been run on your Windows laptop.

Let the **second reviewer** enter the first four cases:

~~~bat
python -m scripts.review_second --limit 4
~~~

Then they can resume at any point and freeze their completed review:

~~~bat
python -m scripts.review_second
python -m scripts.review_second --status
python -m scripts.review_second --lock
~~~

**Only after the second review is locked**, compare reviewers (no model is called):

~~~bat
python -m scripts.compare_human_reviews
~~~

This reports exact agreement, a descriptive Cohen's kappa, and a local list of disagreements **plus seven pre-registered review cases** (B02, B04, B07, B10, B12, B15, B18). Even a shared mistaken label is worth checking on these cases.

Finally, a human can adjudicate the flagged cases separately:

~~~bat
python -m scripts.adjudicate_reviews --limit 4
python -m scripts.adjudicate_reviews
python -m scripts.adjudicate_reviews --status
python -m scripts.adjudicate_reviews --lock
~~~

Adjudication can **defer** cases that lack evidence; it does not silently change the original scores or labels. Outputs remain local under `results/raw/`, excluded from GitHub, and contain only fictional cases if you use the supplied dataset. See [Phase 7 methodology and instructions](docs/multirater_review.md).

### Correction utility for unfinished adjudications

An uploaded partial adjudication (4 of 8 flagged cases) exposed mismatched labels, evidence fields and storage actions. The review CLI supports `python -m scripts.adjudicate_reviews --edit B04` to revisit any **already answered, unlocked** case. It preserves the previous decision in a local revision history. `--status` surfaces conflicting storage choices, and `--lock` prevents accidental finalisation when a duplicate is marked for supersession. **No uploaded JSON or saved memory is modified automatically.**

After pulling from GitHub Desktop, run the revised suite:

~~~bat
python -m unittest discover -s tests -v
~~~

Expected **83 offline tests** (up from 81). Resume pending cases with `python -m scripts.adjudicate_reviews`, then inspect `--status`, fix flagged entries with `--edit BXX`, and only then use `--lock`.

## Experiment 011 — Post-adjudication comparison

The owner has now completed the 8 flagged adjudication cases, producing `review_v1_adjudicated_summary.json`. First and second review labels agreed **18/20**. The final labels changed **B04** from coexists to duplicate, and **B07** from uncertain to coexists. Reusing the original Qwen predictions gives **14/20 agreement raw** and **13/20 gated**; the guarded system still made **0 false replacement recommendations** against final labels, compared with **5** for raw Qwen, but withheld **1 of 7** labelled genuine updates.

The summary contains unresolved conceptual tensions, especially B07, B10, B15 and B18. These warrant rubric review rather than silently relabelling the dataset. See the [full Experiment 011 analysis](docs/experiment_011_results.md).

To reproduce the descriptive scoring locally **without Ollama**, retain the original two JSON exports in `results/raw/` and run:

~~~bat
python -m scripts.rescore_adjudicated
~~~

This writes `results/raw/review_v1_adjudicated_metrics.json`. The first label file, second label file and stored memories remain untouched. The latest offline suite now contains **89 tests**, including six new scorer tests (not yet verified on the user's Windows machine).

## Phase 8 — Frozen rubric + fresh blind evaluations

### Recommended workflow — AI drafts, you verify and edit

**You do not need to type labels for all 24 fictional cases.** Use the local AI to draft them, then use a browser dashboard to inspect the full report, correct mistakes and approve the rest.

~~~bat
python -m scripts.auto_review_holdout_v2
python -m streamlit run app_review.py
~~~

Step 1 creates a separate AI draft file. Step 2 opens the Streamlit dashboard: see all 24 facts and natural-language explanations, **approve unchanged unflagged cases in one explicit action after reading them**, then address any flagged cases individually. Nothing is written to your SQLite memory database.

When all 24 have signoffs, use the dashboard's **Download complete human-reviewed AI report** control. You can also save a versioned Markdown report locally in `results/raw/`, with source AI labels, final human-reviewed answers and an audit trail of changes in a separate JSON file. Your original four Reviewer A answers are not changed or silently reclassified.

**Research provenance matters:** Final wording should be **AI-generated annotations, human-verified/corrected**. Cases approved in bulk are marked as *bulk-attested*, not *individually annotated by a human*. A model cannot create independent human ground truth by writing natural-sounding prose. See [signoff and report instructions](docs/human_verification.md).

### Fast path — automatic AI review (no more manual labelling)

**You can skip completing Reviewer A and B** if your goal is to get useful automated suggestions rather than a rigorous independent accuracy estimate. After GitHub Desktop **Fetch origin → Pull origin**, run:

~~~bat
python -m scripts.auto_review_holdout_v2
~~~

This uses the **existing local Ollama `qwen2.5:1.5b`**, attempts all 24 fictional memory pairs, and creates the private file `results/raw/holdout_v2_ai_review.json`. It prints provisional relationship labels and flags missing information or contradictory storage choices. It does **not** modify your first four Reviewer A answers, Reviewer B, the SQLite database, or old experiment files. You can close the terminal and resume unfinished cases by running the **same command** again; successful cases are automatically skipped.

To inspect the saved progress without invoking Ollama:

~~~bat
python -m scripts.auto_review_holdout_v2 --status
~~~

If a different locally installed judge model is available, `--model MODEL_NAME` can be specified **before the first automatic run**; an existing report is intentionally tied to its original model and cannot silently be overwritten. No new software or subscription is required for the default command.

**Research warning:** This is AI-assisted *triage*, **not an independent human study**. Qwen auto-labelling the same data on which Qwen is evaluated would be circular. The existing `evaluate_holdout_v2` refuses these AI drafts as A/B labels. For externally credible accuracy, independent human reviews are still necessary. For development and a portfolio demonstration, this automatic output can help identify ambiguous cases quickly. See the [automatic review guide](docs/auto_review.md).


We have stopped tuning the classifier on the 20 previously examined cases. Instead, Phase 8 supplies **24 new fictional memory pairs with no answers** and a clearer human annotation rubric. The models and SQLite records are unchanged.

Read the **[decision rubric v2](docs/label_rubric_v2.md)** before making any labels. It asks whether the facts concern the same entity, same specific attribute, whether the old fact is *known* outdated, and whether a specific new value is *known*. These axes are separate from the four-way relationship and storage recommendation.

After **Fetch origin → Pull origin**, start by checking offline tests:

~~~bat
python -m unittest discover -s tests -v
~~~

Expected: **122 offline test methods** (115 before the human signoff feature, plus 7 new). The new tests have not yet been executed on your Windows machine.

**Reviewer A starts with four new cases (no Qwen):**

~~~bat
python -m scripts.review_holdout_v2 --rater A --limit 4
~~~

To resume or check progress:

~~~bat
python -m scripts.review_holdout_v2 --rater A
python -m scripts.review_holdout_v2 --rater A --status
~~~

Only after all **24/24** are labelled, freeze A's labels:

~~~bat
python -m scripts.review_holdout_v2 --rater A --lock
~~~

**A different human Reviewer B** should separately follow the same steps using `--rater B`, without reading A's labels or previous Qwen outputs. If one person fills both files, this is a repeat review, **not independent inter-rater validation**.

**Only after both A and B are locked**, run:

~~~bat
python -m scripts.evaluate_holdout_v2
~~~

The evaluator **refuses to run with an unlocked review** and never reads the SQLite memory database. It runs the unchanged Qwen classifier once per pair, applies the unchanged gate to the same prediction, and measures performance only where reviewers' labels agree. Disagreements are reported separately, not treated as gold labels. It refuses to overwrite an earlier local result.

Documentation: [Phase 8 review instructions](docs/phase8_protocol.md).

## Phase 9 — Evidence-first automatic reviewer (experimental)

After Experiment 012 found **24/24 Qwen drafts labelled `replaces`**, Phase 9 introduces an **independent versioned reviewer**. It does not change your original Phase 8 reviewer or overwrite the previous 24 AI outputs. The goal is to prevent the model from treating every added fact as a replacement.

Instead of asking the LLM directly for a relation label, the new reviewer requests **five structured evidence fields** and literal supporting quotes from the old and new statements. It then uses a conservative local decision policy. If the model fails to provide evidence, or a referent/role seems contradictory, it labels the relationship `uncertain`. Even a proposed `replaces` requires explicit human review; **nothing is stored, deleted, or superseded**.

**In GitHub Desktop, Fetch origin → Pull origin.** Then use your existing MemoryLab terminal:

~~~bat
python -m unittest discover -s tests -v
python -m scripts.auto_review_v3
python -m scripts.compare_ai_review_versions
~~~

Expected **161 offline test methods** (145 before V4, plus 16 new). The tests and local Ollama integration still need execution on your Windows machine. The Phase 9 judge requires a recent Ollama release supporting JSON-schema output; if you encounter an error, keep your old files untouched and share the terminal message.

The reviewer saves progress one case at a time in `results/raw/holdout_v2_ai_review_v3.json`. Running the same command again resumes remaining cases. The comparison requires your **original** `results/raw/holdout_v2_ai_review.json` and creates distinct local `phase9_ai_comparison.json` / `.md` files; it refuses to overwrite a prior comparison. **Do not rerun the old reviewer to replace its historical output.**

**Research limit:** H01–H24 have already been exposed to previous AI outputs and human edits. A different distribution of labels is *not* evidence of accuracy improvement. Future accuracy tests require newly authored cases and independent blind human labels. See [Phase 9 protocol](docs/phase9_protocol.md).

## Experiment 013 follow-up — all-uncertain Phase 9 diagnosis

The user-supplied comparison found **0/24 `replaces` and 24/24 `uncertain` for the new Phase 9 AI judge** (the older AI judge had the exact opposite distribution). Both flagged all cases. We need per-case failure reasons before editing prompts or models.

After **Fetch origin → Pull origin**, run the new standalone analysis on the existing V3 JSON:

~~~bat
python -m scripts.diagnose_phase9
~~~

It writes `results/raw/phase9_failure_diagnostics.md` without making new Ollama calls. The report counts invalid/missing source quote evidence, uncertainty in each of the five evidence axes and repeated warnings. The cause of the model's 24 abstentions remains **unconfirmed until that evidence is inspected**. See [Experiment 013](docs/experiment_013_results.md).

## Experiment 014 — Phase 9 evidence failure diagnosed; V4 proposed

Your uploaded `phase9_failure_diagnostics.md` showed that the **V3 judge returned usable evidence quotes in 24/24 cases** but recorded **`unknown` for all five evidence fields in all 24 cases** (120/120 unknown values). There were **no missing quote or malformed-axis warnings**; every case had only the generic `Evidence is insufficient for a firm relation.` warning. This looks like wholesale conservative abstention in the small local judge, but the raw model responses were not preserved and we cannot prove *why* it abstained.

V4 makes a new **experimental** prediction file; it does not alter your existing V3 or signed decisions. It reserves `unknown` for the two genuinely ambiguous identity/attribute fields, while asking the model to answer yes/no for exact repetition, **proven** obsolescence, and existence of a replacement value. It uses unrelated examples, source-quote checks, and deterministic rules before proposing a label. Risky replacements always stay `review_needed`, never executed. The local raw response text is kept under Git-ignored `results/raw/` for diagnosis.

After GitHub Desktop **Fetch origin → Pull origin**, run:

~~~bat
python -m unittest discover -s tests -v
python -m scripts.auto_review_v4
python -m scripts.compare_v3_v4
~~~

The expected offline suite is **169 test methods** (161 before the safety audit, plus 8 new). These tests and real Ollama calls haven't been run on the user's laptop yet. The V4 run saves to `results/raw/holdout_v2_ai_review_v4.json`; the comparator saves `results/raw/phase9_v4_diagnostic.md`. Both reuse **previously exposed fictional cases**, so a more diverse label distribution would **not** prove better accuracy. For rigorous evaluation use fresh independently labelled examples.

See [Experiment 014](docs/experiment_014_results.md).

## Experiment 015 — V4 false duplicates and safe review

The V4 diagnostic returned seven unflagged duplicate proposals. **H18 (rosemary replaced by lavender)** and **H20 (home versus away jerseys)** are clearly not duplicates, demonstrating a **false-skip risk**. The new standalone safety audit flags suspicious duplicate decisions and requires human approval for **every** candidate duplicate before skipping any new information.

```bat
python -m scripts.audit_review_v4
```

Output: `results/raw/phase9_v4_safety_audit.md`. This command needs the **existing complete V4 AI JSON** saved locally, makes **no new Ollama calls**, and never modifies either review JSON or SQLite. The expected suite is now **169 offline tests** (8 new). Its warning heuristics are not a substitute for independent human labels. See [Experiment 015](docs/experiment_015_results.md).

## Project files

| Path | Purpose |
|---|---|
| `app.py` | Streamlit app, memory storage, search, and QA interface |
| `semantic_search.py` | Calls Ollama for embeddings; ranks memories |
| `answer_generator.py` | Calls Ollama's local chat endpoint with retrieved evidence; supports empty-context experiments |
| `memory_ablation.py` | Runs two local Qwen calls with/without one selected memory |
| `memory_conflicts.py` | Existing four-label single-pass baseline with local duplicate check |
| `memory_staged.py` | Experimental attribute-scope check followed by conditional update assessment |
| `replacement_gate.py` | Conservative text evidence gate for single-pass replacement suggestions |
| `scripts/compare_replacement_gate.py` | Compare raw and gated decisions on the same Qwen output |
| `benchmarks/review_v1_cases.json` | 20 fictional examples deliberately lacking answer labels |
| `scripts/review_eval_cases.py` | Resumable terminal reviewer and label-lock workflow |
| `scripts/evaluate_review_v1.py` | Refuses unlocked labels and scores the paired Qwen/gate run |
| `docs/blind_review.md` | Evaluation rubric, step-by-step use and study limitations |
| `docs/experiment_010_results.md` | First 20-case paired model-versus-gate findings and label issues |
| `scripts/review_second.py` | Separate blind second-reviewer labels plus four evidence dimensions |
| `scripts/compare_human_reviews.py` | Post-lock label agreement, Cohen's kappa, and disagreement queue |
| `scripts/adjudicate_reviews.py` | Independent-from-original-file adjudication records and optional deferred labels |
| `docs/multirater_review.md` | Phase 7 workflow, interpretation, and known limitations |
| `scripts/rescore_adjudicated.py` | Offline comparison of frozen Experiment 010 predictions with final labels |
| `docs/experiment_011_results.md` | Phase 7 outcome, revised metrics and disputed evidence axes |
| `docs/label_rubric_v2.md` | Frozen entity/attribute/obsolete/new-value evidence rules |
| `benchmarks/holdout_v2_cases.json` | 24 new fictional pairs with no labels or predictions |
| `scripts/review_holdout_v2.py` | Independent A/B evidence-first labels, resumable and lockable |
| `scripts/evaluate_holdout_v2.py` | After both reviews lock: one-call paired Qwen/gate scores on consensus subset |
| `scripts/auto_review_holdout_v2.py` | One-command local Ollama case triage; separate AI suggestions, no human-score claim |
| `docs/auto_review.md` | Auto-review usage, limits and interpretation |
| `app_review.py` | Streamlit dashboard to approve, correct, and export AI-first review reports |
| `scripts/review_signoff.py` | Independent approval record, audit trail and versioned report generation |
| `docs/human_verification.md` | AI-first review workflow and precise provenance language |
| `docs/experiment_012_results.md` | All-`replaces` AI failure, 24-case human signoff analysis and semantic audit flags |
| `scripts/auto_review_v3.py` | Phase 9 schema-backed evidence-first AI drafts (distinct output) |
| `scripts/compare_ai_review_versions.py` | Offline label distribution and disagreement diagnostic, never accuracy |
| `docs/phase9_protocol.md` | Phase 9 commands, methodological limits, and preservation safeguards |
| `scripts/diagnose_phase9.py` | Offline counts of V3 missing evidence, quote failures and abstention flags |
| `docs/experiment_013_results.md` | Phase 9 all-uncertain outcome and revised 24-case signoff findings |
| `scripts/auto_review_v4.py` | Separate contrastive yes/no evidence judge; raw response retained for debugging |
| `scripts/compare_v3_v4.py` | AI-only evidence and label distribution comparison (never accuracy) |
| `docs/experiment_014_results.md` | Diagnosis of valid quotes and 120 unknown axes, V4 rationale and cautions |
| `scripts/audit_review_v4.py` | Offline safety audit of risky duplicate-skip suggestions; never changes source data |
| `docs/experiment_015_results.md` | V4 output analysis, two false duplicates and next safeguards |
| `docs/phase8_protocol.md` | Step-by-step Phase 8 process and limitations |
| `benchmarks/conflict_eval_v1.json` | Separate 16-case fictional comparison candidate |
| `scripts/compare_classifiers.py` | Paired baseline-versus-staged evaluation, including false replacement counts |
| `memory_text.py` | Shared conservative text normalisation for duplicate checking |
| `benchmarks/conflict_cases.json` | 16 author-labelled fictional development cases |
| `scripts/run_conflict_benchmark.py` | Local benchmark, per-label confusion counts and optional export |
| `memory_store.py` | Atomically applies only human-approved supersession choices |
| `docs/conflict_review.md` | Guided experiment for changing locations and coexisting facts |
| `docs/ablation_pilot.md` | Guided first experiment and how to interpret results |
| `tests/` | Offline unit tests; does not require Ollama |
| `docs/research_plan.md` | Hypothesis, baselines, metrics, experimental stages |
| `requirements.txt` | Python dependencies (Streamlit only at present) |
| `.gitignore` | Excludes local data, environments, secrets, model weights |

## Research question and planned evaluation

**Hypothesis (unverified):** Downstream utility-aware memory policies may reduce contradictions and improve answer accuracy over recency-only and semantic similarity retrieval.

**Baselines:** exact topic matching → recency → semantic retrieval → proposed utility policy.

**Planned measures:** accuracy on held-out synthetic user histories, contradiction rate, false forgetting, retrieval relevance, inference latency, and computational cost.

Read the full [research plan](docs/research_plan.md).

## Roadmap

- [x] **V1:** SQLite memory history, topic replacement, Streamlit interface (user-tested)
- [x] **V2:** Ollama embedding-based semantic search (user-tested on three example questions)
- [x] **V3:** Local Qwen answer generation with retrieved memory evidence (**model runs locally; factual grounding still being evaluated**)
- [ ] **V4:** Utility-based retention/suppression policy (**phases 1–4 investigated; phase 5 evidence-gated safety prototype published; no learned policy yet**)
- [ ] **V5:** Reproducible held-out evaluation, ablations, and error analysis (**Phase 8 rubric and fresh unlabeled cases frozen; A/B reviews, local validation, and independent adjudication pending**)

## Budget and privacy

Required software and models are free. Target total development spend: **£0**, with an absolute **£20 cap** for the entire MemoryLab project (excluding existing hardware, electricity, and connectivity).

`memorylab.db`, virtual environments, model weights, and local secrets are excluded from GitHub. Memory files stay on your laptop. This repository is intended to be safe to publish after reviewing documentation, issues, screenshots, and test examples for personal data.

**No performance or novelty claim should be made without controlled experiments and comparison to relevant prior work.**
