# MemoryLab Phase 6 — Blind human-label evaluation

## Why we are doing this

Experiments 007–009 revealed model classification errors. Phase 5 added a conservative gate to reduce risky replacement suggestions, but its development diagnostics reused examples already analysed while designing the gate. To make the next comparison more meaningful, this phase collects **human labels first** on new fictional cases.

## What is new

- `benchmarks/review_v1_cases.json` contains **20 fictional memory pairs with no expected labels**, case IDs B01–B20.
- `scripts/review_eval_cases.py` is a simple terminal review questionnaire. It does **not** run Qwen, access SQLite, or access the internet.
- Labels and short reasons are saved after every answer in `results/raw/review_v1_labels.json`, which Git ignores.
- Once all cases are labelled, `--lock` freezes the label file to the exact case-file SHA-256 fingerprint. A changed case file cannot silently reuse prior labels.
- `scripts/evaluate_review_v1.py` refuses to run before lock and compares **one Qwen result per pair** against its evidence-gated counterpart. Both conditions share exactly the same model prediction.

## Human reviewer rubric

Choose the best relationship from the old fact to the proposed new fact:

| Letter | Label | Interpretation |
|---|---|---|
| D | Duplicate | Same assertion, including clear paraphrases. |
| R | Replaces | Same identified entity, same specific attribute, with clear evidence the older value is outdated. |
| C | Coexists | Two different assertions that can both remain valid. |
| U | Uncertain | Not enough evidence that both facts refer to the same entity/attribute, or whether a vague change invalidates the earlier fact. |

**Avoid guessing.** For example, a statement about *one of our devices* does not necessarily refer to a specifically named telescope; that might justify `U`. A replacement with no stated new value may also be uncertain. Record *why* you chose each option. Label an item from the text provided, not imagined background facts.

## Run on Windows

1. Open the cloned MemoryLab project in GitHub Desktop and click **Fetch origin → Pull origin**. Activate your existing Python environment in VS Code.
2. Run the offline test suite:

   `python -m unittest discover -s tests -v`

   Expected: **62 tests** (prior 54 plus eight new mocked tests). These have not been locally verified yet.

3. Start with four fictional examples:

   `python -m scripts.review_eval_cases --limit 4`

   Answer using D/R/C/U and a brief reason. Type `S` to skip a case or `Q` to quit without losing saved progress.

4. Review the rest later, in as many sessions as you wish:

   `python -m scripts.review_eval_cases`

5. Check how many are complete:

   `python -m scripts.review_eval_cases --status`

6. When **20/20** are labelled, lock the answers:

   `python -m scripts.review_eval_cases --lock`

   The evaluator will not start without this step.

7. Now run the local comparison:

   `python -m scripts.evaluate_review_v1`

8. The script prints raw-versus-gated metrics and writes `results/raw/review_v1_results.json`. The model is called only once per pair. You may share that fictional output for research analysis, but do not upload personal data.

## What the metrics can and cannot tell us

The evaluator reports how often each method agrees with the **reviewer's own locked labels**, a confusion matrix for each method, the number of false replacement suggestions, how often real updates were not recognised, and the proportion of suggestions that became uncertain.

Fewer false replacement suggestions are desirable, but turning every decision into `uncertain` would sacrifice usefulness. Report both error types rather than relying on one headline agreement rate.

**Limitations:** The cases were authored within MemoryLab, the reviewer is not necessarily a trained annotator, and a single label is not verified ground truth. There are only 20 cases, no multiple raters, no randomised repeated run, and no externally sourced evaluation. It is a prospective blinded reviewer exercise, **not a rigorous independent held-out benchmark**. No model claims should be made before disagreements are adjudicated and new held-out studies are run.

No paid API, cloud AI inference or new packages are required. These scripts never modify the memory database.
