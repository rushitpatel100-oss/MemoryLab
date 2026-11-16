# Experiment 020 — Novelty probe misses wrong-but-familiar claims

**Date:** 16 November 2026. **Input:** owner-uploaded `phase13_probe_evaluation.md`. The original source data and locked reviewer decisions remain local, unmodified and Git-ignored.

## Source and provenance

- Project-authored 32-case fictional factual-support challenge; the candidate answers are NOT model-generated.
- Dataset SHA-256 (as reported): `aa6a1c7540e7c677df27b0a0b2b3585fa56fd509b60f66d9d19c85ed68daaac3`.
- Frozen single-reviewer signoff SHA-256 (as reported): `e962ae4895d91718291ee10fde87b9c20819dab0105fdfeef947a2e942f450f1`.
- Reviewer labels: 9 supported, 22 unsupported, 1 uncertain. Labels were frozen before the lexical probe was revealed. This protects against one kind of anchoring but does not make the cases independently authored, representative or externally adjudicated.

## Results against the frozen reviewed labels

| Classification outcome | Count |
|---|---:|
| Unsupported answer flagged (true positive) | **10** |
| Supported answer incorrectly flagged (false positive) | **3** |
| Supported answer not flagged (true negative) | **6** |
| Unsupported answer missed (false negative) | **12** |
| Reviewer uncertain, excluded | **1** |

- **Precision on these curated 31 decided cases:** 10 / (10 + 3) = **76.92%**.
- **Recall on these curated 22 unsupported cases:** 10 / (10 + 12) = **45.45%**.
- The screen produced 19 `no_obvious_lexical_novelty` statuses, eight `novel_terms_review`, three `unsupported_weekday` and two `unsupported_number`.

**Interpretation:** Twelve unsupported answers escaped detection and three supported answers were flagged. The detector is **not fit to auto-block or auto-approve responses**. These are descriptive performance figures on a deliberately constructed challenge, not independent model accuracy or generalizable product metrics.

## Failure analysis

### Valid paraphrases unnecessarily flagged (C05, C06, C08)

- **C05:** `west window` versus answer `western window` — a valid spatial paraphrase.
- **C06:** `drawing pencils` versus answer `pencils for sketching` — contextually equivalent.
- **C08:** question asks if mint tea is available; answer `Yes, the cafe serves mint tea` adds a conversational affirmation, not an invented fact.

### Stale values that were present in retrieved sources (C13–C16, C21)

An answer can repeat the old weekday (C13), old venue (C14), earlier opening time (C15), old object name (C16), or previous plant (C21) and contain **zero novel tokens**. A keyword's presence cannot establish that it is the **current** value.

### Cross-entity and cross-attribute confusion (C17–C20)

Wrong musical instrument, the home-jersey colour applied to the away jersey, a telescope's colour taken from a different location, and one person's pie preference assigned to another person all reuse real words. They fail because the correct **subject or attribute** is missing, not because a word is novel.

### Unknown or unproven claims using familiar words (C27–C29)

Unconfirmed poster colour (C27), an event host not selected (C28), and the weekday for a specifically named committee after an unspecified schedule change (C29) highlight missing evidence even when the answer's words occur in the question or some fact.

One other example, **C31**, received the single-reviewer `uncertain` label and is excluded from binary figures. Its status is not silently recoded.

## Research decision

1. **Preserve the lexical probe unchanged** as an optional diagnostic; it must not automatically suppress legitimate answers.
2. **Do not deploy the strict Phase 11 extractive mode**: on earlier data it avoided one fabricated day at the cost of 23 unnecessary abstentions.
3. Publish a **separate Phase 14 semantic verifier experiment**. It asks a locally run Qwen model to assess the *whole claim* against the exact question, referent, time and negation. It saves the raw model response, a structured verdict, evidence quote, validation issues and resume provenance. A citation/quote check is syntactic, **not proof of entailment**.
4. Compare the optional semantic verifier to the **same frozen Phase 13 labels**, explicitly counting deferrals/uncertainty rather than calling them correct detections. This is a further **exploratory diagnostic on already seen curated cases**, not a new holdout.
5. The later release-quality stage should use independently authored cases, blind **multiple** reviewers and fresh untouched examples of entity swaps, stale values, negation, justified abstention and paraphrases. Avoid post-hoc tuning on C01–C32 and then calling a rerun a validation.

## Implementation state

The new script is `scripts/evaluate_semantic_verifier.py` with 11 mocked/offline tests in `tests/test_evaluate_semantic_verifier.py`. It is separate from the live `app.py`, memory store and all previous AI review outputs. Local Qwen results are **pending**. See [Phase 14 protocol](phase14_protocol.md).
