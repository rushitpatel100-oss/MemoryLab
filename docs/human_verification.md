# MemoryLab — AI-first, human-verified review (Phase 8 optional workflow)

## The fastest honest review process

MemoryLab can make the **first draft of every review automatically** and show you one consolidated report. You only need to correct the mistakes and explicitly approve the rest. This is a human-in-the-loop review, not blind independent annotation.

Update MemoryLab via **GitHub Desktop → Fetch origin → Pull origin**. In your existing Python environment run:

~~~bat
python -m unittest discover -s tests -v
python -m scripts.auto_review_holdout_v2
python -m streamlit run app_review.py
~~~

The expected suite size is **122 tests** (115 previous, 7 new signoff tests); those tests have not been run on your Windows laptop yet.

1. The first command runs offline tests, then the local `qwen2.5:1.5b` judge automatically drafts all 24 fictional cases. No manual labelling and no paid API.
2. The Streamlit dashboard opens in your browser and shows a full table of facts, AI relationship labels, explanations, safety flags and approval status.
3. Read the unflagged results and, if you actually checked them, tick the attestation checkbox and press **Approve all remaining unflagged cases**. This is recorded as *bulk_attested* rather than individual human annotation.
4. Select each flagged case, read the old/new facts and AI's reasons, edit the relationship, explanation, four evidence axes and storage recommendation if necessary. Press **Save and approve this case**. Existing signoffs can be revisited and changes are logged.
5. When all 24 cases are approved, download the final Markdown report or save a versioned report locally. An audit JSON is saved automatically after every approval.

## Local files

- `results/raw/holdout_v2_ai_review.json`: original **AI-generated** draft; never overwritten by the dashboard.
- `results/raw/holdout_v2_human_signoff.json`: actual human approval/correction actions and previous versions.
- `results/raw/holdout_v2_human_reviewed_<revision>.md`: human-reviewed **AI-assisted** report, generated when all cases are approved.

All three are already covered by `results/raw/` in `.gitignore` and do not expose any personal memory database. Reports contain the supplied fictional case texts. Neither the AI reviewer nor the dashboard modifies memory records.

## Natural-language explanations and model choice

The initial judge generates a short explanation in ordinary language. You can edit any reason directly in the dashboard, so it reads naturally while staying factually tied to the two original statements.

The default judge is your existing `qwen2.5:1.5b` and requires no download. A separate, larger local judge may produce different or more polished wording, but its accuracy has **not** been established for this task. If you want to experiment with an alternative before you run the automated review for the first time, Ollama provides models such as `qwen3:4b-instruct` or `gemma3:4b`. A different model is still not an independent human reviewer and consumes more disk/memory. The automatic review tool deliberately refuses to switch models within an existing output file.

## What you can accurately claim

- **Good:** 'We used local AI to create draft memory-conflict annotations, then performed human verification and recorded corrections and approvals.'
- **Good:** 'Human-corrected AI suggestions; source attribution and per-case review provenance retained.'
- **Incorrect:** 'All 24 examples were independently human-labelled' if the human saw the AI answer first.
- **Incorrect:** '100% human review accuracy' solely because the final report was approved.

Bulk attestation shows the reviewer accepted all listed unflagged entries after reading the report. It does not prove each was separately evaluated, and the report explicitly counts bulk approvals versus individual approvals and edits.

For rigorous model **accuracy** or safety claims, you still need independent blinded human-labelled cases that are distinct from the model's own output. The previous two-reviewer protocol remains available but is not required to use the AI-first development workflow.

## If the model stops

The automatic judge saves after each successful case. Re-run `python -m scripts.auto_review_holdout_v2` to continue missing cases. The Streamlit dashboard waits for a complete 24-case AI file before allowing human signoff. If the model output changes after human signoff starts, the dashboard refuses to silently reuse the old approvals for new AI content.

## Completed owner review — Experiment 012

The owner's three submitted local exports showed **24/24 signoffs**, 6 individual approvals, 18 edited responses, zero bulk approvals, and 11 changed relationship labels. The same Qwen judge proposed `replaces` in **every case**, so this is a useful failure analysis rather than a validated scoring benchmark. The reviewer gate held **all** suggestions for human review. Some final labels and evidence axes remain contestable (H02, H06, H20 and others); review the [Experiment 012 analysis](experiment_012_results.md) before using them as training labels or permitting any memory supersession. Original submitted files are not modified or committed.
