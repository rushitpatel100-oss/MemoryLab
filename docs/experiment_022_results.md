# Experiment 022 — V1.0 engineering gate passed; manual UI acceptance pending

**Date:** 16 November 2026. Owner-uploaded source: `v1_release_readiness_001.md`, SHA-256 `a206dff625c8dc75f879f786d61967051ebac38db018f201649cb374108de31a`.

## Observed automated results

| Check | Result |
|---|---|
| Project file layout | PASS |
| Configured privacy ignore patterns | PASS |
| Guarded bulk-topic baseline save UI | PASS |
| Transactional selective SQLite save, duplicate and stale-review rollback | PASS |
| Python 3.14.5 and Streamlit present | PASS |
| Offline unit tests | **PASS — 276/276** |
| Local Qwen and all-minilm Ollama model tags | PASS |

**All seven engineering checks passed in the uploaded report.** This establishes those tests ran successfully in the user's local environment; it does not verify model answer correctness, manual UI interactions, or independently sourced evaluation.

## Changes committed after this green report

- The ordinary Streamlit app can now optionally read `MEMORYLAB_DB_PATH` while retaining `memorylab.db` as its normal default. Both baseline and Smart Memory Review writes use that selected path.
- `python -m scripts.launch_v1_demo` sets a temporary private SQLite path and an obvious demo banner, keeping fictional UI tests separate from existing memories. The demo folder is removed when its launcher stops.
- `python -m scripts.record_v1_manual_qa` asks the user for observed UI outcomes and saves a numbered local Markdown report. Seven functional checks are separate from one unsupported-answer observation.
- Six launcher tests and seven manual-report tests bring the **expected new suite to 289 tests**. They have not been executed on the owner's machine yet.

**Preservation:** The uploaded readiness report, earlier evaluation outputs, frozen reviewer decisions and existing personal SQLite database remain unchanged. No v1.0 release tag has been created.

## Next

After GitHub Desktop Fetch origin → Pull origin:

```bat
python -m scripts.v1_release_readiness --check-models
python -m scripts.launch_v1_demo
```

Use [the fictional manual acceptance guide](v1_manual_acceptance.md). Stop the demo with Ctrl+C, then run:

```bat
python -m scripts.record_v1_manual_qa
```

Upload the numbered `results/raw/v1_manual_acceptance_001.md` for triage. Even a passed manual walkthrough does not prove Qwen never hallucinates or replace the separate privacy and clean-install release gates.
