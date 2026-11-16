"""MemoryLab AI-assisted review dashboard.

Start after the automatic local AI judge has finished all 24 cases:
    python -m streamlit run app_review.py

The original machine-generated report is immutable. Final human decisions,
approval methods, and revisions are saved in a different local file.
"""
import streamlit as st

from scripts.review_holdout_v2 import load_local_cases
from scripts.review_signoff import (
    SIGNOFF_FILE, approve_one, approve_unflagged, draft_decision,
    load_ai_drafts, load_signoff, markdown_report, review_stats,
    save_signoff, write_report, AXES,
)

RELATIONS = ("duplicate", "replaces", "coexists", "uncertain")
ACTIONS = ("skip_duplicate", "supersede_old", "keep_both", "review_needed")
AXIS_OPTIONS = ("yes", "no", "unknown")

st.set_page_config(page_title="MemoryLab — Review AI Drafts", page_icon="🧠",
                   layout="wide")
st.title("MemoryLab — Review AI-generated memory labels")
st.caption(
    "AI drafts first → human edits or approvals → transparent final report. "
    "No data is sent to a cloud service by this dashboard."
)
st.info(
    "This workflow is AI-assisted human verification, not an independently "
    "human-labelled benchmark. It does not change any saved SQLite memories."
)

cases, digest = load_local_cases()
try:
    ai, source_sha = load_ai_drafts(cases=cases, digest=digest)
except FileNotFoundError:
    st.warning("The AI draft file is missing. Run this from the project folder first:")
    st.code("python -m scripts.auto_review_holdout_v2", language="text")
    st.stop()
except (ValueError, OSError) as error:
    st.error(str(error))
    st.code("python -m scripts.auto_review_holdout_v2", language="text")
    st.stop()

case_ids = {case["id"] for case in cases}
try:
    signoff = load_signoff(
        SIGNOFF_FILE, digest, source_sha, ai["judge_model"], case_ids
    )
except (ValueError, OSError) as error:
    st.error(str(error))
    st.caption(
        "Existing signoffs are preserved. Avoid manually deleting the "
        "record; the AI source and saved review need reconciling."
    )
    st.stop()

stats = review_stats(signoff, cases)
a, b, c, d = st.columns(4)
a.metric("Cases", stats["total"])
b.metric("Approved", stats["approved"])
c.metric("Remaining", stats["remaining"])
d.metric("Human edits", stats["corrected"])
st.caption("AI judge: " + ai["judge_model"])

st.subheader("Full draft report")
rows = []
for case in cases:
    cid = case["id"]
    proposal = ai["answers"][cid]
    final = signoff["decisions"].get(cid)
    rows.append({
        "Case": cid,
        "Old fact": case["old_fact"],
        "New fact": case["new_fact"],
        "AI label": proposal["provisional_label"],
        "AI explanation": proposal["reason"],
        "Needs attention": proposal["triage"] == "needs_review",
        "Final label": final["final"]["label"] if final else "Pending",
        "Approval": final["method"] if final else "Pending",
    })
st.dataframe(rows, use_container_width=True, hide_index=True)

st.subheader("Approve unchanged, unflagged cases together")
st.write(
    "After reading the table, you can approve unchanged AI drafts that "
    "have no warnings. Flagged cases must be reviewed individually."
)
attested = st.checkbox(
    "I have read the unflagged AI suggestions in the table and accept "
    "their content as provisional human-reviewed annotations."
)
if st.button("Approve all remaining unflagged cases"):
    if not attested:
        st.warning("Please read the report and tick the confirmation box first.")
    else:
        approved = approve_unflagged(
            signoff, ai, [case["id"] for case in cases], attested=True
        )
        if approved:
            save_signoff(signoff)
        st.success("Approved " + str(approved) + " unchanged AI drafts.")
        st.rerun()

st.subheader("Review or correct an individual case")
ordered_cases = sorted(
    cases,
    key=lambda case: (
        case["id"] in signoff["decisions"],
        ai["answers"][case["id"]]["triage"] != "needs_review",
        case["id"]
    ),
)
selected = st.selectbox(
    "Choose a case",
    options=[case["id"] for case in ordered_cases],
    format_func=lambda cid: (
        cid + " — "
        + ("Approved" if cid in signoff["decisions"] else "Needs approval")
        + (" · flagged" if ai["answers"][cid]["triage"] == "needs_review" else "")
    )
)
case = next(row for row in cases if row["id"] == selected)
machine = ai["answers"][selected]
current = signoff["decisions"].get(selected)
form_data = current["final"] if current else draft_decision(machine)

st.markdown("**Old memory:** " + case["old_fact"])
st.markdown("**New memory:** " + case["new_fact"])
st.markdown("**AI suggestion:** " + machine["provisional_label"])
st.markdown("**AI explanation:** " + machine["reason"])
if machine.get("flags"):
    st.warning("AI warnings: " + " | ".join(machine["flags"]))
if current:
    st.caption(
        "Previously saved: " + current["method"]
        + ". Saving again records a new audit entry."
    )
with st.form("review_" + selected):
    label = st.selectbox(
        "Final relationship",
        RELATIONS, index=RELATIONS.index(form_data["label"]),
    )
    reason = st.text_area(
        "Final explanation (write naturally and specifically)",
        value=form_data["reason"], height=110,
    )
    st.markdown("**Evidence checks**")
    axes = {}
    axis_names = {
        "same_entity": "Same specific person/object/event?",
        "same_attribute": "Same specific attribute?",
        "old_fact_known_obsolete": "Is the exact old fact proven outdated?",
        "new_value_known": "Is a specific new value provided?",
    }
    for key in AXES:
        axes[key] = st.selectbox(
            axis_names[key], AXIS_OPTIONS,
            index=AXIS_OPTIONS.index(form_data["axes"][key]),
        )
    action = st.selectbox(
        "Recommended storage action (never executed)",
        ACTIONS, index=ACTIONS.index(form_data["storage_action"])
    )
    submitted = st.form_submit_button("Save and approve this case")
if submitted:
    entry = {
        "label": label, "reason": reason.strip(),
        "axes": axes, "storage_action": action,
    }
    try:
        approve_one(signoff, selected, entry, machine)
        save_signoff(signoff)
    except (ValueError, OSError) as error:
        st.error("Not saved: " + str(error))
    else:
        st.success("Saved your decision for " + selected + ".")
        st.rerun()

st.subheader("Final report")
if stats["remaining"]:
    st.info(
        "Once all cases are explicitly approved or corrected, you can "
        "generate a labelled, traceable Markdown report. "
        + str(stats["remaining"]) + " case(s) remain."
    )
else:
    st.success("All cases have recorded human signoff.")
    content = markdown_report(cases, ai, signoff)
    st.download_button(
        "Download complete human-reviewed AI report",
        data=content,
        file_name="MemoryLab_AI_assisted_human_review.md",
        mime="text/markdown",
    )
    if st.button("Also save a versioned Markdown report in results/raw"):
        path = write_report(cases, ai, signoff)
        st.success("Report saved locally: " + str(path))
st.caption(
    "The initial AI drafts, Reviewer A/B files, old experiments and "
    "SQLite memories are never overwritten by this dashboard."
)
