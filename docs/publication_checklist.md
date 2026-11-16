# MemoryLab — Public portfolio release checklist

**Current repository visibility: PRIVATE.** This file is a publication gate, not a claim that privacy or clean installation have already passed.

## Verified from the current GitHub tree

- A tracked `.gitignore` includes patterns for local `*.db`, `*.sqlite3`, `results/raw/`, `.env` and `.streamlit/secrets.toml`.
- The current tracked-file **names** inspected did not include an obvious database file, `.env` file, or model weight file.
- This does **not** establish that tracked source/document *contents* or older Git commits have no sensitive text.

## Owner actions before changing repository visibility

- [ ] **Clean installation:** clone into a new folder without copying local `.venv`, database or `results/raw/`; install dependencies; pull both Ollama models; run the readiness check; start the isolated demo.
- [ ] **Current tracked content review:** examine the README, scripts, benchmarks, PDFs/images if added, and all research notes for personal details, real memories, passwords, tokens, internal company data or inappropriate third-party material.
- [ ] **Git history review:** check earlier commits too; `.gitignore` does not remove secrets already committed. If any private data appear, remove/rotate the secret and clean history using an appropriate Git process *before* publicity.
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
