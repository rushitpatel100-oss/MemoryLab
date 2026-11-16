# MemoryLab research plan

## Motivation

AI assistants can store memories that later become outdated, contradictory, irrelevant, or misleading. More stored information can sometimes reduce the correctness of future answers. MemoryLab aims to study **when memory should be retrieved, revised, suppressed, or expired** rather than assuming every stored fact remains useful.

## Primary hypothesis

A policy informed by **measured downstream task utility** can reduce contradictions and improve task accuracy versus recency-only and semantic-similarity-only memory policies.

The hypothesis is **unverified**. Results may show no improvement; that would still be an informative research outcome.

## Experimental stages

### Stage 1 — Versioned storage baseline (current)

SQLite stores each memory's topic, text, timestamp, and active/superseded status. A new item in the same topic supersedes the earlier item. No generative AI or learned policy is involved.

### Stage 2 — Semantic retrieval (implemented; local smoke test passed)

Active memories and queries are encoded with Ollama's local `all-minilm` model and ranked using cosine similarity. The project owner successfully tested three paraphrased questions locally. Formal comparison to literal topic search and a labelled benchmark are **still pending**.

### Stage 3 — Local grounded answer generation (local inference confirmed; grounding evaluation pending)

Version 3 retrieves up to three active memories using `all-minilm` cosine similarity and passes these as evidence to `qwen2.5:1.5b` through Ollama's `/api/chat` endpoint. The model is told to use only supplied facts and acknowledge missing evidence. This instruction alone does **not** guarantee grounding: test unsupported questions and manually compare answers to sources. Similarity filtering uses a user-adjustable heuristic, currently 0.25 by default, which is not statistically calibrated.

Keep retrieval errors separate from answer-generation errors; avoid claiming model output is correct because it sounds plausible.

### Stage 4 — Counterfactual utility measurement (phase 1 pilot tested manually; benchmark pending)

Version 4 phase 1 adds a **manual two-call comparison**: Qwen runs once with an empty memory list and once with one selected test memory. Both calls reach the model. The owner reported an appropriate abstention without a hobby memory (5.66s) and a correct photography response with the hobby memory (2.14s). See the Experiment 004 log. This is one positive control, not a learned policy, general accuracy estimate, or latency finding.

Next: create labelled synthetic scenarios, score both answers, repeat with shuffled conditions, and calculate per-memory utility with uncertainty. Only then develop a policy that learns from feedback and test interactions between memories.

### Stage 4B — Human-reviewed conflict classification (prototype, local testing pending)

A local Qwen model assesses **pairs** of facts in the *same exact topic* and suggests `duplicate`, `replaces`, `coexists`, or `uncertain`. A conservative deterministic normalisation check first catches identical same-topic facts without a model call, and SQLite rejects a duplicate write inside the transaction. Suggestions do not write to the database. The user must select whether to supersede each prior fact (safe default: keep both). Updates are atomic and rejected if other same-topic memories changed since review. The earlier Section 1 save remains a topic-overwrite baseline. This is not automatic truth checking, cross-topic conflict detection, or an adaptive utility function. A 16-case author-labelled synthetic development set is provided for initial failure analysis, but it is too small, non-held-out, and potentially ambiguous for general performance claims. Log classification errors and human corrections, then create independent held-out scenarios.

### Stage 4C — Two-stage memory relation analysis (published, local test pending)

The single-pass four-way Qwen classifier matched 10/16 author-assigned development labels in Experiment 007; it incorrectly called two independent-fact pairs `replaces`. The new experimental alternative first asks whether facts concern **independent properties**, the **same property**, or whether identity/attribute alignment is **unclear**. Independent facts route to `coexists`, unclear alignment routes to `uncertain`; only same-attribute facts proceed to another Qwen call that evaluates duplicate/update/compatibility/incompleteness. Exact normalised repeats still use the local rule. Both approaches retain **human approval**, the same SQLite storage implementation, and the same Qwen model. There is no trained memory utility score.

A separate 16-case synthetic comparison candidate is provided; it is newly authored after seeing prior failures, but not independently adjudicated. Score **both methods on identical cases**, including erroneous supersession suggestions, label agreement and inference time. Do not modify prompts to match the comparison cases before recording results. An independent held-out benchmark remains necessary.

### Stage 4D — Conservative replacement-evidence gate (published, local tests pending)

Experiment 009 found that a two-stage Qwen pipeline introduced more false replacement recommendations on the author-labelled examples. The new optional safety-gated single-pass method retains the existing model call and checks for a narrow old-value-to-new-value transition in the text. A model `replaces` prediction with no such transition is displayed as `uncertain`, with the raw prediction and gate reason recorded. The text check does not verify referent identity, attribute identity, or the truth of a claim. Human supersession now requires confirming those facts individually.

A conservative rule can miss real updates that are not phrased as `from X to Y`. Evaluate its false replacement reduction **and** genuine replacement coverage. The current comparison set has already been used during feature design; genuine held-out validation will require new independent synthetic examples and agreed labels.

### Stage 4E — Blind, label-first evaluation candidate (first local experiment completed)

Twenty new fictional fact pairs are provided **without expected relation labels**. Before any new model evaluation, an independent human reader of the examples can assign a four-way label and explanation through a resumable local CLI. The program locks complete labels to the case-file SHA-256 fingerprint, and the evaluation runner refuses to run until all labels are locked. It compares one baseline Qwen prediction and the gate's post-processing of that same output, recording false replacements and missed real updates separately.

This workflow reduces answer-contamination from seeing model predictions first, but the cases were still authored within the project; one reviewer does **not** constitute expert-adjudicated ground truth. **Experiment 010** matched 15/20 reviewer labels for both raw and guarded classifiers; false replacement suggestions fell from 5 to 0, but genuine replacements recognised fell from 7 to 6. Some labels are contestable (especially B04 and B15), so neither overall agreement nor gate safety is fully validated. Preserve the original labels, independently adjudicate disputed cases, then evaluate on new held-out subjects with multiple raters. See [Experiment 010](experiment_010_results.md).

### Stage 4F — Multi-reviewer agreement and label adjudication (published, second reviewer pending)

To avoid treating a single person's disputed labels as unquestionable ground truth, Phase 7 offers a separate **second human review** of the 20 fictional pairs. The new reviewer must not inspect the first person's locked labels or previous Qwen outputs before completing their own decisions. Alongside the original four relationship labels they separately record same-entity, same-attribute, old-obsolete, and new-value-known judgments, plus a recommended storage action.

After **both reviews are locked**, a tool reports raw inter-rater agreement, Cohen's kappa, disagreements, and seven pre-registered semantically challenging cases. Another human-facing adjudication workflow records revised labels or deferrals **without overwriting either original vote or Experiment 010**. If the same person completes both reviews, the result is not independent inter-rater reliability. A shared error can also survive unanimous agreement. Even two reviewers on 20 authored cases are insufficient to prove a universally safe memory policy.

**Experiment 011:** the adjudication summary reports 18/20 first–second label agreement and changes two final labels (B04, B07). Against the frozen predictions, raw Qwen matches 14/20 and the gate matches 13/20, while false `replaces` suggestions remain 5 versus 0. Reviewer independence cannot be established from the files and several `same_entity`/`new_value_known` axes remain contestable. Keep the original first-review results and post-hoc scoring separate. Only after a sharper rubric should the project design and freeze a new multi-identity held-out corpus. See [Phase 7 guide](multirater_review.md) and [Experiment 011](experiment_011_results.md).

### Stage 4G — Phase 8 evidence-first rubric + fresh blind review candidate (published, results pending)

After Experiment 011 showed disputed label interpretations on the previous 20 examples, freeze [rubric v2](label_rubric_v2.md) and a **new set of 24 author-generated fictional cases without labels** (`benchmarks/holdout_v2_cases.json`). A and B must fill the specific entity/attribute/old-obsolete/new-value evidence fields **before** choosing a relationship label or storage action. Inconsistent recommendations are rejected by an offline consistency check. Cases are kept in distinct locally ignored files with independent locks; A/B reviewer identity cannot be authenticated by code.

Only after both are locked, evaluate the existing Qwen and unchanged evidence gate on the same one-call outputs. Score **consensus cases only** and report the disagreement count, false replacement suggestions, missed genuine updates and rate of abstention. Do not tune the gate based on these cases and then describe the same results as held-out; the cases were constructed within the research project and require external revalidation.

No existing data, prompts, model parameters or SQLite storage behaviour is modified in this phase. See [Phase 8 protocol](phase8_protocol.md).

### Stage 4H — Local automatic triage (published, evaluation pending)

To reduce the user's manual annotation burden, MemoryLab now provides a **separate** Ollama-based automatic draft reviewer for the 24 fictional cases. It returns four rubric evidence fields, a provisional relation and an explanation, with warnings about contradictory or destructive proposals. It saves only `results/raw/holdout_v2_ai_review.json` and never touches human A/B labels, SQLite, or the accuracy-evaluation script. Qwen judging Qwen is circular; **no model-accuracy claim is permitted from auto-triage alone**. A different local judge may produce useful error-analysis contrast but still does not replace independent human ground truth. See [automatic review guide](auto_review.md).

### Stage 4I — AI-first human verification and provenance (published, local testing pending)

To minimise manual annotation, a Streamlit dashboard now displays all 24 local AI draft evaluations, enables explicit bulk attestation of unflagged entries, individual approval or edits for flagged and disputed cases, and produces a versioned Markdown report. The approval history distinguishes AI-generated draft labels, human edits, individually checked entries and bulk-attested entries. **This is AI-assisted human verification, not independently human-labelled evidence**, even when the natural-language prose sounds human. No SQLite writes, no revision to the frozen Qwen classifier, and no automatic unlocking of the human-consensus scorer occur. See [human-verification method](human_verification.md).

### Stage 4J — Experiment 012: AI-first verification run (completed, semantic QA outstanding)

The owner supplied the 24-case automatic Qwen review, the full Markdown report, and signoff JSON with 24 matching audit actions. The AI judge suggested `replaces` and `supersede_old` for **all 24 pairs**, but the reviewer gate held **all 24** at `review_needed`; the reviewer changed **11 relation labels**, edited **18** records total and individually approved **6** unchanged. Final reviewer distribution was 13 `replaces`, 6 `coexists`, 5 `duplicate`, 0 `uncertain`. Ten AI responses had missing/invalid structured evidence warnings.

Targeted semantic inspection uncovered questionable final signoffs—especially H02 (dog swimming paraphrase labelled replacement), H06 (office and basement printers treated as identical) and H20 (home and away jerseys treated as the same attribute). These are **review flags**, not edits to the user's signed decisions. Natural prose and formal label/action agreement do not imply factual correctness. **No independent accuracy metrics** are available from these AI-first cases; they are now exposed to model output and cannot be reused as a fresh blind test of the same judge.

See [Experiment 012 results](experiment_012_results.md). Next phase should test semantic relation QA and structured output quality, then evaluate on **new independent** examples and downstream memory-answer correctness.

### Stage 4K — Phase 9 evidence-first reviewer (published; local results pending)

A dedicated experimental reviewer now collects **five structured axes** (`same_entity`, `same_attribute`, `same_assertion`, `old_fact_known_obsolete`, `new_value_known`) and verbatim evidence quotes with a JSON-schema Ollama request. A separate deterministic rule maps this evidence to `duplicate`, `replaces`, `coexists`, or `uncertain`. Missing quotes, contradictory role qualifiers and indefinite referents prevent confident replacement. Proposed replacement actions always remain review-only. It writes a **new** `holdout_v2_ai_review_v3.json` file rather than touching the original Phase 8 drafts or signoffs.

A diagnostic comparison tool produces counts and case-wise label changes against the historical AI drafts, with source fingerprints. **This is not a blind benchmark**: the 24 cases were already analyzed during Experiment 012. Until new independent labels exist, report changes in AI behavior, schema validity and abstentions—not accuracy improvements. The old Qwen classifier, Phase 5 gate, SQLite and historical reports are unchanged. See [Phase 9 protocol](phase9_protocol.md).

### Stage 4L — Experiment 013: Phase 9 all-uncertain diagnostic (results reported)

The owner-uploaded comparison shows **24/24 Phase 9 AI outputs were `uncertain`**, while Phase 8's same 24 cases were **24/24 `replaces`**. Both flagged 24/24 for review. The full V3 evidence JSON was not provided, so the cause of abstention is not established; a new offline `scripts/diagnose_phase9.py` will count missing quotes, unknown axes and per-case warnings without rerunning Ollama. A separately uploaded revised signoff contains 24 decisions/27 audit actions, with H02, H06, H20 relationship labels changed but their original explanations and some evidence axes not yet reconciled. See [Experiment 013](experiment_013_results.md). Do not equate the conservative abstention policy with four-way accuracy or independent evaluation.

### Stage 4M — Experiment 014: valid quotes, all-unknown evidence, V4 (local run pending)

The owner-uploaded V3 evidence diagnostic showed **0 missing old/new quotes** across 24 cases, but all **five evidence questions were answered `unknown` in all cases** (120/120), with no malformed-field warnings. This identifies broad semantic abstention in the saved evidence, though the exact causal mechanism cannot be verified without raw V3 model messages. The new versioned V4 contrastive judge reduces the unnecessary unknown options on binary/observable axes, preserves raw model text and maps explicitly supported evidence to a tentative relation, never an automatic memory write. Comparing V3 vs V4 on these exposed 24 cases is **diagnostic only** and not model accuracy. See [Experiment 014](experiment_014_results.md).

### Stage 4N — Experiment 015: V4 false-duplicate suppression (safety audit published)

The uploaded V3–V4 diagnostic shows seven V4 `duplicate` proposals, of which H18 (rosemary explicitly replaced with lavender) and H20 (home versus away jersey facts) are **unflagged, visibly wrong duplicates**. This exposed-case evaluation is a qualitative failure demonstration, not a blind model-accuracy score. Runtime V4 can recommend `skip_duplicate` for every structurally acceptable duplicate. The new **offline `scripts/audit_review_v4.py`** flags general change-language and role-qualifier conflicts and converts all duplicate skips to nonbinding `review_needed` audit recommendations pending human confirmation. Neither source JSON nor SQLite is modified. Further accuracy research requires fresh, independent labelled scenarios and downstream false-forgetting tests. See [Experiment 015](experiment_015_results.md).

### Stage 4O — Experiment 016: shared cautions in Smart Memory Review

A supplied offline V4 safety audit reported **two high-priority false-duplicate warnings (H18/H20), five other duplicates requiring confirmation, seven out of seven proposed skips withheld, and 17 unresolved**. The audit makes no data changes. We extracted general change-word and role-contrast caution signals into `memory_review_safety.py` and surfaced these risks beside duplicate/replacement suggestions in the live `app.py` Smart Memory Review interface, keeping all existing human approvals and atomic DB protections. This is a **human-facing warning, not a trained or proven semantic classifier**. No independent accuracy or downstream-memory benefit is established; next test needs new blinded fictional scenarios. See [Experiment 016](experiment_016_results.md).

### Stage 5 — Rigorous evaluation

Create synthetic, consent-free user histories with controlled changes: preferences, occupations, dates, context-specific facts, and contradictions. Label the correct current answer and whether an old memory should remain available for historical questions.

Split benchmark identities and scenarios into development and held-out evaluation sets to avoid contamination. Report confidence intervals or repeated runs where generation randomness is involved.

## Baselines

1. Exact topic matching (current)
2. Recency-based retrieval or retention
3. Semantic similarity
4. Proposed utility-based policy

## Metrics

| Metric | Purpose |
|---|---|
| Answer accuracy | Whether the system gives the supported answer |
| Contradiction rate | Whether current facts conflict with verified updates |
| Retrieval precision / recall | How well relevant memories are selected |
| False forgetting | Whether genuinely useful historical context is suppressed |
| Tokens / latency / storage | Efficiency and computational trade-offs |

## Safety and privacy

- Use fictional user profiles and synthetic conversations in public artifacts.
- Never commit local SQLite databases or credentials.
- Retain an explicit memory history for auditability in the local prototype.
- Explicit user deletion requests must take priority over any learned memory utility score.

## Limits on claims

This project is a prototype, not a solved long-term memory architecture. Strong research claims require comparisons against published work and independent evaluation. Track failure cases, not just successful demonstrations.

## Qualitative experiment log — V3 negative control

**Source:** user-reported application response (not independently executed by the assistant).

- **Question:** "What city do I live in?"
- **Observed response:** "No memories met the similarity threshold. Try a clearer question, add a relevant memory, or lower the threshold."
- **Interpretation:** The retrieval threshold rejected all candidate memories; the application did **not** call Qwen in this run. This is a successful retrieval-stage abstention, not evidence that Qwen itself avoids unsupported claims.
- **Unknown/unrecorded:** exact database contents, selected similarity threshold, similarity values.
- **Follow-up test (user reported):** after changing the threshold to `0.00`, the app returned: "I don't have enough information in the saved memories to answer that." Given the current Version 3 code path, this indicates a Qwen response rather than a retrieval-stage rejection. It supports abstention on this one example, not general grounding reliability.
- **Unknown/unrecorded for follow-up:** exact retrieved memories, similarity scores, and full execution trace.

Keep this record separate from held-out benchmark results; it is a single manual smoke test, not a quantitative performance measurement.
