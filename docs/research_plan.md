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

### Stage 3 — Local grounded answer generation (local inference confirmed; grounding evaluation pending)

Version 3 retrieves up to three active memories using `all-minilm` cosine similarity and passes these as evidence to `qwen2.5:1.5b` through Ollama's `/api/chat` endpoint. The model is told to use only supplied facts and acknowledge missing evidence. This instruction alone does **not** guarantee grounding: test unsupported questions and manually compare answers to sources. Similarity filtering uses a user-adjustable heuristic, currently 0.25 by default, which is not statistically calibrated.

Keep retrieval errors separate from answer-generation errors; avoid claiming model output is correct because it sounds plausible.

### Stage 4 — Counterfactual utility measurement (phase 1 pilot tested manually; benchmark pending)

Version 4 phase 1 adds a **manual two-call comparison**: Qwen runs once with an empty memory list and once with one selected test memory. Both calls reach the model. The owner reported an appropriate abstention without a hobby memory (5.66s) and a correct photography response with the hobby memory (2.14s). See the Experiment 004 log. This is one positive control, not a learned policy, general accuracy estimate, or latency finding.

Next: create labelled synthetic scenarios, score both answers, repeat with shuffled conditions, and calculate per-memory utility with uncertainty. Only then develop a policy that learns from feedback and test interactions between memories.

### Stage 4B — Human-reviewed conflict classification (prototype, local testing pending)

A local Qwen model assesses **pairs** of facts in the *same exact topic* and suggests `replaces`, `coexists`, or `uncertain`. Suggestions do not write to the database. The user must select whether to supersede each prior fact (safe default: keep both). Updates are atomic and rejected if other same-topic memories changed since review. The earlier Section 1 save remains a topic-overwrite baseline. This is not automatic truth checking, cross-topic conflict detection, or an adaptive utility function. Log classification accuracy and human correction rates in later experiments.

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

## Qualitative experiment log — V3 negative control

**Source:** user-reported application response (not independently executed by the assistant).

- **Question:** "What city do I live in?"
- **Observed response:** "No memories met the similarity threshold. Try a clearer question, add a relevant memory, or lower the threshold."
- **Interpretation:** The retrieval threshold rejected all candidate memories; the application did **not** call Qwen in this run. This is a successful retrieval-stage abstention, not evidence that Qwen itself avoids unsupported claims.
- **Unknown/unrecorded:** exact database contents, selected similarity threshold, similarity values.
- **Follow-up test (user reported):** after changing the threshold to `0.00`, the app returned: "I don't have enough information in the saved memories to answer that." Given the current Version 3 code path, this indicates a Qwen response rather than a retrieval-stage rejection. It supports abstention on this one example, not general grounding reliability.
- **Unknown/unrecorded for follow-up:** exact retrieved memories, similarity scores, and full execution trace.

Keep this record separate from held-out benchmark results; it is a single manual smoke test, not a quantitative performance measurement.
