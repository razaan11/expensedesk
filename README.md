# ExpenseDesk

Expense-claim policy checks, corporate card reconciliation and a request queue, built for executive assistant support work.

Executive assistants submit claims for partners and directors. Someone has to check each claim against the Travel & Expense policy, match claims to the card statement, chase what is missing and track every request. ExpenseDesk does that in one place and explains every decision in plain language.

## What it does

| Feature | What you get |
| --- | --- |
| **Policy check** | Category caps, receipt rule, late submission, duplicate claims and non-reimbursable items. Each flag has a written reason. |
| **Card reconciliation** | Matches claims to statement lines by amount, date window and merchant similarity. Lists claims not on the statement and statement lines nobody claimed. |
| **Request queue** | Opens a ticket for every flagged claim with a priority and SLA due time. Log ad hoc requests, update status, see overdue tickets. |
| **Itinerary builder** | Turns trip legs and hotel details into a clean itinerary, downloadable as Word. |
| **Excel report** | One workbook with review, matches, gaps and tickets. |
| **SOP and SIPOC** | Written procedure and process map in `docs/`. |

Decisions come from fixed, visible rules, not a model, so every result can be explained to the claimant.

## Run it

```bash
pip install -r requirements.txt
python -m expensedesk.sample_data   # optional: regenerate demo data
streamlit run app.py
```

Open http://localhost:8501. Sample data is loaded by default. To use your own, turn off *Use sample data* and upload two CSVs:

- **Claims:** `claim_id, employee, expense_date, submitted_date, category, merchant, amount, receipt, description`
- **Statement:** `txn_id, txn_date, merchant, amount`

## Demo data

The sample data has 41 claims with known problems so you can see each rule fire: one over-limit meal, one missing receipt, one non-reimbursable item, one late submission and one duplicate. Two claims are not on the card statement and two statement lines were never claimed.

## Tests

```bash
python -m pytest
```

11 tests cover each policy rule, reconciliation matching, ticket priority and SLA, itinerary output and the seeded demo data.

## Project layout

```
app.py                  Streamlit interface
expensedesk/policy.py   T&E policy rules
expensedesk/reconcile.py  Claim to statement matching
expensedesk/tickets.py  Ticket queue and SLA
expensedesk/itinerary.py  Itinerary text and Word export
expensedesk/report.py   Excel export
docs/                   SOP and SIPOC
tests/                  pytest suite
```

## Tech

Python, pandas, Streamlit, RapidFuzz, openpyxl, python-docx, pytest.
