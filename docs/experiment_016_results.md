# Experiment 016 — V4 safety audit verified; warnings surfaced in Smart Memory Review

**Date:** 16 November 2026. **Evidence:** owner's `phase9_v4_safety_audit.md` export, SHA-256 `35ee4520210aa5fb952dede1cf16d1833a746e74bf9680637a60f73d4cef3abc`. The Markdown reports input V4 AI JSON SHA-256 `a9e1a1089493444a8c288197be1639a205171023d842e3c3dc86157d57636c52`. **The input V4 JSON was not uploaded in this turn, so its per-case raw model responses were not independently inspected here.**

## Audit report counts

| Recorded audit outcome | Cases |
|---|---:|
| Total fictional pairs | **24** |
| High-priority duplicate warnings | **2** (H18, H20) |
| Other duplicate suggestions needing confirmation | **5** (H02, H07, H14, H19, H23) |
| **All AI-proposed duplicate skips held for confirmation** | **7/7** |
| Unresolved `uncertain` cases | **17** |
| AI replacement recommendations to approve | **0** |

**H18:** `My balcony planter contains rosemary` / `I replaced the rosemary in my balcony planter with lavender`. The V4 model said `duplicate`; the audit spotted explicit change language and requested review. The new claim indicates a replacement, not a repeated fact.

**H20:** `The cycling team's home jersey is navy` / `The away jersey was changed from navy to grey`. The V4 model said `duplicate`; the audit spotted both change language and the *home versus away* contrast and requested review. These are distinct jersey facts, so treating the second as an exact duplicate would omit information.

Five other duplicate proposals were placed in an explicit-confirmation group rather than automatically accepted. The report made **no SQLite writes** and left 17 ambiguous cases unresolved. The observation '2/2 known dangerous duplicates caught' is a narrow qualitative test on **previously exposed, project-authored examples**, not a measured general detection rate or an externally validated model-accuracy result.

## Product integration: reusable cautions

A new pure-Python `memory_review_safety.py` contains small **general-purpose warning functions** for a possible duplicate (change/cessation wording and contrasting role/location qualifiers), and for a possible replacement (contrasting qualifiers and indefinite referents such as `one of`). These checks have no model calls or database access and are intentionally conservative: warnings can be false positives, and the absence of a warning never proves a statement is a duplicate.

`scripts/audit_review_v4.py` now reuses these functions rather than duplicating its lexical heuristics. The existing **`app.py` Smart Memory Review screen** also displays an explicit 'Potential FALSE DUPLICATE' warning alongside a Qwen duplicate recommendation when these signals appear. Unflagged non-exact paraphrase suggestions also ask the user to check before deciding not to save; replacement suggestions with uncertain referents show additional caution. The application continues to require manual review of supersession selections and retains the transactional exact-duplicate checks in `memory_store.py`. **No new automatic suppression or deletion action was introduced.**

The product UI is a separate live review screen from the offline V4 case audit. This change does **not** claim the live app is now using V4 as its classifier; it reuses generic caution rules to help users assess whichever of the existing classifiers is selected.

## Verification and limitations

Eight additional mock/offline regression tests in `tests/test_memory_review_safety.py` check update and attribute-contrast warnings, human-confirmation requirements, and known false positives. Expected total suite: **177 tests** (169 before this change, 8 added). Source files and test methods were committed to GitHub; the tests and Streamlit UI have **not** been executed on the user's Windows environment in this session.

To run after GitHub Desktop Fetch origin → Pull origin:

```bat
python -m unittest discover -s tests -v
python -m streamlit run app.py
```

In Smart Memory Review, check a **fictional** rosemary-to-lavender update or home/away jersey pair under the same topic. A Qwen duplicate suggestion should display stronger caution; even if Qwen makes another prediction, its human review process remains in place. Do not use personal or sensitive memories for initial verification.

## What to do next

Stop repeatedly adjusting prompt wording against H01–H24: all 24 examples have been used to design and debug safeguards, and they are not a new blind test set. Create a **new fictional, independent, pre-labelled evaluation set** (with human verification clearly attributed if AI drafts are used), freeze the rubric and storage-action acceptance criteria, then test whether erroneous duplicate skipping or supersession affects *later memory answers*. None of the uploaded private JSON, old experiments, or SQLite memories has been committed or changed.
