# Version 4, Phase 1 — Memory Impact Pilot

This is the first controlled *comparison* feature in MemoryLab. It does **not** yet learn a retention policy or prove a memory improved accuracy.

## Research question

For the same question and local Qwen model, how does supplying one selected memory change the answer?

## Beginner walkthrough

1. Start the cloned MemoryLab app: `python -m streamlit run app.py`.
2. Add a **fictional** memory under topic `hobby`: `My favourite hobby is photography.`
3. Scroll to **6. Memory Impact Lab**.
4. Select this memory.
5. Enter `What hobby do I enjoy?` and click **Run with/without-memory experiment**.
6. Compare the results:
   - **Without memory:** Qwen receives `[]` as its evidence. It should acknowledge missing information.
   - **With memory:** Qwen receives the selected record. A supported answer should mention photography.
7. Use the evidence record to check support. Don't assume a different or longer answer is a better answer.

## What is held constant?

- One question
- The same local Qwen model (`qwen2.5:1.5b`)
- The same system prompt and settings (`temperature=0`, context length, response limit)

**Changed variable:** evidence list is empty versus one selected memory.

Both conditions send an actual request to Ollama. In the normal Version 3 UI, no eligible memories result in no model call; this pilot deliberately does something different.

## Important caveats

- The two model calls run sequentially; background system load and warm-up can influence timings.
- Temperature zero reduces randomness but does not guarantee perfectly identical outputs across platforms/runs.
- The current UI lets a person choose the memory, so this is **not** an unbiased retrieval or retention comparison.
- There is no automatic correctness metric yet. Judge each answer against the synthetic ground truth.
- The pilot only compares **one** memory. Useful interactions between memories cannot be assessed yet.
- A successful individual case cannot establish an original research finding.

## User-reported Version 3 negative controls

With a city question and no relevant memory:
1. At the default similarity threshold, retrieval rejected all candidates and Qwen was not invoked.
2. At threshold `0.00`, Qwen answered, "I don't have enough information in the saved memories to answer that."

The observations are manual and do not establish a general hallucination rate.

## Next research milestone

Create a fixed dataset of synthetic histories and labelled questions, run repeated trials with and without memories, score answer correctness and abstention, and estimate how often a memory helps or hurts. Hold out entire user profiles/scenarios before evaluating a learned utility policy.
