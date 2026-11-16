# MemoryLab V1.0 — Architecture and trust boundaries

## Core components

~~~mermaid
flowchart TD
    UI[Streamlit application] --> DB[(Local SQLite memorylab.db)]
    UI --> SEARCH[Active-memory search]
    DB --> SEARCH
    SEARCH --> EMB[all-minilm embeddings via local Ollama]
    EMB --> SEARCH
    SEARCH --> GEN[Qwen 2.5 1.5B via local Ollama]
    GEN --> UI
    UI --> REVIEW[Smart Memory Review]
    REVIEW --> SUGGEST[Qwen suggestion + deterministic risk cues]
    SUGGEST --> HUMAN{Human chooses action}
    HUMAN -->|Keep or supersede| TX[Transactional memory_store.py]
    TX --> DB

    DEMO[Disposable demo launcher] -. "MEMORYLAB_DB_PATH override" .-> UI
    EXP[Research-only verifiers and benchmarks] -. "not a live gate" .-> GEN
~~~

## Stored memory and revisions

Each SQLite record stores a topic, factual text, creation timestamp and whether it is active. Original history remains accessible when a prior record is superseded. The normal Section 1 research baseline deactivates **all existing active facts of the same topic** when a new one is saved; this is intentionally a comparison baseline, not a sophisticated conflict policy.

Section 7 offers **selective human-reviewed supersession**. The reviewer sees candidate conflicts, chooses **Keep both** or **Supersede old memory** per existing record, and confirms the referent/attribute/time when superseding. The transactional store rejects duplicate facts and stale reviews of records that changed since inspection.

## Retrieval and answering

1. The app searches active facts in SQLite and computes local embeddings through `all-minilm`.
2. It ranks similar memories using cosine similarity and selects evidence for the question.
3. `qwen2.5:1.5b` returns a candidate response; the app shows retrieved source records for inspection.
4. The similarity threshold is a **heuristic**, not calibrated truth confidence. A cited or retrieved fact does not guarantee that a generated answer is entailed by that fact.

## Privacy boundaries

- Main application: `memorylab.db` on the owner's computer by default. Never committed intentionally.
- Demo launcher: forces `MEMORYLAB_DB_PATH` to a temporary SQLite file and sets `MEMORYLAB_DEMO_MODE=1`; test data are removed on launcher exit.
- Demo overwrite safety: when an existing topic has active facts, **Section 1 bulk replacement is disabled** both in the UI and inside a SQLite transaction; new-topic first saves still work.
- App-model calls: Ollama running on the same computer. No required cloud inference provider.
- Research scripts: use fictional benchmarks and Git-ignored `results/raw/` files. The optional novelty and semantic verifiers do not approve/reject live user answers.

## What this is not

This version has **no trained utility-based memory policy**, independent entailment guarantee, independent model-performance benchmark, production access-control system or multi-user hosted storage. The core contribution is a reproducible local **memory update-and-evidence investigation with explicit human approval**.
