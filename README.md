# MemoryLab 🧠
### Local-first AI memory with human-controlled updates

MemoryLab is a Python, SQLite, Streamlit and Ollama portfolio project that explores a practical problem: **how should an assistant use useful remembered facts without losing other facts, confusing outdated information with current information, or inventing answers?**

**V1.0 status: local functional and clean-environment tests reported PASS; publication checks still open.** The project owner reported **295/295 offline tests passing**, correct selective memory history and safety controls, a correct answer to one supported fictional question, and abstention on one unsupported fictional question. These are local engineering and manual observations, **not independent model accuracy**. The owner also ran a fresh-clone, fresh-venv check and pasted six PASS lines (project layout, privacy excludes, UI guard, temporary storage, runtime, offline suite); the optional Ollama model-tag line was not included. A preliminary pattern scan of all 104 main-branch commit diffs found no common token-pattern matches, but comprehensive personal-data review remains open. An earlier failed UI walkthrough led to an extra demo-only overwrite safeguard; see [acceptance history](docs/v1_acceptance_status.md).

> **Important:** MemoryLab is an experimental research demonstrator, **not a production AI assistant or an automatic truth checker**. It uses local inference but can still generate unsupported answers.

## What it can do

- **Remember facts locally:** SQLite storage with active and superseded history.
- **Find related memories:** semantic search using the local Ollama `all-minilm` embedding model.
- **Answer from retrieved evidence:** local `qwen2.5:1.5b`, with the retrieved source memories visible for inspection.
- **Review memory conflicts:** AI-generated suggestions plus **explicit human Keep both / Supersede** decisions.
- **Protect updates:** transactional selective writes reject duplicates and stale reviews.
- **Explore failure modes:** separate reproducible research scripts and documented unsuccessful experiments.

The broad-topic replacement in Section 1 is a **research baseline**, not the recommended way to update facts. Use **Section 7: Smart Memory Review** for selective updates. In the isolated demo, bulk replacement of an existing topic is disabled.

## Try it on Windows (fictional data only)

Prerequisites: **Python 3.10+**, **Git/GitHub Desktop**, and **Ollama for Windows** from https://ollama.com/download. Commands below are for **Command Prompt (cmd)** inside the cloned project folder.

~~~bat
py -3 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
ollama pull all-minilm
ollama pull qwen2.5:1.5b
python -m scripts.v1_release_readiness --check-models
python -m scripts.launch_v1_demo
~~~

The demo uses a **disposable, isolated SQLite database**; stopping the launcher with **Ctrl+C** removes its temporary data. If Streamlit says the default port is occupied, rerun with an available port, for example `python -m scripts.launch_v1_demo --port 8505`. Verify the **ISOLATED DEMO MODE** banner.

For an ordinary persistent local database, run `python -m streamlit run app.py`. This uses the local `memorylab.db` file by default; **do not use personal memories for a public demonstration**.

[First-time Windows setup and troubleshooting](docs/windows_quickstart.md) · [Safe demo walkthrough](docs/v1_manual_acceptance.md)

## Architecture

~~~mermaid
flowchart LR
  U[Streamlit UI] --> S[(SQLite versioned memories)]
  U --> R[Semantic retrieval]
  R --> E[Ollama all-minilm embeddings]
  R --> A[Ollama Qwen local answers]
  U --> H[Human conflict review]
  H --> P[Transactional selective save]
  P --> S
  S --> R
~~~

All model calls in the core application are to **local Ollama**. MemoryLab does not need a paid cloud LLM service. Model weights and private SQLite files are **not** committed.

[Architecture and data boundaries](docs/architecture_v1.md)

## What the research actually found

| Development evaluation | Observation | Interpretation |
|---|---|---|
| Saved-answer keyword/abstention proxy (28 fictional questions) | Original mode 25/28 proxy matches; strict extractive mode 5/28 | Strict evidence extraction caused severe over-abstention, **not an accuracy improvement** |
| Lexical novelty probe (32 author-crafted candidate answers) | Flagged 10/22 single-reviewer-labelled unsupported answers; falsely flagged 3/9 supported answers | Missed stale values, wrong entities and many unsupported claims |
| Semantic support verifier (same 32 crafted answers) | Classified **all 32 as supported**, missing all 22 labelled unsupported | Failed as an approval filter; kept research-only |
| V1.0 local release readiness | Owner reported 295 tests passed and manual save/retrieval checks passed | Engineering and functional evidence, **not representative answer correctness** |

These are **small, exposed or deliberately curated development examples**. The 32 candidate answers were authored within this project, **not generated by Qwen**. None of these figures should be marketed as independent AI accuracy, learned memory-utility improvement or production readiness. A new externally curated holdout and multiple blind reviewers remain future research.

[Evaluation details and limitations](docs/v1_release_notes.md) · [Full research journal (historical)](docs/research_journal_archive.md)

## Portfolio demonstration

The demo shows how one fictional memory can be updated while preserving a different fact on the same topic, followed by evidence-aware question answering. A 3–5 minute [demo storyboard](docs/demo_storyboard.md) provides exact steps and narration for recording a recruiter-friendly walkthrough.

**Project stack:** Python · Streamlit · SQLite · Ollama · all-minilm · Qwen 2.5 1.5B · unittest

**Release position:** The repository is currently **private**. The V1.0 release candidate is documented, but **public visibility and a v1.0 tag are deliberately withheld** until clean-install and privacy/history review are complete. See [publication checklist](docs/publication_checklist.md).

## Project navigation

| Resource | Purpose |
|---|---|
| [Quickstart](docs/windows_quickstart.md) | First-time local setup and troubleshooting |
| [Architecture](docs/architecture_v1.md) | Components, data flow and safety boundaries |
| [Demo storyboard](docs/demo_storyboard.md) | 3–5 minute fictional scenario |
| [Acceptance status](docs/v1_acceptance_status.md) | What was tested and what failed previously |
| [Release notes](docs/v1_release_notes.md) | V1.0 scope, limitations and known issues |
| [Publication checklist](docs/publication_checklist.md) | Clean-install, privacy and release decisions |
| [Research journal archive](docs/research_journal_archive.md) | Original detailed experiments and historical procedures |
| [Research plan](docs/research_plan.md) | Unverified scientific hypothesis and future work |

**License:** [MIT](LICENSE) — Copyright © 2026 MemoryLab contributors. This license covers MemoryLab's original source and documentation; independently distributed Python packages and Ollama models retain their own terms.
