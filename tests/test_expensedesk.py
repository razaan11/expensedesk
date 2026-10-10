from datetime import datetime
import pandas as pd
import pytest

from expensedesk.policy import check_claims
from expensedesk.reconcile import reconcile
from expensedesk.tickets import tickets_from_review, priority_for, overdue
from expensedesk.itinerary import build_itinerary_text, build_itinerary_docx
from expensedesk.sample_data import generate


def claim(**kw):
    base = dict(claim_id="C1", employee="A", expense_date="2026-09-01", submitted_date="2026-09-03",
                category="Meals", merchant="Taj Cafe", amount=30.0, receipt="Y", description="lunch")
    base.update(kw)
    return base


def review(*rows):
    return check_claims(pd.DataFrame(list(rows)))


def test_clean_claim_is_approved():
    assert review(claim()).loc[0, "decision"] == "Approve"


def test_over_limit_needs_review():
    r = review(claim(amount=96.5)).loc[0]
    assert "OVER_LIMIT" in r["flags"] and r["decision"] == "Needs Review"


def test_missing_receipt_only_above_threshold():
    assert "MISSING_RECEIPT" in review(claim(amount=40, receipt="N")).loc[0, "flags"]
    assert review(claim(amount=20, receipt="N")).loc[0, "flags"] == []


def test_duplicate_is_rejected():
    r = review(claim(), claim(claim_id="C2"))
    assert r.loc[0, "decision"] == "Approve"
    assert r.loc[1, "decision"] == "Reject" and "DUPLICATE" in r.loc[1, "flags"]


def test_late_and_non_reimbursable():
    r = review(claim(submitted_date="2026-12-15"), claim(claim_id="C2", merchant="Bar", description="wine"))
    assert "LATE_SUBMISSION" in r.loc[0, "flags"]
    assert "NON_REIMBURSABLE" in r.loc[1, "flags"]


def test_missing_columns_raise():
    with pytest.raises(ValueError):
        check_claims(pd.DataFrame({"claim_id": ["x"]}))


def test_reconcile_matches_and_finds_gaps():
    claims = pd.DataFrame([claim(), claim(claim_id="C2", amount=55.0, merchant="Uber")])
    stmt = pd.DataFrame([
        {"txn_id": "T1", "txn_date": "2026-09-02", "merchant": "TAJ CAFE HYD", "amount": 30.0},
        {"txn_id": "T2", "txn_date": "2026-09-05", "merchant": "AMAZON", "amount": 12.0}])
    matched, un_claims, un_stmt = reconcile(claims, stmt)
    assert list(matched["claim_id"]) == ["C1"]
    assert list(un_claims["claim_id"]) == ["C2"]
    assert list(un_stmt["txn_id"]) == ["T2"]


def test_statement_line_used_once():
    claims = pd.DataFrame([claim(), claim(claim_id="C2")])
    stmt = pd.DataFrame([{"txn_id": "T1", "txn_date": "2026-09-01", "merchant": "Taj Cafe", "amount": 30.0}])
    matched, un_claims, _ = reconcile(claims, stmt)
    assert len(matched) == 1 and len(un_claims) == 1


def test_priority_and_sla():
    assert priority_for(["DUPLICATE"]) == "High"
    assert priority_for(["OVER_LIMIT"]) == "Medium"
    reviewed = review(claim(amount=96.5))
    t = tickets_from_review(reviewed, now=datetime(2026, 9, 10, 9, 0))
    assert t.loc[0, "ticket_id"] == "REQ00001" and t.loc[0, "due"] == "2026-09-10 17:00"
    assert len(overdue(t, now=datetime(2026, 9, 10, 18, 0))) == 1
    assert len(overdue(t, now=datetime(2026, 9, 10, 12, 0))) == 0


def test_itinerary_outputs():
    legs = [{"date": "2026-10-12", "time": "09:15", "mode": "Flight", "from": "HYD", "to": "BOM", "ref": "6E 312"},
            {"date": "2026-10-11", "time": "18:00", "mode": "Cab", "from": "Office", "to": "HYD"}]
    text = build_itinerary_text("S. Khan", "Mumbai client visit", legs)
    assert text.index("2026-10-11") < text.index("2026-10-12")
    assert build_itinerary_docx("S. Khan", "Mumbai client visit", legs)[:2] == b"PK"


def test_sample_data_seeded_issues_are_caught():
    claims, stmt = generate()
    r = check_claims(claims)
    codes = {c for f in r["flags"] for c in f}
    assert {"OVER_LIMIT", "MISSING_RECEIPT", "NON_REIMBURSABLE", "LATE_SUBMISSION", "DUPLICATE"} <= codes
    matched, un_claims, un_stmt = reconcile(claims, stmt)
    assert set(un_claims["claim_id"]) == {"CLM0007", "CLM0013"}
    assert len(un_stmt) == 2
