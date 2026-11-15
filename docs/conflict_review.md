# V4 Phase 2 — Smart Memory Review

This prototype asks local Qwen to **suggest** a relationship between an old and new memory. It does not know the real world, cannot verify truth, and never automatically removes an old memory.

## Update test

1. In section 1, save a fictional memory:
   - topic: location
   - fact: I currently live in Bristol.
2. In section 7, type topic **location**, fact **I have moved from Bristol to York.**
3. Click **Review possible conflicts**.
4. Examine Qwen's suggestion. We expect **replaces**, but a 1.5B model might be wrong. Select **Supersede old memory** manually.
5. Click **Save reviewed memory**.
6. In section 3, check that Bristol is **Superseded** and York is **Active**.

## Coexistence test

1. Keep the new York memory active.
2. In section 7, use topic **location**, fact **I work in London.**
3. Click **Review possible conflicts**.
4. We expect **coexists** because someone can live in York and work in London. Keep **Keep both** selected.
5. Save, then inspect history: both York and London facts should be **Active**.

## Design constraints

- Comparisons are limited to the **exact same topic**, not every memory in the database.
- If more than 10 active facts share a topic, the pilot declines to proceed rather than silently skipping entries.
- The model's relation and reason are **unverified suggestions**, not authoritative truth labels.
- The previous add-memory control in **section 1** remains a simplistic baseline that supersedes all older facts with that topic. To keep coexistence facts, use **section 7** for subsequent entries.
- Even a valid JSON output from Qwen can be semantically wrong. Always check the facts before approving supersession.
- Version 4 is not yet a learned policy. Evaluation needs labelled synthetic cases, baselines, and held-out measurements.
- The same SQLite table is used; no migrations and no new packages required.

## Helpful tests

Run all offline unit tests in your virtual environment:

~~~bat
python -m unittest discover -s tests -v
~~~

Run the app:

~~~bat
python -m streamlit run app.py
~~~

Use only fictional or consented data in demonstrations. Local database files remain excluded from GitHub.

## First local Qwen classification observation (owner-reported)

The project owner tested section 7 with topic `test_location`:

- **Old active fact (M6):** "I currently live in Bristol."
- **Proposed new fact:** "I have moved from Bristol to York."
- **Qwen returned:** `replaces`
- **Qwen's explanation:** "The new statement updates the location from Bristol to York."
- **Manual assessment:** The relationship label and explanation are appropriate for a stated change of residence.
- **Storage validation (owner-reported):** After approving the change, the project owner confirmed that Bristol appears **Superseded** and York appears **Active** in Memory History. This verifies the intended status transition in one local manual test.

This is one qualitative classification and storage observation, **not** a measured classification accuracy rate or broad proof of database reliability. Next, test the contrasting coexistence case (living in York while working in London).

## Second local Qwen classification observation (owner-reported)

The project owner tested section 7 with the active York residence memory:

- **Old active fact (M7):** "I have moved from Bristol to York."
- **Proposed new fact:** "I work in London."
- **Qwen label:** `uncertain`.
- **Qwen reason:** "The old statement indicates a change in location, while the new statement indicates a change in occupation. These are unrelated facts."
- **Expected label:** `coexists`, since residing in York and working in London can both be true.
- **Interpretation:** The explanation recognises independent statements, but the relation label is overly cautious. This is one incorrect classification relative to the synthetic expected label. It is **not** a confirmed database-write failure; the default `Keep both` prevents unintended supersession.
- **Database outcome (owner-reported):** The owner saved the proposed London fact using **Keep both** and confirmed that both the York residence and London work memories are **Active** in Memory History. This validates reviewed coexistence storage in this one manual test.

**Prompt improvement:** The conflict classifier now explicitly distinguishes independent/coexisting facts from genuinely ambiguous statements, with an exact example of residence in York plus work in London. The original model output is preserved as an observation. The updated prompt and a mocked request regression test were published; see the later live retest below. Human review remains required.

## Post-fix unit-test confirmation (owner-reported)

After pulling the revised coexistence prompt and added mocked request test, the project owner reported that **all 21 offline unit tests passed** on Windows. These tests cover code paths and model-request formatting with mocks; they do **not** establish whether Qwen's revised live classification output is correct. That direct retest remains pending.

## Third local Qwen classification observation — coexistence retest (owner-reported)

After updating the local classifier prompt, the project owner re-entered the **same** new fact, "I work in London.", with topic `test_location`. There were two active facts to compare against. The owner reported Qwen suggested `coexists` **in both comparisons**:

1. Existing "I have moved from Bristol to York." vs proposed "I work in London.": `coexists` is the expected label. **The earlier `uncertain` error did not recur in this run.**
2. Existing "I work in London." vs proposed "I work in London.": `coexists` is a non-ideal label for a repeated, identical fact. The current classifier has no `duplicate` category, so it cannot explicitly identify exact repeats.

**Status:** Owner-reported live test; raw request/response traces not separately captured. One successful retest does not establish a general improvement rate. No new memory was requested to be saved during the retest.

**Next research improvement:** Add `duplicate` handling (preferably deterministic normalised exact-text detection before calling Qwen) and protect against duplicate writes. Maintain the default human review for ambiguous relationships and evaluate on a fixed set of labelled synthetic cases.

## Four-label duplicate guard — Version 4 Phase 3

The same London test fact was previously labelled `coexists` against its identical stored copy. We have added the `duplicate` label, plus a deterministic same-topic text comparison before Qwen is called. This catches formatting-only repeats (different case, repeated spaces and simple trailing punctuation) and disables Save in the UI. The reviewed-memory SQLite transaction additionally rejects duplicate inserts without superseding any records. Qwen may label a paraphrase as a possible duplicate; it is not automatically blocked without a review.

**Implementation published, local testing pending.** No existing records are deleted or changed during installation. See [the 16-case synthetic development benchmark](conflict_benchmark.md) and its limitations.
