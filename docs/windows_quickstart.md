# MemoryLab — Windows first-time setup

These instructions were prepared for a Windows local-first portfolio release. They have **not yet been independently executed on a fresh Windows installation**. The project owner's existing machine passed 295 automated tests by report.

## 1. Install dependencies

Install **Python 3.10 or newer** and **GitHub Desktop**. Install Ollama from https://ollama.com/download; it runs the local embedding and answer models. Open GitHub Desktop, clone the MemoryLab repository, and choose **Repository → Open in your editor** or **Show in Explorer**. Open **Command Prompt** inside that folder (the folder containing `app.py`).

The repository is currently private. Access requires the owner's GitHub permissions until publication.

## 2. Create a virtual environment

~~~bat
py -3 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
~~~

If `py -3` is unavailable, use `python -m venv .venv`. To reactivate an existing environment in cmd, run `.venv\Scripts\activate.bat`. PowerShell has different activation syntax; the commands here specifically target **cmd.exe**.

## 3. Install local models

~~~bat
ollama pull all-minilm
ollama pull qwen2.5:1.5b
ollama list
~~~

Keep Ollama running. The embedding model supports search; the Qwen model generates and reviews text. Both operate through Ollama's local HTTP interface. The project itself is not a cloud LLM service and does not require an API key.

## 4. Verify the application

~~~bat
python -m scripts.v1_release_readiness --check-models
~~~

Expected on the V1.0 candidate revision: **295 unit tests** and the engineering checks. A passing readiness report is saved under `results\raw\v1_release_readiness_XXX.md` and is excluded from Git. Failures must be investigated; the reported first-party acceptance from an existing installation does not guarantee a fresh install will pass.

## 5. Start a temporary fictional demo

~~~bat
python -m scripts.launch_v1_demo
~~~

The app should display **ISOLATED DEMO MODE**. It uses a unique temporary SQLite database for the entire session and deletes it when stopped with **Ctrl+C**. **Use only invented facts**, not personal information.

If the Streamlit port is busy, run a new launch on a genuinely free port, for example:

~~~bat
python -m scripts.launch_v1_demo --port 8505
~~~

Open the corresponding URL displayed in the terminal, e.g. `http://localhost:8505`. If many ports appear occupied, stop old terminals running Streamlit, or inspect port ownership in Windows before retrying. Do not assume a different port is automatically free.

For full fictional demo data and an eight-check acceptance sequence, use [the manual walkthrough](v1_manual_acceptance.md).

## 6. Optional persistent personal workspace

Only after understanding the application and its limitations:

~~~bat
python -m streamlit run app.py
~~~

This default mode stores facts in the local project `memorylab.db`. **Section 1's research baseline can replace all active facts in a topic after acknowledgement.** To update one fact while preserving another, use **Section 7: Smart Memory Review**. The application is experimental and has no guarantee of correct LLM inference. Avoid storing secrets or highly sensitive personal information.

## Troubleshooting

- **No module named streamlit:** activate the virtual environment and reinstall `requirements.txt`.
- **Model not found / connection refused:** start Ollama, run `ollama list`, and ensure both models were pulled.
- **Port unavailable:** close existing Streamlit processes or specify a free port with `--port` in the demo launcher.
- **Wrong memories displayed:** verify the isolated-demo banner and the browser's active port; another Streamlit server may still be open. **Do not delete a real memorylab.db** while diagnosing.
- **Demo has disappeared:** temporary demo memories are intentionally deleted when the launcher ends.
- **Python installation differs:** use `python --version` to check and recreate the venv with a supported Python.

## After setup

[Architecture](architecture_v1.md) · [3–5 minute demo](demo_storyboard.md) · [Release/privacy checklist](publication_checklist.md)
