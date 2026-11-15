# Experiment 004 — Memory impact pilot

**Status:** Completed manual positive control (user-reported results; the assistant did not execute Ollama).

## Conditions

- Question: "What hobby do I enjoy?" (as specified in the pilot; exact execution input not independently captured)
- Selected synthetic memory: "My favourite hobby is photography."
- Model: local Qwen through MemoryLab's answer generator, configured by default as qwen2.5:1.5b
- Both conditions call Qwen, with zero and one selected memories respectively
- Synthetic ground truth: photography

## Results

| Condition | Reported response | Time | Interpretation |
|---|---|---:|---|
| Without memory | "I don't have enough information in the saved memories to answer that." | 5.66s | Appropriate abstention |
| With memory | "Based on the memory record provided, your hobby is photography." | 2.14s | Answer supported by the fictional memory |

## Interpretation and limitations

This example demonstrates a desirable change in answerability when a relevant memory is supplied. It does **not** establish a general accuracy improvement, a learned memory utility policy, or a latency advantage. Sequential timings are influenced by warm-up, load, and order effects. The actual on-device memory records, model revision, and raw trace were not independently inspected.

## Next experiment

Test an irrelevant memory and a deliberately stale memory with ground truth defined **outside** the database. See Experiment 005 protocol. Record results separately from any eventual held-out benchmark.
