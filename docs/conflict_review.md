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
