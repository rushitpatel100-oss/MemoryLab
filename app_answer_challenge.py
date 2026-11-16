"""MemoryLab Phase 13 — one-reviewer, probe-blind factual-support UI.

    python -m streamlit run app_answer_challenge.py

This screen DOES NOT display novelty-probe predictions, expected labels,
or candidate model scores. All cases are fictional and project authored.
Labels remain amendable until the reviewer explicitly freezes the set.
"""
import streamlit as st

from scripts.phase13_review import (
    LABELS, SIGNOFF, load_dataset, load_signoff, lock_signoff,
    record_decision, save_signoff,
)

st.set_page_config(page_title="MemoryLab — Answer Challenge Review",
                   page_icon="🧠", layout="wide")
st.title("MemoryLab · Phase 13 answer-support review")
st.caption(
    "Label the candidate answer using the fictional source facts, "
    "without seeing the novelty probe's predictions. "
    "Project-authored stress-test cases; not independent gold truth."
)

try:
    data, digest = load_dataset()
    cases = data["cases"]
    ids = {c["id"] for c in cases}
    review = load_signoff(SIGNOFF, digest, ids)
except (OSError, ValueError) as exc:
    st.error("Cannot load the answer challenge: " + str(exc))
    st.stop()

count = len(review["decisions"])
total = len(cases)
locked = bool(review.get("locked_at"))
st.progress(count / total, text=f"Reviewed {count} of {total}")
if locked:
    st.success("Human review is locked. Diagnostic evaluation can now run.")
else:
    st.info(
        "Review every answer; the probe results remain hidden. "
        "A supporting quote must establish the candidate's **entire claim**, "
        "including the correct person, attribute, date and negation."
    )

choice = st.selectbox(
    "Select a fictional case",
    range(len(cases)),
    format_func=lambda i: (
        cases[i]["id"] + " — " +
        ("reviewed" if cases[i]["id"] in review["decisions"] else "not reviewed")
    ),
)
case = cases[choice]
cid = case["id"]
st.subheader("Case " + cid)
for m in case["retrieved_memories"]:
    st.write(f"**[M{m['id']}]** {m['fact']}")
st.write("**Question:** " + case["question"])
st.write("**Candidate answer:** " + case["candidate_answer"])

current = review["decisions"].get(cid, {})
if locked:
    st.write("**Saved review:** " + current.get("label", "not reviewed"))
    st.write("**Reason:** " + (current.get("rationale") or "(none entered)"))
else:
    with st.form("label_" + cid):
        initial_label = current.get("label", "supported")
        label = st.radio(
            "Is this candidate answer fully supported by these facts?",
            LABELS, index=LABELS.index(initial_label),
            help=(
                "Supported: the entire answer follows from the facts. "
                "Unsupported: claims something contradicted or not justified "
                "by them. Uncertain: cannot decide from the case; explain why."
            ),
        )
        rationale = st.text_area(
            "Your reason (required for Uncertain)",
            value=current.get("rationale", ""),
            height=95,
            placeholder="For example: the sentence specifies an old day, not the new day.",
        )
        submitted = st.form_submit_button("Save review")
    if submitted:
        try:
            record_decision(review, cid, label, rationale, ids)
            save_signoff(review)
        except (OSError, ValueError) as exc:
            st.error("Could not save the decision: " + str(exc))
        else:
            st.rerun()

st.divider()
if not locked and count == total:
    st.subheader("Freeze the reviewed labels")
    st.warning(
        "Locking preserves your decisions for the evaluation. "
        "The app will no longer allow changes to this signoff."
    )
    attest = st.checkbox(
        "I reviewed each fictional answer using the shown facts, "
        "without seeing the novelty probe predictions."
    )
    if st.button("Freeze all 32 reviews", disabled=not attest):
        try:
            lock_signoff(review, ids)
            save_signoff(review)
        except (OSError, ValueError) as exc:
            st.error("Could not freeze labels: " + str(exc))
        else:
            st.rerun()

if locked:
    st.write("**Next command:**")
    st.code("python -m scripts.evaluate_answer_challenge", language="bash")
    st.caption("The evaluation script creates a new report; this app never displays its scores.")
else:
    st.caption(
        "Review data is saved only under results/raw/phase13_answer_signoff.json "
        "(Git-ignored). Earlier human signoffs and MemoryLab's database remain untouched."
    )
