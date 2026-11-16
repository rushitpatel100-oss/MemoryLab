# Experiment 013 — Phase 9 all-uncertain collapse and revised human signoff

**Status:** Analysis of two owner-uploaded files from 16 November 2026. No local Qwen run was performed here. Original Phase 8/9 outputs, signed decisions and SQLite memories remain unchanged. This is a **behavior diagnostic, not independently established model accuracy**.

## Input and provenance

1. `phase9_ai_comparison.md` — a local comparison report on 24 previously examined fictional cases. It reports the original Phase 8 AI file SHA-256 `38fa61accde6dccc3e8d988f4e142fbd504094a6618bcb50529c0d9ee631b983` and Phase 9 V3 AI file SHA-256 `b8046a99dbcadf596a59cf0ece551298c2e3d90a201de77b84c2a3a302d6d6cf`. The full **V3 AI JSON was not uploaded this turn**; this analysis cannot verify those bytes or its per-case evidence warnings.
2. `holdout_v2_human_signoff(1).json` — updated AI-first human-reviewed signoff, SHA-256 `da87c8aca0bcbbdeab0a5f351efeaf4de444fbe92857f4c4876051f6f362de06`. The signoff still refers to the original AI report hash, and `independently_human_labelled=false`. It contains **24 final decisions and 27 audit events**, including three later revisions to H02/H06/H20.

## Two degenerate AI reviewer versions

| Measure | Phase 8 direct AI reviewer | Phase 9 evidence-first reviewer |
|---|---:|---:|
| Cases | 24 | 24 |
| `replaces` | **24** | **0** |
| `uncertain` | 0 | **24** |
| `duplicate` | 0 | 0 |
| `coexists` | 0 | 0 |
| Marked `needs_review` | **24** | **24** |
| Changed labels compared to previous version | — | **24/24** |

**Interpretation:** The first AI workflow was systematically overconfident, while the revised reviewer now abstained on **every** example. It did not demonstrate improved four-way relation classification. The Phase 9 conservatism may prevent risky supersession, but can also make an automated reviewer unhelpful if every case still requires human intervention. This is not a clean performance comparison: the cases have already been exposed to the project, and a single reviewer's edited labels are not independent ground truth.

## The precise cause is still unverified

Phase 9's `interpret` function converts invalid/missing evidence to `unknown`, refuses unsupported evidence quotes, and can downgrade any relation to `uncertain`. The comparison Markdown includes **only final labels and triage flags**, not the five per-case axes or quote validation outcomes. Therefore it does **not** establish whether the all-`uncertain` result came from malformed JSON, failure of a small model to follow the structured prompt, invalid verbatim quotes, overly conservative decision rules, or several of these.

A new standalone **offline diagnostic** (`scripts/diagnose_phase9.py`) can inspect the already saved `results/raw/holdout_v2_ai_review_v3.json`, count the reasons for abstention, identify missing quote evidence and summarize all five evidence axes. It writes **`results/raw/phase9_failure_diagnostics.md`**, without rerunning the model or touching earlier experiments. Run:

```bat
python -m scripts.diagnose_phase9
```

The saved output only contains already-normalized axes and accepted evidence quotes. It does **not** preserve the raw Ollama response, so a failed or invented quote cannot always be distinguished from a strict matching issue. Do not change the policy or claim that a larger model fixed this until the failure reasons are observed.

## Updated human review: three corrections confirmed

| Case | Previous final label | Latest final label | Remaining consistency issue |
|---|---|---|---|
| H02 — dog Saffron's swimming | `replaces` | `duplicate` | The explanation was **not rewritten** and still argues an ownership distinction that does not exist in these two fact texts |
| H06 — office vs basement printer | `replaces` | `uncertain` | The explanation still says it is a clear replacement, and `same_entity=yes`/`old_fact_known_obsolete=yes` remain, even though office and basement printers may be different machines |
| H20 — home vs away jersey | `replaces` | `uncertain` | The explanation still says away jersey updates supersede the **home** jersey. They are different named attributes, so `coexists`, `same_attribute=no`, and keeping both are worth considering |

The *labels and storage actions* were updated, but the accompanying **text and evidence axes** were left untouched in all three. These are semantic review flags, not authorization to edit the user's saved decisions.

### Revised 24-case human signoff distribution

| Label | Count |
|---|---:|
| `replaces` | **10** |
| `coexists` | **6** |
| `duplicate` | **6** |
| `uncertain` | **2** |

The signed record has **19 decisions whose most recent action is `corrected` and 5 `individual` approvals**, zero bulk attestation; 27 total audit actions include the three later revisions. The human-review method remains AI-assisted rather than independently human-labelled. **14/24** final relationship labels differ from the original all-`replaces` AI proposal, but this is *reviewer disagreement*, not an accuracy score.

## Recommended next action

1. Diagnose V3 evidence failures using `python -m scripts.diagnose_phase9` and inspect/upload `results/raw/phase9_failure_diagnostics.md` or the underlying **`holdout_v2_ai_review_v3.json`**. Without one of those, the failure cause cannot be determined.
2. In `python -m streamlit run app_review.py`, revisit the explanations and evidence fields for H02, H06 and H20; preserve the audit log. A changed label with a stale 'replaces' explanation is **not internally review-ready**.
3. Keep Experiment 012 and the present Experiment 013 separately. If future evaluator/prompt changes follow these diagnostics, use *new fictional examples with independent human labels* for claims about classification reliability. No existing memory should be deleted or replaced from this diagnostic.
