# Experiment 011 — Post-adjudication re-score of frozen Experiment 010

**Evidence:** Owner-uploaded `review_v1_adjudicated_summary.json`, generated **15 November 2026 13:09:07 UTC**, and owner-uploaded `review_v1_results.json` from Experiment 010, generated **15 November 2026 11:33:29 UTC**. Both exports use the exact same dataset SHA-256 `c23de988a620b541c336517cbcda54094fc7e0a061a08bd51620e229c8fc2bd9`. The original predictions were reused; **Qwen was not rerun**, and the original first-review labels were not overwritten. This record does not commit any personal local JSON files.

## Human-review outcomes

- **20/20 cases have final labels.** The final summary shows **8/8 flagged cases adjudicated**, zero deferred, and 12 labelled `agreed_not_adjudicated`. The latter were carried forward because the first and second reviews agreed; they were **not** separately adjudicated.
- **First–second label agreement:** 18/20 = 90%, with two disagreements (B02 and B04). Descriptive Cohen's kappa computed from the first and second label marginals is approximately **0.8444**. This is a 20-case author-generated dataset; reviewer identity/independence is **not established by the file**, and these figures are not externally validated inter-rater reliability.
- **Two final relationship labels changed versus the first locked review:** B04 `coexists` → `duplicate`; B07 `uncertain` → `coexists` even though **both initial reviews selected `uncertain`**. The other 18 original labels remained.
- First-review source fingerprint: `fc2517ea15161c9b717d779a3514f355371cfde5a6fb80dd2de77bdce3c66f8b`; second-review fingerprint: `368d856efda85e13228e2a2f01e6587af6f96d8df52c9ee28db9a6c41f4ec560`; adjudication fingerprint: `825c36bb7aa4e1df9b61dd913b9206a2222d17b739919abb3695456e3aa719f9`.

## Same frozen model predictions, two label versions

| Metric | Raw Qwen vs first locked labels | Evidence gate vs first locked labels | Raw Qwen vs adjudicated labels | Evidence gate vs adjudicated labels |
|---|---:|---:|---:|---:|
| Agreement | 15/20 (75%) | 15/20 (75%) | **14/20 (70%)** | **13/20 (65%)** |
| False `replaces` suggestions | 5 | 0 | **5** | **0** |
| Genuine `replaces` recognised | 7/7 | 6/7 | **7/7** | **6/7** |
| Genuine updates not recognised | 0 | 1 | 0 | 1 |
| `uncertain` model recommendations | 0 | 6 | 0 | 6 |

Original single-pass Qwen produced the same predictions as Experiment 010. The guard post-processed those exact predictions. The results do **not** mean the guard made Qwen inherently more accurate: it reduced supersession recommendations while increasing abstentions and missed one reviewer-labelled update. Re-scoring cannot measure real memory retention or answer quality.

### Why overall agreement changed

- **B04:** OLD `I enjoy mystery novels.` versus NEW `Mystery novels are something I enjoy.` Both models returned `coexists`; adjudication corrected the initial `coexists` label to `duplicate`. Thus both models lose **one** match.
- **B07:** OLD cousin Iris in Brighton versus NEW `My cousin moved to Oxford.` The gate returned `uncertain`, matching the two initial reviewers. Adjudication selected `coexists`; consequently the gate loses **one more** match. Raw Qwen's `replaces` was wrong under both label versions.

## Remaining rubric/evidence concerns — do not silently correct labels

- **B07:** The final reason says `Might be different cousin`, but the stored axis `same_entity=yes` conflicts with that uncertainty. Coexistence is possible, but distinct identity has not been established. `uncertain` remains a defensible reading.
- **B10:** `The telescope is stored in cabinet three` versus `One of our devices was moved yesterday` is ambiguous about the moved object's identity. Final label `coexists` and axis `same_entity=yes` may be overstated; a fresh adjudicator should determine whether `unknown` is more appropriate.
- **B18:** The original names Nora, but the second statement says `One of our volunteers took a new position.` The final `same_entity=yes` is not evidenced. Keep the original decision for reproducibility, but flag for identity ambiguity.
- **B15:** The facts only state that the chess-club `meeting details have changed`, not which detail or any new meeting time. The adjudication marked `new_value_known=yes`, `old_fact_known_obsolete=yes`, and supersession. The current Tuesday meeting fact might or might not be invalidated; the exact changed attribute needs clarification before any real supersession.
- **B02:** The new fact says the dog's *collar* was replaced but does not provide its new colour. Final `new_value_known=yes` may conflate knowing an object changed with knowing its new attribute value.
- **B04, B08 and B12:** Final duplicate labels now have the storage action `skip_duplicate`. This is consistent with preserving a single active copy of equivalent information.

These are **semantic audit questions**, not evidence of file tampering or a licence to overwrite completed human judgements. The uploaded final summary does not contain the full second reviewer explanations, adjudicator identity, or an independent audit trail of human decision-making.

## Reproducibility

A new offline script `scripts/rescore_adjudicated.py` compares `results/raw/review_v1_results.json` to `results/raw/review_v1_adjudicated_summary.json`. It verifies that the dataset hashes, exact case IDs, and original first labels agree, and records separate initial and adjudicated scores without rerunning Ollama. It refuses mismatched files. Run:

```cmd
python -m scripts.rescore_adjudicated
```

It writes `results/raw/review_v1_adjudicated_metrics.json` and never touches SQLite. This is a convenience for checking the supplied results, not a new model experiment. Six mocked tests accompany the script; Windows execution still needs confirmation.

## Research decision

**Freeze Experiment 010 and 011 as separate analyses.** Do not automatically tune the guard to increase agreement with these revised, partly ambiguous labels. Develop a clear two-level relation and storage-action rubric, then obtain new independently labelled fictional profiles from separate reviewers, with explicit identity, time and updated-attribute evidence. Evaluating downstream answer accuracy and false forgetting remains necessary before claiming a generally safe memory policy.
