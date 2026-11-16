# MemoryLab automatic AI review — quick start

## One command, no manual 24-case questionnaire

After updating the repository in GitHub Desktop (**Fetch origin → Pull origin**) and activating your current MemoryLab Python environment, run:

~~~bat
python -m scripts.auto_review_holdout_v2
~~~

The program uses your already installed **local Ollama `qwen2.5:1.5b`** and the exact 24 new fictional cases in `benchmarks/holdout_v2_cases.json`. It judges each old/new pair using the Phase 8 rubric, and saves a draft relationship, four evidence dimensions, explanation and recommended storage action.

Outputs appear in **`results/raw/holdout_v2_ai_review.json`**, which is excluded from Git. The script saves after every completed case. If it stops due to Ollama being offline, run the **same command** to resume. You may try the first four with `--limit 4`, then continue without `--limit`. To see counts and flagged IDs without making calls:

~~~bat
python -m scripts.auto_review_holdout_v2 --status
~~~

**What the output means:** `provisional_label` is a *machine suggestion*. `triage=needs_review` indicates missing evidence, an AI contradiction, an uncertain relation, or proposed memory supersession. `safe_storage_action=review_needed` prevents interpreting those cases as permission to remove memory. None of these fields changes `memorylab.db`.

## Why this is separate from Reviewer A and B

Phase 8's strict evaluator was designed to measure prediction agreement against locked human labels. The auto-reviewer produces **AI draft labels in a separate filename**, not reviewer A or B entries. It never calls or unlocks the human-label evaluator. A model reviewing its own predictions risks self-confirmation and must not be advertised as independent validation. An alternative installed Ollama judge model can be used through `--model MODEL_NAME` **before an initial run**, but a different model still is not a trained, independent human reviewer.

The script records the judge model and the dataset fingerprint and refuses to mix data from a changed model or dataset. It never overwrites your existing human review progress or earlier 20-case Experiment 010/011 outputs. It does not require additional paid APIs, models or Python dependencies in the default configuration.

## Local testing and troubleshooting

Run the unit suite first:

~~~bat
python -m unittest discover -s tests -v
~~~

Expected **115 tests** after this automation feature (105 prior + 10 new mocked tests). Tests don't require a running model and haven't yet been executed on the user's Windows system.

If you see a connection error, ensure Ollama is running, then re-run the same command. If you see a model-not-found error, ensure `qwen2.5:1.5b` is available in your existing Ollama installation. If a model returned malformed JSON, it is recorded conservatively as an uncertain, flagged AI draft instead of a confident memory update.

## How to use the findings responsibly

Use AI triage for: spotting ambiguous fact pairs, checking whether the explanation mentions the correct person/attribute, finding overconfident supersessions, or preparing a small human-review shortlist. **Do not compute an accuracy score** by comparing this Qwen judgement to the same Qwen classifier. A real claim about memory accuracy still needs separate human labels, ideally a new externally authored scenario sample and downstream memory-answer testing.

## Optional human-verification dashboard

After the automatic judge has completed all 24 cases, run `python -m streamlit run app_review.py`. This dashboard presents the AI draft report and allows you to correct or approve entries. It distinguishes per-case edits, individual approvals and bulk attestations and exports a clearly attributed Markdown report. **AI-generated and human-approved is not independent blind human labelling.** See [the human verification guide](human_verification.md).
