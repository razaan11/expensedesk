"""ExpenseDesk - Streamlit app. Run with: streamlit run app.py"""
from datetime import date, time
from pathlib import Path

import pandas as pd
import streamlit as st

from expensedesk.itinerary import build_itinerary_docx, build_itinerary_text
from expensedesk.policy import DEFAULT_POLICY, check_claims
from expensedesk.reconcile import reconcile
from expensedesk.report import to_excel
from expensedesk.tickets import SLA_HOURS, STATUSES, new_ticket, overdue, tickets_from_review

DATA = Path(__file__).parent / "data"
DOCS = Path(__file__).parent / "docs"

st.set_page_config(page_title="ExpenseDesk", page_icon=":receipt:", layout="wide")
st.markdown("""
<style>
.block-container {padding-top: 2rem;}
[data-testid="stMetricValue"] {font-size: 2rem;}
.pill {display:inline-block;padding:2px 10px;border-radius:12px;font-size:.8rem;font-weight:600;}
</style>""", unsafe_allow_html=True)

st.title("ExpenseDesk")
st.caption("Expense-claim policy checks, card statement reconciliation and request tracking for executive assistant support.")

# ---------------- data in ----------------
with st.sidebar:
    st.header("Data")
    use_sample = st.toggle("Use sample data", value=True)
    claims_file = stmt_file = None
    if not use_sample:
        claims_file = st.file_uploader("Expense claims (CSV)", type="csv")
        stmt_file = st.file_uploader("Card statement (CSV)", type="csv")
    st.header("Policy limits")
    caps = {k: st.number_input(k, value=float(v), step=5.0) for k, v in DEFAULT_POLICY.category_caps.items()}
    receipt_above = st.number_input("Receipt required above", value=DEFAULT_POLICY.receipt_required_above)
    within = st.number_input("Submit within (days)", value=DEFAULT_POLICY.submit_within_days, step=5)

if use_sample:
    claims = pd.read_csv(DATA / "sample_claims.csv")
    stmt = pd.read_csv(DATA / "sample_amex_statement.csv")
elif claims_file and stmt_file:
    claims, stmt = pd.read_csv(claims_file), pd.read_csv(stmt_file)
else:
    st.info("Upload both CSV files in the sidebar, or switch on sample data.")
    st.stop()

policy = type(DEFAULT_POLICY)(category_caps=caps, receipt_required_above=receipt_above, submit_within_days=int(within))
try:
    reviewed = check_claims(claims, policy)
except ValueError as e:
    st.error(str(e))
    st.stop()
matched, un_claims, un_stmt = reconcile(claims, stmt)

if "tickets" not in st.session_state or st.session_state.get("tickets_for") != (use_sample, len(claims)):
    st.session_state.tickets = tickets_from_review(reviewed)
    st.session_state.tickets_for = (use_sample, len(claims))
tickets = st.session_state.tickets

tab_dash, tab_review, tab_recon, tab_tix, tab_itin, tab_docs = st.tabs(
    ["Dashboard", "Claim review", "Card reconciliation", "Request queue", "Itinerary builder", "SOPs & process"])

# ---------------- dashboard ----------------
with tab_dash:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Claims", len(reviewed))
    c2.metric("Approved", int((reviewed["decision"] == "Approve").sum()))
    c3.metric("Needs review", int((reviewed["decision"] == "Needs Review").sum()))
    c4.metric("Rejected", int((reviewed["decision"] == "Reject").sum()))
    c5.metric("Unreconciled", len(un_claims) + len(un_stmt))
    left, right = st.columns(2)
    with left:
        st.subheader("Why claims were flagged")
        counts = pd.Series([c for f in reviewed["flags"] for c in f]).value_counts()
        if len(counts):
            st.bar_chart(counts)
        else:
            st.write("No flags.")
    with right:
        st.subheader("Spend by category")
        st.bar_chart(reviewed.groupby("category")["amount"].sum())
    st.download_button("Download full report (Excel)", to_excel(reviewed, matched, un_claims, un_stmt, tickets),
                       "expensedesk_report.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")

# ---------------- claim review ----------------
with tab_review:
    pick = st.multiselect("Decision", ["Approve", "Needs Review", "Reject"], default=["Needs Review", "Reject"])
    view = reviewed[reviewed["decision"].isin(pick)].copy()
    view["flags"] = view["flags"].apply(", ".join)
    st.dataframe(view[["claim_id", "employee", "expense_date", "category", "merchant", "amount", "decision", "flags", "reasons"]],
                 use_container_width=True, hide_index=True)
    st.caption("Every decision comes from a fixed policy rule, shown in the 'reasons' column, so it can be explained to the claimant.")

# ---------------- reconciliation ----------------
with tab_recon:
    a, b, c = st.columns(3)
    a.metric("Matched to statement", len(matched))
    b.metric("Claimed, not on statement", len(un_claims))
    c.metric("On statement, not claimed", len(un_stmt))
    st.subheader("Claimed but not on the card statement")
    st.dataframe(un_claims[["claim_id", "employee", "expense_date", "merchant", "amount"]], use_container_width=True, hide_index=True)
    st.subheader("On the statement but never claimed")
    st.dataframe(un_stmt, use_container_width=True, hide_index=True)
    with st.expander("Matched items"):
        st.dataframe(matched, use_container_width=True, hide_index=True)

# ---------------- ticket queue ----------------
with tab_tix:
    st.subheader("Request queue")
    with st.expander("Log an ad hoc request"):
        with st.form("new_req", clear_on_submit=True):
            who = st.text_input("Requester")
            what = st.text_input("Request")
            prio = st.selectbox("Priority", list(SLA_HOURS), index=1)
            if st.form_submit_button("Create ticket") and who and what:
                t = new_ticket(len(tickets) + 1, who, what, prio).to_dict()
                st.session_state.tickets = pd.concat([tickets, pd.DataFrame([t])], ignore_index=True)
                st.rerun()
    edited = st.data_editor(
        st.session_state.tickets, use_container_width=True, hide_index=True,
        disabled=[c for c in st.session_state.tickets.columns if c != "status"],
        column_config={"status": st.column_config.SelectboxColumn("status", options=STATUSES)})
    st.session_state.tickets = edited
    late = overdue(edited)
    if len(late):
        st.warning(f"{len(late)} ticket(s) past SLA")
    else:
        st.success("No tickets past SLA")
    st.caption("SLA targets: " + ", ".join(f"{k} {v}h" for k, v in SLA_HOURS.items()))

# ---------------- itinerary ----------------
with tab_itin:
    st.subheader("Travel itinerary builder")
    c1, c2 = st.columns(2)
    traveller = c1.text_input("Traveller", "S. Khan")
    title = c2.text_input("Trip", "Mumbai client visit")
    legs_df = st.data_editor(
        pd.DataFrame([{"date": date(2026, 10, 12), "time": time(9, 15), "mode": "Flight", "from": "Hyderabad", "to": "Mumbai", "ref": "6E 312"},
                      {"date": date(2026, 10, 14), "time": time(19, 40), "mode": "Flight", "from": "Mumbai", "to": "Hyderabad", "ref": "6E 521"}]),
        num_rows="dynamic", use_container_width=True)
    h1, h2, h3 = st.columns(3)
    hotel = {"name": h1.text_input("Hotel", "Marriott Mumbai"), "city": "Mumbai",
             "check_in": str(h2.date_input("Check-in", date(2026, 10, 12))),
             "check_out": str(h3.date_input("Check-out", date(2026, 10, 14))), "ref": "HTL-88213"}
    notes = st.text_area("Notes", "Airport cab pre-booked. Meeting at client office 11:30.")
    legs = [{**r, "date": str(r["date"]), "time": str(r["time"])[:5]} for r in legs_df.dropna(subset=["date"]).to_dict("records")]
    if legs:
        st.code(build_itinerary_text(traveller, title, legs, hotel, notes), language=None)
        st.download_button("Download itinerary (Word)", build_itinerary_docx(traveller, title, legs, hotel, notes),
                           "itinerary.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

# ---------------- docs ----------------
with tab_docs:
    for name in ["SOP_expense_claim_review.md", "SIPOC.md"]:
        p = DOCS / name
        if p.exists():
            st.markdown(p.read_text(encoding="utf-8"))
            st.divider()
