# MemoryLab — 3–5 minute portfolio demonstration

**Use the disposable demo only.** Start with `python -m scripts.launch_v1_demo` and check the **ISOLATED DEMO MODE** banner. Never include real people, private memories, browser accounts or credentials in a recording.

## 0:00–0:30 — Problem and architecture

Suggested narration: “AI assistants can remember facts, but naïvely replacing everything under one topic loses useful information. MemoryLab uses SQLite versioned memory, local Ollama retrieval and Qwen answers, with selective human approval for memory updates.”

Show the [architecture diagram](architecture_v1.md) and briefly identify the local Streamlit interface.

## 0:30–1:45 — Keep a compatible fact

- Section 1: new topic `orchid-demo` and first fact **Orchid Center holds its workshop in Maple Room.**
- Section 7: new fact **Orchid Center provides a digital projector.**
- Review the earlier memory and choose **Keep both**, regardless of any unreliable automatic suggestion.
- Section 2: demonstrate both memories are active.

Narration: “Two independent attributes should coexist even under the same topic.”

## 1:45–2:45 — Selectively supersede only the outdated fact

- Section 7: propose **Orchid Center moved its workshop from Maple Room to Cedar Room.**
- Mark the Maple Room fact **Supersede old memory** with all three accurate confirmation boxes; retain the digital-projector fact with **Keep both**.
- Section 3: display inactive Maple Room history, active projector and active Cedar Room update.
- Demonstrate a duplicate attempt being blocked. Do not intentionally perform destructive saves.

Narration: “Old information remains auditable, and a new location need not erase an unrelated projector fact.”

## 2:45–3:30 — Evidence-based answering and limits

- Ask **Where does Orchid Center hold its workshop now?** and inspect the retrieved memory evidence for **Cedar Room**. The model's precise wording can vary.
- Ask **What is the entrance ticket price for Orchid Center?**; no saved fact gives this answer. Record what the model actually says. A single abstention is **not proof it always abstains**.

Narration: “The answers come from a locally hosted small language model. It is experimental: unsupported answers remain possible, so the evidence is visible and no automated semantic verifier is treated as a trusted truth gate.”

## 3:30–4:30 — Research lesson and results

Show the README results table. Briefly discuss:
- Original versus strict extraction: the strict mode abstained too often.
- Lexical screen missed 12/22 deliberately curated unsupported answers.
- The semantic verification experiment accepted all 32 crafted answers, including all 22 labelled unsupported.
- The project retained these negative results instead of advertising misleading accuracy.

Finish: “This is a working, local-first research demonstrator with human-controlled memory updates, an honest evaluation record, and clear next research steps.”

## Recording checklist

- Record only a disposable database and synthetic data.
- Show the demo banner and the three memory states.
- Keep the video under five minutes; crop out personal tabs and desktop identifiers.
- If a model answer is incorrect, **disclose it** rather than editing the result to look accurate.
- Link the finished video from the README **only after it exists**; do not add a broken or placeholder link.
