# MemoryLab V1.0 — Release candidate notes

**Release position:** Portfolio release candidate, **not public or tagged** as of 16 November 2026. The repository is still private. No release files or packaged executables are implied.

## Implemented scope

- Local SQLite records with visible active/superseded history.
- Active-memory semantic retrieval via local `all-minilm`.
- Experimental Qwen local answers and visible retrieved memory evidence.
- AI-assisted but **human-approved** selective memory revisions, with atomic transaction checks.
- Safe disposable Streamlit demo mode, including UI and transactional prevention of broad-topic baseline overwrites.
- Offline unit tests, documented synthetic experiments, and local readiness/manual walkthroughs.

## Observed candidate acceptance

- **295 offline unit tests:** owner reported pass.
- **Memory save and history safeguards:** owner reported correct on final repeated demo.
- **Supported-answer example:** owner reported correct.
- **Unsupported-answer example:** owner reported abstention.
- An **earlier manual UI06 walkthrough failed**, showing only a front-desk record active. The exact trigger was not independently determined. An additional two-layer demo-only safeguard was committed, and the owner later reported the save/history check correct.

This is **user-reported local test evidence**, not a remote independent reproduction. A new clean-clone/virtual-environment run produced **six PASS lines** from the owner, covering layout, privacy ignore patterns, baseline guard, SQLite, runtime and offline suite. The optional seventh Ollama-model-tag line was not provided. An automated limited regex/pattern review across available diffs of all **104 main-branch commits** found no common credential-type flags; human content and historic privacy inspections remain outstanding.

## Known scientific limitations

- The Qwen model may invent unsupported details despite a system instruction to use saved evidence. A previously exposed fictional case produced an invented weekday.
- Strict extractive answer mode excessively abstained and is **not shipped as a live safety gate**.
- Lexical token novelty cannot detect wrong-but-familiar values (wrong person, stale name, negation).
- The experimental semantic verifier classified all 32 project-authored candidate answers as supported, missing 22 reviewer-labelled unsupported answers. It is **not shipped as a live decision gate**.
- These project-authored datasets are not independently sourced or representative. We make **no 100% accuracy, production safety, trained utility policy or independent validation claim**.

## Release candidate go/no-go

**Functional gate:** passed according to owner-reported 295 tests and final manual observations.

**Still required for making the repository public or tagging v1.0:** finish the optional model-tag/fresh demo confirmation, manually inspect tracked content and Git history for sensitive or identifying information beyond automated patterns, confirm rights to license all original content under the newly added [MIT license](../LICENSE), and inspect any screenshots/recording before sharing. The clean-clone offline checks already passed by owner report.

Follow [the publication checklist](publication_checklist.md) and [acceptance status](v1_acceptance_status.md). Do not silently treat a private release candidate as a public finished version.


## License

MemoryLab's original source and documentation are now offered under the [MIT License](../LICENSE), Copyright © 2026 MemoryLab contributors. Ollama models and third-party packages have separate upstream terms. The licence change does not make this private repository public and does not resolve the remaining privacy/publication review.


## Final tracked-content and Git email privacy screen

A patterned scan of **all 142 current tracked files** at the MIT-licensed commit found no matched personal email patterns, Windows user paths, UK phone formats, common secret keys, private-key blocks or assignment-style passwords/tokens. A separate prior pass screened changed-text diffs of 104 then-existing `main` commits for similar patterns without flags. **Commit metadata is a separate issue:** among the **106 commits** observed before this documentation update, the author/committer metadata contained a Gmail-domain email, which may be exposed if the repository becomes public. The owner must explicitly accept this exposure or arrange a safe history rewrite before publishing. These scans are non-exhaustive; the project remains private.
