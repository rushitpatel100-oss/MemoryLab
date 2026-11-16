# Experiment 015 — V4 duplicate-suppression risk audit

**Date:** 16 November 2026. **Source:** owner-uploaded `phase9_v4_diagnostic.md`, generated from earlier local AI drafts on 24 fictional, previously exposed cases. Its reported SHA-256 for the V3 AI JSON is `b8046a99dbcadf596a59cf0ece551298c2e3d90a201de77b84c2a3a302d6d6cf` and for the V4 AI JSON is `a9e1a1089493444a8c288197be1639a205171023d842e3c3dc86157d57636c52`. **The V4 source JSON was not uploaded in this turn; its warning details and raw model messages cannot yet be inspected directly.**

## Observed version-level results

| Metric | V3 evidence-first | V4 contrastive |
|---|---:|---:|
| Cases | 24 | 24 |
| `duplicate` | 0 | **7** |
| `replaces` | 0 | 0 |
| `coexists` | 0 | 0 |
| `uncertain` | **24** | **17** |
| Marked `needs_review` | **24** | **17** |
| `same_entity=unknown` | 24 | 13 |
| `same_attribute=unknown` | 24 | 17 |
| `same_assertion=unknown` | 24 | 0 |
| `old_fact_known_obsolete=unknown` | 24 | 0 |
| `new_value_known=unknown` | 24 | 0 |
| V4 raw model response saved | — | 24 |

Changing the prompt reduced generic uncertainty and produced **seven unflagged duplicate proposals**. That is improved *coverage*, not demonstrated accuracy: five duplicates appear to be sensible paraphrases, while two are clear errors by inspection of the authored fact pairs.

## Critical false-duplicate proposals

| ID | Old memory | New memory | V4 decision | Why dangerous |
|---|---|---|---|---|
| **H18** | `My balcony planter contains rosemary.` | `I replaced the rosemary in my balcony planter with lavender.` | `duplicate`, unflagged | This is an explicit **replacement**. Skipping it would preserve the obsolete rosemary memory instead of noting lavender. |
| **H20** | `The cycling team's home jersey is navy.` | `The away jersey was changed from navy to grey.` | `duplicate`, unflagged | The statements describe **home versus away jerseys**. They can coexist; skipping the new away-jersey fact loses distinct information. |

Five other V4 `duplicate` cases—H02, H07, H14, H19 and H23—are consistent with paraphrases when judged from the actual fictional fact text, but that is a *targeted project-internal semantic review*, not independent human-labelled accuracy. **H12** is also a straightforward bus-commute paraphrase yet V4 classified it `uncertain`. Straightforward explicit updates such as H03, H08, H10, H15, H21 and H22 also remain `uncertain`, illustrating unnecessary abstention.

## Safety implication

V4's internal draft policy maps any `duplicate` to `safe_storage_action=skip_duplicate` with `triage=draft` if no structural warnings occur. That is **not a real storage write**, but it can be dangerous if later consumed automatically: the wrong duplicate decision could cause a genuine update to be ignored. It therefore needs a safety audit distinct from the AI's own flags.

## Implementation: non-destructive automatic audit

A separate offline tool `scripts/audit_review_v4.py` performs **generic change-word and role-qualifier checks** against saved V4 drafts. It does **not** hardcode H18 or H20 IDs into its runtime logic. It distinguishes:

- **High priority:** duplicates where the new statement contains change/cessation language, contrasting role qualifiers such as home/away, invalid evidence quotes or contradictory evidence axes.
- **Confirm duplicate:** other duplicate proposals still require explicit human approval before a memory can be skipped, even with no heuristic warning.
- **Unresolved:** `uncertain` outputs remain for human inspection. Any `replaces` proposal also requires approval.

The audit converts *all* AI duplicate skips to a **separate non-binding `audit_action=review_needed` recommendation** in its output; it never changes V4's saved JSON or any active memory. False-positive warnings and false-negative omissions remain possible.

Run after pulling from GitHub Desktop:

```bat
python -m unittest discover -s tests -v
python -m scripts.audit_review_v4
```

Expected suite **169 tests** (161 before this change, eight new). Windows execution is not yet verified. The report is saved to `results/raw/phase9_v4_safety_audit.md` and refuses to overwrite an existing output; no Ollama calls occur.

## Research restrictions and next steps

Do not claim that V4 achieves 5/7 duplicate accuracy: this set has been repeatedly discussed and the examples were authored within the project. The valid claim is **two demonstrably risky unflagged duplicate proposals among seven on the exposed case set**, based on a direct inspection of the supplied facts. This finding motivates regression tests and human approval before suppression.

Before further prompt iterations, collect a **new, independent, blind-labelled fictional evaluation set** and separate three outcomes: duplicate skipping, superseding a known obsolete memory, and preserving additional compatible information. The experiment should measure the practical impact of false skipping and false supersession on downstream answer quality, not only output labels.

**Integrity:** The uploaded comparison Markdown, earlier AI files, previous human signoffs, all old Experiment 010–014 records, and live SQLite database were not overwritten or committed.

## Audit verification and UI integration — Experiment 016

The owner uploaded the completed safety audit: **2 high-priority**, **5 additional duplicate confirmations**, **all 7 duplicate skips withheld**, and **17 unresolved cases**. New shared caution functions are also displayed in the actual Smart Memory Review Streamlit UI, without changing classifier predictions or allowing automatic memory suppression. See [Experiment 016](experiment_016_results.md). These figures remain project-internal diagnostics.
