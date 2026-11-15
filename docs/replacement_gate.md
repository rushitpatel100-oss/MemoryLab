# V4 Phase 5 — Replacement-evidence safeguard

## Why this exists

Experiments 007–009 showed that Qwen sometimes recommends `replaces` for independent facts and even paraphrases of duplicates. The experimental two-stage classifier performed worse on the 16-case synthetic comparison. Rather than adding more Qwen inference passes, this experiment adds a narrow deterministic check and stronger user confirmations.

## How it works

1. The unchanged single-pass Qwen classifier suggests one of four labels.
2. If it suggests `replaces`, a local Python text check looks for a change verb followed by `from X to Y`, where value X also appears as whole words in the old fact.
3. When this phrase is absent, the displayed recommendation becomes `uncertain`. The original Qwen prediction is still available for analysis.
4. When the phrase is found, the recommendation may stay `replaces`, but it is **not verified**. The user must still confirm subject identity, attribute identity, and genuine outdatedness.
5. No memory is changed until the user manually chooses Supersede and confirms all three checks. Fresh review controls prevent reusing prior acknowledgements.

**Supported signal example:** OLD `I currently live in Bristol.` and NEW `I moved from Bristol to York.`

**Unsupported replacement example:** OLD `I live in York.` and NEW `I work in London.` If Qwen says `replaces`, the gate changes that suggestion to `uncertain`.

**False negative example:** OLD `I prefer French.` and NEW `I now prefer Spanish instead of French.` This can be a real update that lacks a literal `from X to Y` phrase; the gate will request manual review rather than asserting replacement.

**Possible false positive:** An unrelated fact could share value X and contain a `from X to Y` phrase. The text rule never proves identical entities or attributes. Human verification remains essential.

The original section 1 topic overwrite baseline is intentionally not covered by this experimental review safeguard. Direct code calls to SQLite are also outside the UI confirmation barrier.

## Local test commands (Windows)

Fetch and pull in GitHub Desktop. In the MemoryLab virtual environment:

~~~bat
python -m unittest discover -s tests -v
python -m scripts.compare_replacement_gate --limit 4
~~~

Expected: **54 offline tests**, including 12 new gate/runner tests. Once they pass, run all 16 previously analysed synthetic cases and export optional diagnostics:

~~~bat
python -m scripts.compare_replacement_gate --output results/raw/gate.json
~~~

The comparison script uses one Qwen call per pair; the raw and guarded labels share the same model output, and the script never reads or writes the SQLite database. It prints author-label agreement, false replacement suggestions, and true replacement suggestions retained. The output folder is excluded from Git.

## Research limitations

The narrow gate may simply trade false supersession for missed true updates, which matters for memory usefulness. The 16-case evaluation candidate was already inspected in Experiment 009 and **influenced this safeguard design**; outcomes are development diagnostics, not held-out evidence. Further independent label adjudication, unseen synthetic profiles, repeated/randomised runs and human-error measurement are required. No paid API or new dependencies.

## Next: Prospective label-first review

A new 20-case fictional blind-review candidate is now published. Do not run classifier predictions before labelling and locking all cases. See [the step-by-step blind review protocol](blind_review.md). The newly supplied evaluation candidate has **no published expected labels**, and its results should not be confused with the reused 16-case development diagnostic above.
