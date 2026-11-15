# MemoryLab 🧠

**A local-first research project exploring adaptive memory for LLM assistants.**

MemoryLab investigates an important GenAI engineering question: **when should an assistant retrieve, update, or suppress a remembered fact?** We are building simple baselines first, then comparing them against a proposed utility-based memory policy.

> **Current status: V4 Phase 4 paired comparison underway.** The previous single-pass classifier matched 10/16 author labels in Experiment 007. The initial four-case live comparison of the staged alternative matched 2/4 versus 3/4 for baseline, with an additional incorrect replacement suggestion. The staged method is **not yet shown to improve decisions**. Full 16-case comparison and stage-trace review are pending; this is not a validated holdout or learned utility policy.

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

## Project files

| Path | Purpose |
|---|---|
| `app.py` | Streamlit app, memory storage, search, and QA interface |
| `semantic_search.py` | Calls Ollama for embeddings; ranks memories |
| `answer_generator.py` | Calls Ollama's local chat endpoint with retrieved evidence; supports empty-context experiments |
| `memory_ablation.py` | Runs two local Qwen calls with/without one selected memory |
| `memory_conflicts.py` | Existing four-label single-pass baseline with local duplicate check |
| `memory_staged.py` | Experimental attribute-scope check followed by conditional update assessment |
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
- [ ] **V4:** Utility-based retention/suppression policy (**phases 1–3 evaluated; phase 4 two-stage classifier code and paired evaluation published, local testing pending**)
- [ ] **V5:** Reproducible held-out evaluation, ablations, and error analysis

## Budget and privacy

Required software and models are free. Target total development spend: **£0**, with an absolute **£20 cap** for the entire MemoryLab project (excluding existing hardware, electricity, and connectivity).

`memorylab.db`, virtual environments, model weights, and local secrets are excluded from GitHub. Memory files stay on your laptop. This repository is intended to be safe to publish after reviewing documentation, issues, screenshots, and test examples for personal data.

**No performance or novelty claim should be made without controlled experiments and comparison to relevant prior work.**
