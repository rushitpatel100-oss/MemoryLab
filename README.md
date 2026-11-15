# MemoryLab 🧠

**A local-first research project exploring adaptive memory for LLM assistants.**

MemoryLab investigates an important GenAI engineering question: **when should an assistant retrieve, update, or suppress a remembered fact?** We are building simple baselines first, then comparing them against a proposed utility-based memory policy.

> **Current status: Version 3 code published (local end-to-end test pending).** Version 1's memory store and Version 2's semantic retrieval were tested on Windows by the project owner. Version 3 adds local Qwen answer generation using retrieved memories. This is a baseline, not yet a validated research result.

## Features

1. **Store a memory** under a topic in a local SQLite database.
2. **Update a topic** by marking older facts superseded (history remains visible).
3. **Search active memories** using exact/partial topic matching.
4. **Semantic search** with Ollama's local `all-minilm` embeddings and cosine similarity.
5. **Ask MemoryLab** a natural-language question; retrieve candidate memories and pass them to `qwen2.5:1.5b` running on Ollama.
6. **Inspect retrieved evidence**, including memory IDs and similarity scores.

**Important limits:** The app currently treats all facts under one exact topic as replacements. Similarity is *not* a probability that a memory is true. A small LLM can still make mistakes or ignore grounding instructions. Don't use real private information while developing or documenting experiments.

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

Next test an unrelated question such as `What is my favourite colour?`. A grounded response should admit that the saved memories do not establish the answer. This negative test is crucial.

If the app says no relevant memories met the threshold, decrease the experimental similarity slider or add a more relevant memory. The default threshold of `0.25` is a starting heuristic, **not a calibrated confidence cutoff**.

If the app reports that Ollama is unavailable, confirm it is running and that both models appear in `ollama list`.

## Project files

| Path | Purpose |
|---|---|
| `app.py` | Streamlit app, memory storage, search, and QA interface |
| `semantic_search.py` | Calls Ollama for embeddings; ranks memories |
| `answer_generator.py` | Calls Ollama's local chat endpoint with retrieved evidence |
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
- [ ] **V3:** Local Qwen answer generation with retrieved memory evidence (**code published; user test pending**)
- [ ] **V4:** Utility-based retention/suppression policy and counterfactual tests
- [ ] **V5:** Reproducible held-out evaluation, ablations, and error analysis

## Budget and privacy

Required software and models are free. Target total development spend: **£0**, with an absolute **£20 cap** for the entire MemoryLab project (excluding existing hardware, electricity, and connectivity).

`memorylab.db`, virtual environments, model weights, and local secrets are excluded from GitHub. Memory files stay on your laptop. This repository is intended to be safe to publish after reviewing documentation, issues, screenshots, and test examples for personal data.

**No performance or novelty claim should be made without controlled experiments and comparison to relevant prior work.**
