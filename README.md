# MemoryLab 🧠

**A local-first research project exploring adaptive memory for LLM assistants.**

MemoryLab investigates an important GenAI engineering question: **when should an assistant retrieve, update, or suppress a remembered fact?** We are building simple baselines first, then comparing them against a proposed utility-based memory policy.

> **Current status: V4 Phase 2 conflict-review code published; laptop testing pending.** Versions 1–3 and the V4 memory-impact experiment have been user-tested. Section 7 now proposes whether a new fact replaces or coexists with same-topic memories and requires explicit review before saving. This is not yet a learned policy or validated research benchmark.

## Features

1. **Store a memory** under a topic in a local SQLite database.
2. **Update a topic** by marking older facts superseded (history remains visible).
3. **Search active memories** using exact/partial topic matching.
4. **Semantic search** with Ollama's local `all-minilm` embeddings and cosine similarity.
5. **Ask MemoryLab** a natural-language question; retrieve candidate memories and pass them to `qwen2.5:1.5b` running on Ollama.
6. **Inspect retrieved evidence**, including memory IDs and similarity scores.
7. **Memory Impact Lab (pilot):** run two Qwen calls, with and without one selected memory, and inspect both answers.
8. **Smart Memory Review (experimental):** suggest relationship between facts and let you choose exactly which older records stay active.

**Important limits:** Section 1 still treats all facts under one exact topic as replacements. Section 7 can save multiple facts under one topic, but only compares **exactly matching topics**, and Qwen's suggestions can be wrong. Similarity is *not* a probability that a memory is true. A small LLM can still make mistakes or ignore grounding instructions. Don't use real private information while developing or documenting experiments.

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

Follow the [conflict-review experiment guide](docs/conflict_review.md) to test Bristol → York updates and simultaneous work/home locations. The first prototype limits same-topic reviews to at most 10 active memories.

## Project files

| Path | Purpose |
|---|---|
| `app.py` | Streamlit app, memory storage, search, and QA interface |
| `semantic_search.py` | Calls Ollama for embeddings; ranks memories |
| `answer_generator.py` | Calls Ollama's local chat endpoint with retrieved evidence; supports empty-context experiments |
| `memory_ablation.py` | Runs two local Qwen calls with/without one selected memory |
| `memory_conflicts.py` | Gets pairwise Qwen suggestions (replaces / coexists / uncertain) |
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
- [ ] **V4:** Utility-based retention/suppression policy (**phase 1 tested; phase 2 human-reviewed conflict prototype published, local validation pending**)
- [ ] **V5:** Reproducible held-out evaluation, ablations, and error analysis

## Budget and privacy

Required software and models are free. Target total development spend: **£0**, with an absolute **£20 cap** for the entire MemoryLab project (excluding existing hardware, electricity, and connectivity).

`memorylab.db`, virtual environments, model weights, and local secrets are excluded from GitHub. Memory files stay on your laptop. This repository is intended to be safe to publish after reviewing documentation, issues, screenshots, and test examples for personal data.

**No performance or novelty claim should be made without controlled experiments and comparison to relevant prior work.**
