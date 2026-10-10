"""Match expense claims to corporate card (e.g. Amex) statement lines."""
import pandas as pd
from rapidfuzz import fuzz

DATE_WINDOW_DAYS = 3
MIN_MERCHANT_SCORE = 60


def reconcile(claims: pd.DataFrame, statement: pd.DataFrame):
    """Return (matched, unmatched_claims, unmatched_statement).

    A claim matches a statement line when the amount agrees to the cent, the
    dates are within DATE_WINDOW_DAYS and the merchant names are similar.
    Each statement line is used at most once.
    """
    claims = claims.copy()
    stmt = statement.copy()
    claims["expense_date"] = pd.to_datetime(claims["expense_date"])
    stmt["txn_date"] = pd.to_datetime(stmt["txn_date"])

    used, matches = set(), []
    for _, c in claims.iterrows():
        best = None
        for si, s in stmt.iterrows():
            if si in used or abs(c["amount"] - s["amount"]) > 0.01:
                continue
            gap = abs((c["expense_date"] - s["txn_date"]).days)
            if gap > DATE_WINDOW_DAYS:
                continue
            score = fuzz.token_set_ratio(str(c["merchant"]).lower(), str(s["merchant"]).lower())
            if score < MIN_MERCHANT_SCORE:
                continue
            rank = (score, -gap)
            if best is None or rank > best[0]:
                best = (rank, si, score, gap)
        if best:
            used.add(best[1])
            matches.append({"claim_id": c["claim_id"], "txn_id": stmt.loc[best[1], "txn_id"],
                            "employee": c["employee"], "amount": c["amount"],
                            "claim_merchant": c["merchant"],
                            "statement_merchant": stmt.loc[best[1], "merchant"],
                            "merchant_score": round(best[2]), "date_gap_days": best[3]})

    matched = pd.DataFrame(matches, columns=["claim_id", "txn_id", "employee", "amount", "claim_merchant",
                                             "statement_merchant", "merchant_score", "date_gap_days"])
    unmatched_claims = claims[~claims["claim_id"].isin(matched["claim_id"])]
    unmatched_stmt = stmt[~stmt["txn_id"].isin(matched["txn_id"])]
    return matched, unmatched_claims, unmatched_stmt
