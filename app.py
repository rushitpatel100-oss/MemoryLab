import sqlite3
from datetime import datetime, timezone

import streamlit as st

DB_NAME = "memorylab.db"


def connect():
    """Open a connection to the local SQLite memory database."""
    return sqlite3.connect(DB_NAME)


def setup_database():
    """Create the memory table when the app runs for the first time."""
    with connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                fact TEXT NOT NULL,
                created_at TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1
            )
        """)


def save_memory(topic, fact):
    """Save a memory and supersede earlier facts with the same topic."""
    topic = topic.strip().lower()
    fact = fact.strip()

    if not topic or not fact:
        return False

    timestamp = datetime.now(timezone.utc).isoformat()

    with connect() as conn:
        conn.execute(
            "UPDATE memories SET active = 0 WHERE topic = ?",
            (topic,)
        )
        conn.execute(
            """
            INSERT INTO memories (topic, fact, created_at)
            VALUES (?, ?, ?)
            """,
            (topic, fact, timestamp)
        )

    return True


def search_memories(topic):
    """Find active memories by topic, or list all active memories."""
    topic = topic.strip().lower()

    with connect() as conn:
        conn.row_factory = sqlite3.Row

        if topic:
            results = conn.execute(
                """
                SELECT * FROM memories
                WHERE active = 1 AND topic LIKE ?
                ORDER BY id DESC
                """,
                (f"%{topic}%",)
            ).fetchall()
        else:
            results = conn.execute(
                """
                SELECT * FROM memories
                WHERE active = 1
                ORDER BY id DESC
                """
            ).fetchall()

    return [dict(row) for row in results]


def get_history():
    """Show both active and superseded memories."""
    with connect() as conn:
        conn.row_factory = sqlite3.Row
        results = conn.execute(
            "SELECT * FROM memories ORDER BY id DESC"
        ).fetchall()

    return [dict(row) for row in results]


st.set_page_config(
    page_title="MemoryLab",
    page_icon="🧠",
    layout="centered"
)

setup_database()

st.title("🧠 MemoryLab")
st.write("An experimental adaptive AI memory system")

st.subheader("1. Add a memory")

topic = st.text_input(
    "Memory topic",
    placeholder="Example: job"
)

fact = st.text_area(
    "Memory information",
    placeholder="Example: I work as a mechanical engineer."
)

if st.button("Save memory"):
    if save_memory(topic, fact):
        st.success("Memory saved successfully!")
    else:
        st.warning("Please enter a topic and a fact.")

st.divider()

st.subheader("2. Search active memories")

query = st.text_input(
    "Search by topic",
    placeholder="Example: job"
)

if st.button("Search"):
    results = search_memories(query)

    if results:
        for memory in results:
            st.info(f"{memory['topic']}: {memory['fact']}")
    else:
        st.warning("No active memories found.")

st.divider()

st.subheader("3. Memory history")

if st.button("Show all memories"):
    history = get_history()

    if not history:
        st.write("No memories saved yet.")

    for memory in history:
        status = "Active" if memory["active"] else "Superseded"
        st.write(f"**{memory['topic']}** — {memory['fact']}")
        st.caption(
            f"Status: {status} | Saved: {memory['created_at']}"
        )

# Semantic search feature
from semantic_search import find_similar

st.divider()

st.subheader("4. Semantic Memory Search")

question = st.text_input(
    "Ask a question",
    placeholder="What is my profession?"
)

if st.button("Find related memories"):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        active_memories = search_memories("")

        if not active_memories:
            st.warning("No active memories found.")
        else:
            try:
                results = find_similar(
                    question,
                    active_memories
                )

                for result in results[:3]:
                    memory = result["memory"]
                    score = result["similarity"]

                    st.write(
                        f"**{memory['fact']}**"
                    )
                    st.caption(
                        f"Similarity score: {score:.3f}"
                    )
            except Exception as error:
                st.error(
                    f"Semantic search failed: {error}"
                )
                st.info(
                    "Check that Ollama is running "
                    "and all-minilm is installed."
                )
