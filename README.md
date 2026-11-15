# MemoryLab 🧠

**An experimental memory system for long-running AI assistants.**

MemoryLab is a beginner-friendly, local-first GenAI engineering research project investigating when AI assistants should **retain, update, or suppress** stored information. The project will compare simple memory management against semantic retrieval and eventually utility-based memory policies.

> **Current status:** Version 1 (tested locally by the project owner) stores and searches memories, keeps version history, and marks earlier entries in the same topic as superseded. It does **not** yet use an LLM or detect contradictions intelligently.

## What works today

- Save a fact under a topic such as "job" or "hobby".
- Update a topic: the previous entry becomes **superseded**, not deleted.
- Search active memories by topic.
- Inspect the full history in a Streamlit interface.
- Keep data in a local SQLite file.

### Example

1. Save topic **job** with fact **I work as a mechanical engineer.**
2. Save topic **job** with fact **I now work as a GenAI engineer.**
3. Search for **job**: only the second fact is active.
4. Open history: both facts are visible, with their respective statuses.

**Limitation:** All facts sharing one exact topic are treated as replacements. That is an intentional baseline, not yet an intelligent memory engine.

## Quick start on Windows

Requirements: Python 3.11+ (the project owner is using Python 3.14), an internet connection for installing Streamlit, and approximately 16 GB RAM recommended for future local models. **Ollama is not required for Version 1.**

In Command Prompt, run from the cloned MemoryLab directory:

~~~bat
py -3.14 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python -m streamlit run app.py
~~~

If Python 3.14 isn't installed, replace 3.14 with your installed version. A browser should open at http://localhost:8501.

### Your existing local app and data

This GitHub repository does **not** automatically update the existing MemoryLab folder on your laptop. Clone it to a separate folder before switching. Your existing local file **memorylab.db** contains your test memories and is intentionally excluded from GitHub; keep a local backup if you want to preserve them.

## Research direction

**Question:** Can memory policies that account for outdated and harmful information improve downstream task accuracy over naive recency-based and semantic-search baselines?

**Planned comparisons:**
- Topic-based supersession (current baseline)
- Recency-based retention
- Semantic similarity retrieval
- Utility-aware retention, suppression, and update

**Planned measures:** answer accuracy, contradiction rate, harmful-memory retrieval, false forgetting, token and storage cost, and evaluation latency.

See [Research plan](docs/research_plan.md) for the hypotheses, dataset design, and experimental guardrails.

## Roadmap

- [x] **V1 — Persistent memory:** Streamlit + SQLite, topic-based updates, history
- [ ] **V2 — Semantic retrieval:** local embedding model through Ollama; requires local testing
- [ ] **V3 — Answer generation:** local LLM with retrieved evidence
- [ ] **V4 — Memory utility policy:** compare retention decisions experimentally
- [ ] **V5 — Research evaluation:** held-out benchmarks, ablations, error analysis, reproducibility

## Tech stack and budget

- Python, Streamlit, SQLite: free
- Planned local embeddings/LLMs with Ollama: free
- Optional paid evaluations: strictly capped at **£20 total per project**, with a £0 path for core experiments

No account credentials or paid inference are required for Version 1. Running locally avoids uploading personal memories to a hosted database.

## Privacy and repository hygiene

Local databases, virtual environments, API keys, model files, and temporary outputs are excluded by [.gitignore](.gitignore). Use **synthetic test facts**, not real private details, in screenshots, issues, and experiment datasets.

## Reproducibility notes

For future experiments, record model identifiers, quantization, dependencies, hardware, dataset seeds, inference settings, and evaluation scripts. Improvements must be validated on held-out cases; a successful demo is not itself evidence of research novelty or performance.
