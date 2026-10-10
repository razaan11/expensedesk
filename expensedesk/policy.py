"""Travel & Expense policy engine.

Every rule is a plain, visible check so a reviewer can see exactly why a claim
was flagged. Nothing here is a black box.
"""
from dataclasses import dataclass, field
import pandas as pd

REQUIRED_COLUMNS = ["claim_id", "employee", "expense_date", "submitted_date", "category",
                    "merchant", "amount", "receipt", "description"]


@dataclass(frozen=True)
class Policy:
    category_caps: dict = field(default_factory=lambda: {
        "Meals": 50.0, "Hotel": 220.0, "Taxi": 45.0, "Airfare": 900.0,
        "Train": 150.0, "Client Entertainment": 120.0, "Other": 100.0})
    receipt_required_above: float = 25.0
    submit_within_days: int = 60
    blocked_keywords: tuple = ("alcohol", "wine", "beer", "cocktail", "personal", "gift card")


DEFAULT_POLICY = Policy()

REJECT_CODES = {"DUPLICATE"}


def check_claims(df: pd.DataFrame, policy: Policy = DEFAULT_POLICY) -> pd.DataFrame:
    """Return the claims with `flags` (list of codes), `reasons` and `decision` columns."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    out = df.copy()
    out["expense_date"] = pd.to_datetime(out["expense_date"])
    out["submitted_date"] = pd.to_datetime(out["submitted_date"])
    dup_key = out.duplicated(subset=["employee", "expense_date", "merchant", "amount"], keep="first")

    flags_col, reasons_col = [], []
    for idx, r in out.iterrows():
        flags, reasons = [], []

        def flag(code, why):
            flags.append(code)
            reasons.append(why)

        if dup_key.loc[idx]:
            flag("DUPLICATE", "Same employee, date, merchant and amount already claimed")
        if r["amount"] <= 0:
            flag("INVALID_AMOUNT", f"Amount {r['amount']} is not positive")
        cap = policy.category_caps.get(r["category"])
        if cap is None:
            flag("UNKNOWN_CATEGORY", f"Category '{r['category']}' is not in policy")
        elif r["amount"] > cap:
            flag("OVER_LIMIT", f"{r['category']} claim {r['amount']:.2f} exceeds cap {cap:.2f}")
        if r["amount"] > policy.receipt_required_above and str(r["receipt"]).upper() != "Y":
            flag("MISSING_RECEIPT", f"Receipt required above {policy.receipt_required_above:.0f}")
        age = (r["submitted_date"] - r["expense_date"]).days
        if age > policy.submit_within_days:
            flag("LATE_SUBMISSION", f"Submitted {age} days after expense (limit {policy.submit_within_days})")
        if age < 0:
            flag("FUTURE_DATED", "Expense date is after the submission date")
        text = f"{r['description']} {r['merchant']}".lower()
        hit = [k for k in policy.blocked_keywords if k in text]
        if hit:
            flag("NON_REIMBURSABLE", f"Contains non-reimbursable item: {', '.join(hit)}")

        flags_col.append(flags)
        reasons_col.append("; ".join(reasons))

    out["flags"] = flags_col
    out["reasons"] = reasons_col
    out["decision"] = [
        "Reject" if set(f) & REJECT_CODES else ("Needs Review" if f else "Approve") for f in flags_col
    ]
    return out
