"""Human-approved, atomic selective supersession for the existing SQLite schema."""
import sqlite3
from contextlib import closing
from datetime import datetime, timezone

from memory_text import is_same_stored_fact


def save_reviewed_memory(topic, fact, decisions, expected_ids,
                         db_path="memorylab.db"):
    """Preserve non-superseded facts and reject reviews made on stale data."""
    topic, fact = topic.strip().lower(), fact.strip()
    if not topic or not fact:
        raise ValueError("Topic and fact must not be blank.")
    expected = list(expected_ids)
    if len(set(expected)) != len(expected):
        raise ValueError("Repeated IDs in review.")
    if set(decisions) != set(expected):
        raise ValueError("Every previously reviewed memory needs a decision.")
    if any(x not in {"keep", "supersede"} for x in decisions.values()):
        raise ValueError("Invalid save decision.")

    # sqlite3.Connection as a context manager commits/rolls back, but does
    # NOT close the connection; closing() releases Windows file locks.
    with closing(sqlite3.connect(db_path, timeout=10)) as conn, conn:
        conn.execute("BEGIN IMMEDIATE")
        existing = list(conn.execute(
            "SELECT id, fact FROM memories WHERE active=1 AND topic=?",
            (topic,)
        ))
        actual = {row[0] for row in existing}
        if actual != set(expected):
            raise ValueError("Active memories changed; please review again.")

        # Reject duplicates before superseding anything; rollback on error.
        # Checked inside the same write transaction to prevent stale-review
        # and duplicate-write races.
        for old_id, old_fact in existing:
            if is_same_stored_fact(topic, old_fact, topic, fact):
                raise ValueError(
                    f"Duplicate of active memory M{old_id}; "
                    "nothing was saved."
                )
        for mid, action in decisions.items():
            if action == "supersede":
                conn.execute(
                    "UPDATE memories SET active=0 "
                    "WHERE id=? AND active=1 AND topic=?",
                    (mid, topic)
                )
        cur = conn.execute(
            "INSERT INTO memories (topic, fact, created_at, active) "
            "VALUES (?, ?, ?, 1)",
            (topic, fact, datetime.now(timezone.utc).isoformat()),
        )
        return cur.lastrowid
