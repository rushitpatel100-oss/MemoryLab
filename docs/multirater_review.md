# MemoryLab Phase 7 — Second-reviewer agreement and adjudication

## Research objective

Experiment 010 reduced false replacement suggestions against its locked reviewer labels (5 to 0) but left 15/20 overall label agreement unchanged. Cases like B04 and B15 showed that **human labels can be ambiguous too**. This phase measures human agreement and explicitly records reasons for resolving or deferring disagreements before making more policy changes.

**No second reviewer is yet involved.** The code permits a new human reviewer, but cannot verify that a different person used it. If the owner enters both reviews, call it a repeat review, *not* independent inter-annotator agreement.

## First step: a genuinely separate second human reviewer

The person should not read `results/raw/review_v1_labels.json`, `review_v1_results.json`, Experiment 010, or another reviewer's explanations before finishing their independent labels. The `review_second` tool itself loads only the public **unlabelled** dataset and the second reviewer's own local file.

Start from the up-to-date MemoryLab repo in an activated Windows Python terminal:

~~~bat
python -m unittest discover -s tests -v
~~~

Expected after Phase 7 plus the correction utility: **83 offline unit tests** (63 prior + 20 new or updated review tests). These simulate reviewer inputs; they do not confirm a real person has reviewed anything.

To start with just four cases:

~~~bat
python -m scripts.review_second --limit 4
~~~

For each fictional old/new fact, choose:

| Field | Input | Meaning |
|---|---|---|
| Main relation | D / R / C / U | Duplicate / Replaces / Coexists / Uncertain |
| Explanation | Free text | Short, specific reasoning, required |
| Same entity? | Y / N / U | Are both claims about the same person, object or event? |
| Same attribute? | Y / N / U | Do they address exactly the same property? |
| Old fact obsolete? | Y / N / U | Is the original fact demonstrated to be outdated? |
| New value known? | Y / N / U | Does the new claim give a replacement value? |
| Storage action | K / S / R / D | Keep both / Supersede old / Needs review / Skip duplicate |

Please use **U** for unknown rather than inventing information. The structured fields deliberately do not automatically determine the main relationship; differences make potential rubric disagreements visible.

The second reviewer can stop and resume:

~~~bat
python -m scripts.review_second
python -m scripts.review_second --status
~~~

After **20/20** cases are complete, they lock their labels:

~~~bat
python -m scripts.review_second --lock
~~~

Second-review labels are saved to `results/raw/review_v1_second_labels.json`. The original `review_v1_labels.json` remains untouched. A hash catches accidental later edits but is not a tamper-proof audit log.

## Compare the two locked reviews

**Only after both humans have locked their labels**, run:

~~~bat
python -m scripts.compare_human_reviews
~~~

The program refuses unlocked or incomplete reviews and writes `results/raw/review_v1_disagreements.json`. It calculates:

- **Exact label agreement:** number of cases where both humans selected the same relationship.
- **Cohen's kappa:** marginal-adjusted descriptive agreement (can be undefined with constant labels; small, imbalanced samples have unstable estimates).
- **Disagreement queue:** every pair with a conflicting label, plus a pre-registered set of potentially ambiguous cases B02, B04, B07, B10, B12, B15, B18, even if the raters agree. The tool also flags **internal conflicts** between the second reviewer's recorded evidence, relationship label, and suggested storage action; this is a prompt for human review, not a truth judgement.

This tool never calls Qwen, edits memories or overwrites either review. It shows both original rationales and the second reviewer's four evidence judgements **only after locking**.

## Human adjudication, not automatic relabelling

Run after the comparison:

~~~bat
python -m scripts.adjudicate_reviews --limit 4
~~~

Each flagged case shows its fictional facts and the two human reviews. The adjudicator can choose D/R/C/U with fresh reasons, evidence dimensions and a storage recommendation, or choose **X (defer)** when the text remains insufficient.

Resume, inspect status and lock when the queue is complete:

~~~bat
python -m scripts.adjudicate_reviews
python -m scripts.adjudicate_reviews --status
python -m scripts.adjudicate_reviews --lock
~~~

Outputs: `results/raw/review_v1_adjudication.json` (the individual decisions) and `results/raw/review_v1_adjudicated_summary.json` (all 20 case IDs, final labelled or deferred status, alongside both original labels). The original review files are never overwritten. Unflagged agreeing cases are marked **agreed_not_adjudicated**, not declared expert-verified truth.

### Correcting an unlocked adjudication

If you realise a saved answer conflicts with its justification or storage action, you can correct it **before locking**:

~~~bat
python -m scripts.adjudicate_reviews --status
python -m scripts.adjudicate_reviews --edit B04
~~~

The edit command displays the existing answer and asks all questions again for **that case only**. Earlier answers are retained in `revision_history` within the local adjudication JSON. Nothing is altered without your input. Once locked, the tool refuses revisions. The status command warns about contradictory storage recommendations, and `--lock` refuses to finalize cases such as a fact labelled **Duplicate** with an action of **Supersede old memory**. An automated check cannot catch all reasoning contradictions; review the written explanations too.

**Important:** The adjudicator sees both human labels and so this stage is **not blind**. A separate adjudicator is preferable, but these tools do not enforce independent identities. Adjudicated outcomes should be reported as post-hoc corrections, never substituted silently into Experiment 010's original 15/20 baseline.

## Limits and next milestone

This is still only 20 project-authored fictional examples. Reviewer disagreement may reveal vague rubrics; agreement may conceal systematic shared errors. Two reviewers and an adjudicator improve label quality but do not prove general-purpose reliability. Next, create new fictional profiles with case-level referent and temporal annotations, freeze a new dataset, use multiple raters, and evaluate downstream false forgetting or incorrect answers rather than classifier labels alone.

All work is local, uses existing free tools, and never modifies `memorylab.db`.

## Completed Phase 7 output — Experiment 011

The owner supplied a locked adjudication summary of the 20 fictional cases. **Eight flagged cases were adjudicated; 12 agreeing cases were carried forward without case-by-case adjudication.** Two final labels changed: B04 and B07. First/second agreement was 18/20, but the source does not establish two independent people. Re-scoring the existing model predictions against final labels yielded **14/20 raw** and **13/20 gated**, with **5 versus 0 false supersession suggestions**. Some final evidence axes remain contested; see [Experiment 011](experiment_011_results.md). Use `python -m scripts.rescore_adjudicated` for offline reproduction of these numbers, without model calls.
