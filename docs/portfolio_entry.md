# MemoryLab — Portfolio description

## Short resume bullet

Built **MemoryLab**, a local-first AI memory research application using Python, Streamlit, SQLite and Ollama; implemented semantic retrieval, evidence-visible Qwen answers, and human-controlled memory updates with transactional duplicate and stale-review safeguards, supported by 295 owner-reported passing unit tests and documented failure analysis.

## Project overview for a portfolio page

**MemoryLab — Adaptive Memory Research Demonstrator**

I designed and implemented a local-first experimental memory system to investigate how AI assistants should preserve, retrieve and revise remembered facts. The application combines a versioned SQLite store, semantic search with `all-minilm` embeddings, and a locally hosted Qwen model for question answering. A Smart Memory Review interface recommends relationships between existing and proposed facts, but the user decides which facts to keep or supersede; storage transactions reject duplicates and stale updates.

The accompanying reproducible experiments document important limitations as well as working features. In a curated factual-support challenge, lightweight lexical screening missed many wrong-but-familiar claims, while a semantic verifier accepted all proposed answers—including those a single reviewer marked unsupported. Those unsuccessful approaches remain research-only rather than being presented as verified safety gates.

**Technologies:** Python, SQLite, Streamlit, Ollama, Qwen 2.5, all-minilm, GitHub, unittest.

**Validation:** 295 local unit tests reported passing; a subsequent fictional-data manual walkthrough reported successful selective updates, retrieval and an unsupported-question abstention. These checks do **not** establish independent model accuracy.

## Recruiter demo summary

A three-to-five-minute screen recording can show a fictional venue moving from Maple Room to Cedar Room while an unrelated projector fact stays active, followed by evidence-based question answering and the limits of small-LLM verification.

Use [the storyboard](demo_storyboard.md) to produce the video. Do not claim that a recording exists until it has actually been produced.
