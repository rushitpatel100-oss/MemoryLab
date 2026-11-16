# MemoryLab — Public portfolio release checklist

**Current repository visibility: PRIVATE.** The owner reported passing six fresh-environment readiness checks and an automated keyword/pattern review of the 104 main-branch commit diffs found no flags. MIT licensing is completed. Automated content and diff pattern checks did not find credentials, **but a Gmail address is present in Git commit metadata**; the owner must confirm whether that email can be exposed publicly. Human content/privacy review and publication approval remain outstanding.

## Verified from the current GitHub tree

- A tracked `.gitignore` includes patterns for local `*.db`, `*.sqlite3`, `results/raw/`, `.env` and `.streamlit/secrets.toml`.
- The current tracked-file **names** inspected did not include an obvious database file, `.env` file, or model weight file.
- A patterned scan read all **142 current tracked blobs** at commit `e780e61`, checking for email patterns (except fictional example domains), UK phone formats, Windows user-profile paths, common GitHub/OpenAI/AWS token formats, private-key headers and credential assignments: **no matches found**.
- **Separate metadata finding:** the available author/committer metadata from **106 existing commits** contains **one Gmail address** and one GitHub-domain address. Commit metadata can become publicly accessible when the repository becomes public. The email itself is not repeated in this checklist.
- These are limited pattern checks; they **do not certify** absence of all sensitive data, copyrighted material or real-world identifying details.

## Owner actions before changing repository visibility

- [x] **Fresh clone + environment + offline tests (owner-reported):** created a clean copy in a separate folder and reported PASS on six readiness checks: layout, ignore patterns, guarded UI, temporary SQLite review storage, Python 3.14.5 with Streamlit, and offline suite. These specific checks are done; no seventh model-tag line was supplied.
- [ ] **Fresh-clone Ollama/demo check:** optionally confirm `--check-models` gives a PASS for both model tags and open the disposable demo from the clean clone. The previous complete manual test on the primary machine passed by owner report.
- [ ] **Current tracked content review:** examine the README, scripts, benchmarks, PDFs/images if added, and all research notes for personal details, real memories, passwords, tokens, internal company data or inappropriate third-party material.
- [x] **Automated history pattern review (limited scope):** screened available diffs of **104 commits** on the single GitHub `main` branch for common GitHub/OpenAI/AWS token formats, private-key headers, apparent credential assignments, Windows user-profile paths, and filenames suggesting local DBs/secrets. **No matches were reported.** Current tree filenames also showed no obvious secret/database artifact. This is a pattern check, not a guaranteed sensitive-data scan.
- [ ] **Human history/content review:** inspect all source/docs/benchmark data and older Git revisions for other private material, employer data, personally identifying information or unusual credentials. `.gitignore` does not scrub past commits. If private data are present, fix/rotate and sanitize history *before* publication.
- [ ] **Git author-email privacy decision:** confirm the Gmail address in commit metadata is acceptable to disclose. If not, **do not make the repository public yet**: update future Git author configuration and plan a carefully coordinated history rewrite, with backup, before publication. Changing GitHub's email privacy settings alone will not alter email fields already stored in old commits.
- [ ] **No secrets in screenshots:** inspect browser windows, terminal paths, usernames, model prompts and file dialogs in any demo recording. Synthetic examples only.
- [x] **MIT license:** added a standard root-level `LICENSE` file (Copyright © 2026 MemoryLab contributors) and linked it in the README. Confirm contributors' agreement and rights to distribute code or documentation before public publication; external dependencies and model weights remain governed by their own licenses.
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
