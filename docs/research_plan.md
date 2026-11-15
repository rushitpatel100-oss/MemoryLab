# MemoryLab research plan

## Motivation

AI assistants can store memories that later become outdated, contradictory, irrelevant, or misleading. More stored information can sometimes reduce the correctness of future answers. MemoryLab aims to study **when memory should be retrieved, revised, suppressed, or expired** rather than assuming every stored fact remains useful.

## Primary hypothesis

A policy informed by **measured downstream task utility** can reduce contradictions and improve task accuracy versus recency-only and semantic-similarity-only memory policies.

The hypothesis is **unverified**. Results may show no improvement; that would still be an informative research outcome.

## Experimental stages

### Stage 1 — Versioned storage baseline (current)

SQLite stores each memory's topic, text, timestamp, and active/superseded status. A new item in the same topic supersedes the earlier item. No generative AI or learned policy is involved.

### Stage 2 — Semantic retrieval (implemented; local smoke test passed)

Active memories and queries are encoded with Ollama's local `all-minilm` model and ranked using cosine similarity. The project owner successfully tested three paraphrased questions locally. Formal comparison to literal topic search and a labelled benchmark are **still pending**.

### Stage 3 — Local grounded answer generation (code implemented; local validation pending)

Version 3 retrieves up to three active memories using `all-minilm` cosine similarity and passes these as evidence to `qwen2.5:1.5b` through Ollama's `/api/chat` endpoint. The model is told to use only supplied facts and acknowledge missing evidence. This instruction alone does **not** guarantee grounding: test unsupported questions and manually compare answers to sources. Similarity filtering uses a user-adjustable heuristic, currently 0.25 by default, which is not statistically calibrated.

Keep retrieval errors separate from answer-generation errors; avoid claiming model output is correct because it sounds plausible.

### Stage 4 — Counterfactual utility measurement

For a set of benchmark questions, compare answers **with vs. without** individual candidate memories while holding evaluation conditions as constant as possible. Develop a retention and revision policy that can learn from feedback. Evaluate uncertainty and interactions between memories.

### Stage 5 — Rigorous evaluation

Create synthetic, consent-free user histories with controlled changes: preferences, occupations, dates, context-specific facts, and contradictions. Label the correct current answer and whether an old memory should remain available for historical questions.

Split benchmark identities and scenarios into development and held-out evaluation sets to avoid contamination. Report confidence intervals or repeated runs where generation randomness is involved.

## Baselines

1. Exact topic matching (current)
2. Recency-based retrieval or retention
3. Semantic similarity
4. Proposed utility-based policy

## Metrics

| Metric | Purpose |
|---|---|
| Answer accuracy | Whether the system gives the supported answer |
| Contradiction rate | Whether current facts conflict with verified updates |
| Retrieval precision / recall | How well relevant memories are selected |
| False forgetting | Whether genuinely useful historical context is suppressed |
| Tokens / latency / storage | Efficiency and computational trade-offs |

## Safety and privacy

- Use fictional user profiles and synthetic conversations in public artifacts.
- Never commit local SQLite databases or credentials.
- Retain an explicit memory history for auditability in the local prototype.
- Explicit user deletion requests must take priority over any learned memory utility score.

## Limits on claims

This project is a prototype, not a solved long-term memory architecture. Strong research claims require comparisons against published work and independent evaluation. Track failure cases, not just successful demonstrations.
