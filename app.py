import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone

import streamlit as st

DB_NAME = "memorylab.db"


def connect():
    """Open a connection to the local SQLite memory database."""
    return sqlite3.connect(DB_NAME)


def setup_database():
    """Create the memory table when the app runs for the first time."""
    with closing(connect()) as conn, conn:
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

    with closing(connect()) as conn, conn:
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

    with closing(connect()) as conn, conn:
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
    with closing(connect()) as conn, conn:
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

st.subheader("1. Add a memory (baseline)")
st.caption(
    "This baseline automatically supersedes ALL older facts under the "
    "same topic. For conflict-aware saving use section 7 below."
)

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

# Grounded answer generation (Version 3)
from answer_generator import generate_answer

st.divider()

st.subheader("5. Ask MemoryLab")
st.caption(
    "Answers use active memories and a local Qwen model. "
    "Similarity is a retrieval score, not a confidence percentage."
)

answer_question = st.text_input(
    "Question for the AI",
    placeholder="What is my profession?",
    key="answer_question",
)

minimum_score = st.slider(
    "Minimum memory similarity (experimental)",
    min_value=0.0,
    max_value=1.0,
    value=0.25,
    step=0.05,
    help=(
        "Higher values exclude more memories. This is a heuristic "
        "threshold, not a calibrated probability."
    ),
)

if st.button("Generate answer from memory"):
    if not answer_question.strip():
        st.warning("Please enter a question.")
    else:
        active_memories = search_memories("")

        if not active_memories:
            st.info(
                "No active memories yet. Add a test memory in section 1."
            )
        else:
            try:
                with st.spinner("Finding relevant memories..."):
                    ranked = find_similar(
                        answer_question, active_memories
                    )
                    selected = [
                        item for item in ranked
                        if item["similarity"] >= minimum_score
                    ][:3]

                if not selected:
                    st.info(
                        "No memories met the similarity threshold. "
                        "Try a clearer question, add a relevant memory, "
                        "or lower the threshold."
                    )
                else:
                    with st.spinner("Generating with local Qwen..."):
                        answer = generate_answer(
                            answer_question,
                            [item["memory"] for item in selected],
                        )

                    st.write(answer)

                    with st.expander("See retrieved memory evidence"):
                        for item in selected:
                            memory = item["memory"]
                            st.write(
                                f"[M{memory['id']}] "
                                f"{memory['topic']}: {memory['fact']}"
                            )
                            st.caption(
                                "Similarity score: "
                                f"{item['similarity']:.3f}"
                            )
            except Exception as error:
                st.error(f"Answer generation failed: {error}")
                st.info(
                    "Check that Ollama is running and that both "
                    "'all-minilm' and 'qwen2.5:1.5b' are installed "
                    "(run 'ollama list' in Command Prompt)."
                )

# Controlled memory-impact pilot (Version 4, phase 1)
from memory_ablation import run_memory_comparison

st.divider()

st.subheader("6. Memory Impact Lab")
st.caption(
    "Experimental: ask local Qwen the same question with and without "
    "one selected memory. Both conditions call Qwen. This is not "
    "yet a learned retention policy or a formal research benchmark."
)

pilot_memories = search_memories("")

if not pilot_memories:
    st.info("Add a fictional test memory in section 1 to run this pilot.")
else:
    pilot_memory = st.selectbox(
        "Select one active test memory",
        pilot_memories,
        format_func=lambda m: f"[M{m['id']}] {m['topic']}: {m['fact'][:90]}",
        key="pilot_memory",
    )

    pilot_question = st.text_input(
        "Question to compare",
        placeholder="What hobby do I enjoy?",
        key="pilot_question",
    )

    if st.button("Run with/without-memory experiment"):
        if not pilot_question.strip():
            st.warning("Enter a question to compare.")
        else:
            try:
                with st.spinner("Running two local Qwen calls..."):
                    st.session_state["memory_pilot_result"] = (
                        run_memory_comparison(
                            pilot_question, pilot_memory
                        )
                    )
            except Exception as error:
                st.error(f"Experiment failed: {error}")
                st.info(
                    "Confirm that Ollama is running and "
                    "'qwen2.5:1.5b' is installed."
                )

    pilot_result = st.session_state.get("memory_pilot_result")

    if pilot_result:
        st.write(f"**Question:** {pilot_result['question']}")
        st.caption(
            f"Selected memory [M{pilot_result['memory']['id']}]: "
            f"{pilot_result['memory']['fact']}"
        )

        left, right = st.columns(2)
        with left:
            st.markdown("**Without memory**")
            st.write(pilot_result["without_memory"]["answer"])
            st.caption(
                "Elapsed: "
                f"{pilot_result['without_memory']['elapsed_seconds']:.2f}s"
            )
        with right:
            st.markdown("**With memory**")
            st.write(pilot_result["with_memory"]["answer"])
            st.caption(
                "Elapsed: "
                f"{pilot_result['with_memory']['elapsed_seconds']:.2f}s"
            )

        st.info(
            "Compare both answers with the known fictional fact. "
            "An answer difference is not proof of improved accuracy; "
            "manually check whether each answer is supported."
        )

        st.download_button(
            "Download pilot result (JSON)",
            data=json.dumps(
                pilot_result, indent=2, ensure_ascii=False
            ),
            file_name="memorylab_pilot_result.json",
            mime="application/json",
        )
        st.caption(
            "The downloaded JSON contains the question, selected memory, "
            "and answers. Do not publish results with personal data."
        )

# V4 Phase 2: human-reviewed memory conflict handling
from memory_conflicts import classify_pair
from memory_store import save_reviewed_memory
from memory_text import is_same_stored_fact
from memory_staged import classify_pair_staged
from replacement_gate import classify_pair_guarded

st.divider()
st.subheader("7. Smart Memory Review")
st.caption(
    "MemoryLab detects repeat facts and Qwen suggests duplicate / "
    "replaces / coexists / uncertain. "
    "You decide before anything is changed. This pilot checks "
    "only memories with the same exact topic."
)

smart_classifier = st.radio(
    "Classification method",
    ("Single-pass baseline", "Safety-gated experimental",
     "Two-stage experimental"),
    horizontal=True,
    key="smart_classifier",
)
st.caption(
    "Safety-gated uses one Qwen call and a conservative text rule. "
    "Two-stage may use two Qwen calls. Neither checks truth. "
    "Every supersession requires your explicit review."
)

smart_topic = st.text_input(
    "New memory topic", placeholder="location", key="smart_topic"
)
smart_fact = st.text_area(
    "New memory fact",
    placeholder="I have moved from Bristol to York.",
    key="smart_fact",
)

if st.button("Review possible conflicts"):
    # New ID ensures prior review acknowledgements cannot carry forward.
    st.session_state["smart_review_count"] = (
        st.session_state.get("smart_review_count", 0) + 1
    )
    st.session_state["smart_review"] = None
    nt, nf = smart_topic.strip().lower(), smart_fact.strip()
    if not nt or not nf:
        st.warning("Enter both a topic and a fact.")
    else:
        matches = [
            m for m in search_memories("") if m["topic"] == nt
        ]
        if len(matches) > 10:
            st.warning(
                "More than 10 active memories have this topic. "
                "This early pilot will not silently skip them. "
                "No memory was modified."
            )
        else:
            try:
                with st.spinner("Comparing local memories using Qwen..."):
                    if smart_classifier == "Safety-gated experimental":
                        compare = classify_pair_guarded
                    elif smart_classifier == "Two-stage experimental":
                        compare = classify_pair_staged
                    else:
                        compare = classify_pair
                    items = [
                        {"memory": m, "proposal": compare(m, nt, nf)}
                        for m in matches
                    ]
                st.session_state["smart_review"] = {
                    "topic": nt, "fact": nf, "items": items,
                    "classifier": smart_classifier,
                    "review_count": st.session_state["smart_review_count"],
                    "expected_ids": [m["id"] for m in matches],
                }
            except Exception as exc:
                st.error(f"Could not classify memories: {exc}")
                st.info(
                    "Confirm that Ollama and qwen2.5:1.5b are running. "
                    "Nothing was changed."
                )

review = st.session_state.get("smart_review")
if review is not None:
    if (
        smart_topic.strip().lower() != review["topic"]
        or smart_fact.strip() != review["fact"]
        or smart_classifier != review.get("classifier")
    ):
        st.warning(
            "You changed the proposed fact. Review conflicts again "
            "before saving."
        )
    else:
        st.write("**New fact:**", review["fact"])
        if not review["items"]:
            st.info("No active memories have this topic. Save as a new fact.")
        else:
            st.caption(
                "The safe default is Keep both. Choose Supersede "
                "only when the old fact truly needs updating."
            )
        duplicate_matches = [
            entry for entry in review["items"]
            if is_same_stored_fact(
                entry["memory"]["topic"], entry["memory"]["fact"],
                review["topic"], review["fact"]
            )
        ]
        possible_duplicates = [
            entry for entry in review["items"]
            if entry["proposal"]["relation"] == "duplicate"
            and entry not in duplicate_matches
        ]
        if duplicate_matches:
            ids = ", ".join(
                f"M{entry['memory']['id']}" for entry in duplicate_matches
            )
            st.warning(
                f"This exact fact is already active as {ids}. "
                "Duplicate saving is disabled; no data will be changed."
            )
        elif possible_duplicates:
            st.warning(
                "Qwen thinks this may repeat an existing fact. "
                "Please review before choosing to save."
            )
            confirm_potential_duplicate = st.checkbox(
                "I reviewed the possible duplicate and still want to save it.",
                key=f"confirm_duplicate_{review['topic']}_{review['fact']}",
            )
        else:
            confirm_potential_duplicate = True

        actions = {}
        confirmations = {}
        for entry in review["items"]:
            old = entry["memory"]
            assessment = entry["proposal"]
            st.write(f"**M{old['id']} — {old['fact']}**")
            st.caption(
                f"Suggestion ({assessment.get('source', 'qwen')}): "
                f"{assessment['relation']} — {assessment['reason']}"
            )
            if assessment.get("raw_relation") == "replaces":
                audit = assessment["gate"]
                st.info(
                    "Qwen originally suggested Replaces. "
                    f"Evidence signal: {audit['status']}. "
                    f"{audit['reason']}"
                )
            if assessment.get("stages"):
                with st.expander(f"See decision steps for M{old['id']}"):
                    for step in assessment["stages"]:
                        st.write(step)
            choice = st.radio(
                f"What should happen to M{old['id']}?",
                ("Keep both", "Supersede old memory"),
                key=f"smart_action_{old['id']}_{review.get('review_count', 0)}",
            )
            actions[old["id"]] = (
                "keep" if choice == "Keep both" else "supersede"
            )
            if choice == "Supersede old memory":
                st.warning(
                    "Superseding deactivates this old fact. Qwen and the "
                    "text rule cannot verify that it is outdated. "
                    "Confirm each condition from the actual facts."
                )
                checks = [
                    st.checkbox(
                        "Both statements refer to the same person or object.",
                        key=f"verify_subject_{old['id']}_{review.get('review_count', 0)}",
                    ),
                    st.checkbox(
                        "Both describe the same specific attribute.",
                        key=f"verify_attribute_{old['id']}_{review.get('review_count', 0)}",
                    ),
                    st.checkbox(
                        "The new fact makes this exact older fact outdated.",
                        key=f"verify_outdated_{old['id']}_{review.get('review_count', 0)}",
                    ),
                ]
                confirmations[old["id"]] = all(checks)
            else:
                confirmations[old["id"]] = True

        if st.button(
            "Save reviewed memory",
            disabled=(
                bool(duplicate_matches)
                or not confirm_potential_duplicate
                or not all(confirmations.values())
            ),
        ):
            try:
                new_id = save_reviewed_memory(
                    review["topic"], review["fact"], actions,
                    review["expected_ids"],
                )
                st.session_state["smart_review"] = None
                st.success(
                    f"Memory M{new_id} saved. Only the older "
                    "memories you explicitly selected were superseded."
                )
            except (ValueError, sqlite3.Error) as exc:
                st.error(f"Could not save: {exc}")
                st.info(
                    "No partial changes were saved. "
                    "If other memories changed, start a new review."
                )
