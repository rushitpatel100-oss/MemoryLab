# MemoryLab V1.0 — Isolated manual acceptance walkthrough

**Run only with fictional facts.** This checks the real Streamlit app without touching the normal `memorylab.db` file. It is NOT an accuracy test of the LLM.

## Open a new disposable demo

After GitHub Desktop **Fetch origin → Pull origin**, open a terminal in MemoryLab and run:

```bat
python -m scripts.v1_release_readiness --check-models
python -m scripts.launch_v1_demo
```

Confirm that Streamlit displays **ISOLATED DEMO MODE**. The launcher sets a temporary SQLite database for *both* research-baseline and Smart Memory Review saving. When you press Ctrl+C in the terminal, this demo database is removed. The updated offline test suite should contain **289** tests; the latest 13 tests still need local verification.

## Three fictional memories

Use the identical topic **`orchid-demo`** for each entry.

- **A (original):** `Orchid Center holds its workshop in Maple Room.`
- **B (compatible):** `Orchid Center provides a digital projector.`
- **C (update):** `Orchid Center moved its workshop from Maple Room to Cedar Room.`

## Eight checks to perform in order

1. **UI01 — First memory:** In Section 1, save A under `orchid-demo`. Search Section 2 and confirm it is active. This is a new, empty demo database, so no earlier memory is overwritten.
2. **UI02 — Coexistence:** In Section 7, **Smart Memory Review**, propose B with the same topic. Choose **Keep both** for A, then **Save reviewed memory**. Verify both A and B remain active. Do not blindly follow the model's classifier recommendation.
3. **UI03 — Selective supersession:** In Section 7, propose C. Choose **Supersede old memory** for A and tick the three identity, attribute and obsolescence confirmations. Choose **Keep both** for B. Save, then confirm active B and C. The old room A should be inactive.
4. **UI04 — Duplicate:** Propose fact B again in Section 7. The app should block an exact duplicate and should not create another saved record.
5. **UI05 — Baseline warning:** In Section 1, propose `Orchid Center has a front desk.` under `orchid-demo`. Verify a strong warning says every existing active fact in this topic would be superseded. Without checking the acknowledgement box, the baseline save button must remain disabled. **Do not perform this bulk overwrite**.
6. **UI06 — History:** In Section 3, show all memories. A should be superseded/inactive; B and C should remain active; no extra B record should exist.
7. **UI07 — Semantic search and supported answer:** In Sections 4 and 5, ask `Where does Orchid Center hold its workshop now?` and inspect the retrieved facts. Expected relevant evidence: C, **Cedar Room**. If retrieval or Qwen fails to use it, record a FAIL and the actual response.
8. **UI08 — Unsupported-answer observation:** In Section 5 ask `What is the entrance ticket price for Orchid Center?` The saved facts provide no price. Record whether Qwen abstains or invents one, with the exact response. This is an observation, **not a passing accuracy certification**.

## Save your observations

When finished, stop the Streamlit launcher with **Ctrl+C**. Then run:

```bat
python -m scripts.record_v1_manual_qa
```

Enter **pass**, **fail**, or **not_tested** for UI01–UI07, based on what you saw. For UI08, use **observed**, **fail**, or **not_tested** with a brief note describing the actual Qwen output. Failure and observation notes are required; do not guess outcomes for checks that did not run.

The script writes a numbered Git-ignored report, such as `results/raw/v1_manual_acceptance_001.md`. **Upload that report next.** If any readiness test failed on the updated code, upload the newest `v1_release_readiness_XXX.md` too.

## Safety and research integrity

- The normal Streamlit command still uses the real local memory file by default; use the isolated launcher for this walkthrough.
- Keep screenshots and reports free of real personal data, passwords and private memory contents.
- The human approval UI controls supersession; Qwen proposals can be wrong.
- A passed manual product check does not establish independently verified fact accuracy or production readiness.
- Do not create a V1.0 Git tag until manual acceptance, clean install and privacy inspection have been completed.
