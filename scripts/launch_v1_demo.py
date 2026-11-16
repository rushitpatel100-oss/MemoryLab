"""Launch MemoryLab in disposable, fictional-data-only V1.0 demo mode.

Usage:
    python -m scripts.launch_v1_demo
    python -m scripts.launch_v1_demo --port 8502

A fresh SQLite database is created in the OS temporary directory, separate
from the normal project database. Both the research baseline and Smart
Memory Review use that temporary database. When the Streamlit process
exits, the launcher deletes its demo files.

Use only fictional facts in the demo. Do not enter personal information
or passwords. This does not certify the correctness of generated answers.
"""
import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def launch(port=8501, runner=subprocess.run):
    if not isinstance(port, int) or not 1 <= port <= 65535:
        raise ValueError("Port must be between 1 and 65535.")
    with tempfile.TemporaryDirectory(prefix="memorylab_v1_demo_") as directory:
        database = Path(directory) / "demo.sqlite3"
        env = os.environ.copy()
        # Force these two settings even if the user has a different
        # MEMORYLAB_DB_PATH in their shell. Never launch on the live DB.
        env["MEMORYLAB_DB_PATH"] = str(database)
        env["MEMORYLAB_DEMO_MODE"] = "1"
        command = [
            sys.executable, "-m", "streamlit", "run", str(ROOT / "app.py"),
            "--server.port", str(port),
        ]
        print("Opening isolated MemoryLab demo on port", port, flush=True)
        print("Temporary demo database:", database, flush=True)
        print("Your normal memorylab.db is not accessed by this launcher.", flush=True)
        print("Use Ctrl+C to close the demo and remove its data.", flush=True)
        try:
            finished = runner(command, cwd=str(ROOT), env=env, check=False)
            return finished.returncode
        except KeyboardInterrupt:
            print("Isolated demo ended; temporary database is being removed.")
            return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8501)
    args = parser.parse_args()
    try:
        return launch(args.port)
    except (ValueError, OSError) as error:
        print("Could not start demo:", error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
