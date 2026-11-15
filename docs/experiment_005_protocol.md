# Experiment 005 — When memory does not help

Use only fictional test facts. Section 6 (**Memory Impact Lab**) asks the same question twice: with no evidence, and with one selected memory. It calls Qwen in both cases.

## Part A — Irrelevant memory

1. Save topic **snack**, fact **My favourite snack is apple slices.**
2. Select the snack memory in section 6.
3. Ask **What city do I currently live in?**
4. No city has been provided: **both responses should abstain**. If a city is invented, mark that as unsupported.

This probes whether irrelevant evidence causes Qwen to invent a fact.

## Part B — Stale memory

Assume a fictional person's **actual current city is York**. This ground truth is defined outside MemoryLab.

1. Save topic **location**, fact **I currently live in Bristol.** This is deliberately incorrect relative to ground truth.
2. Select that memory and ask **Which city do I currently live in?**
3. If Qwen answers Bristol, it used the memory but gave an answer **wrong relative to ground truth**. This is a memory-quality failure, not necessarily an LLM instruction failure.
4. Save a new memory under the same topic: **I now live in York.**
5. Select the updated location memory and ask the same question again. A York answer is correct. Bristol should appear only as *Superseded* in history.

## Record each observation

| Field | What to capture |
|---|---|
| Scenario | Irrelevant / stale / corrected |
| Fictional ground truth | "Not supplied" or York |
| Selected memory | Exact fact and topic |
| Without-memory answer | Copy verbatim |
| With-memory answer | Copy verbatim |
| Supported by input evidence? | Yes / no / abstained |
| Correct relative to ground truth? | Yes / no / not answerable |
| Time | Optional; descriptive only |

**Important:** The pilot cannot yet estimate a memory's average utility. For that we will need a frozen synthetic dataset, repeat runs, shuffled condition order, a scoring rubric, and held-out profiles. Do not commit personal memory exports or private data.
