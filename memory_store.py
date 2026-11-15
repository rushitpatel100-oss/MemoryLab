"""Human-approved, atomic selective supersession for the existing SQLite schema."""
import sqlite3
from datetime import datetime, timezone


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

    with sqlite3.connect(db_path, timeout=10) as conn:
        conn.execute("BEGIN IMMEDIATE")
        actual = {row[0] for row in conn.execute(
            "SELECT id FROM memories WHERE active=1 AND topic=?",
            (topic,)
        )}
        if actual != set(expected):
            raise ValueError("Active memories changed; please review again.")
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
