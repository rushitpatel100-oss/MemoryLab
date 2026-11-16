# MemoryLab — Public portfolio release checklist

**Current repository visibility: PRIVATE.** The owner reported passing six fresh-environment readiness checks and an automated keyword/pattern review of the 104 main-branch commit diffs found no flags. Human content/privacy review, explicit licensing and publication decisions remain outstanding.

## Verified from the current GitHub tree

- A tracked `.gitignore` includes patterns for local `*.db`, `*.sqlite3`, `results/raw/`, `.env` and `.streamlit/secrets.toml`.
- The current tracked-file **names** inspected did not include an obvious database file, `.env` file, or model weight file.
- This does **not** establish that tracked source/document *contents* or older Git commits have no sensitive text.

## Owner actions before changing repository visibility

- [x] **Fresh clone + environment + offline tests (owner-reported):** created a clean copy in a separate folder and reported PASS on six readiness checks: layout, ignore patterns, guarded UI, temporary SQLite review storage, Python 3.14.5 with Streamlit, and offline suite. These specific checks are done; no seventh model-tag line was supplied.
- [ ] **Fresh-clone Ollama/demo check:** optionally confirm `--check-models` gives a PASS for both model tags and open the disposable demo from the clean clone. The previous complete manual test on the primary machine passed by owner report.
- [ ] **Current tracked content review:** examine the README, scripts, benchmarks, PDFs/images if added, and all research notes for personal details, real memories, passwords, tokens, internal company data or inappropriate third-party material.
- [x] **Automated history pattern review (limited scope):** screened available diffs of **104 commits** on the single GitHub `main` branch for common GitHub/OpenAI/AWS token formats, private-key headers, apparent credential assignments, Windows user-profile paths, and filenames suggesting local DBs/secrets. **No matches were reported.** Current tree filenames also showed no obvious secret/database artifact. This is a pattern check, not a guaranteed sensitive-data scan.
- [ ] **Human history/content review:** inspect all source/docs/benchmark data and older Git revisions for other private material, employer data, personally identifying information or unusual credentials. `.gitignore` does not scrub past commits. If private data are present, fix/rotate and sanitize history *before* publication.
- [ ] **No secrets in screenshots:** inspect browser windows, terminal paths, usernames, model prompts and file dialogs in any demo recording. Synthetic examples only.
- [ ] **License choice:** explicitly choose and add a license if you want others to reuse the code. A public repository without a license does **not** grant general permission for redistribution.
- [ ] **Version and docs:** verify all README links and commands on the final commit; write a short GitHub repo description, choose optional topics, and confirm references don't claim independent accuracy.
- [ ] **Security boundary:** don't expose Streamlit or local Ollama on the public internet; this V1.0 is intended for local use and is not a multi-user service.
- [ ] **Final decision:** only after the above checks, optionally make the repository public and create a stable `v1.0.0` release or tag. These actions are **not performed automatically**.

## Useful Windows checks

From Command Prompt in the project folder:

~~~bat
git status --short
git ls-files
git log --all --name-only --pretty=format:
python -m scripts.v1_release_readiness --check-models
~~~

Review `git ls-files` for currently tracked sensitive file names. Review the `git log` output for historical filenames (and inspect relevant commits' contents). Run a dedicated secret scanner or inspect suspicious changes manually before making the repository public; mere absence of suspicious file names is not sufficient.

## After the repository is publicly visible

Include only publicly suitable screenshots and a verified demo video. Don't share a `sandbox`, local Windows path or private GitHub connector URI as the public download link. Reconfirm the portfolio summary's claims against observed tests.

[Release notes](v1_release_notes.md) · [Clean setup](windows_quickstart.md)
