"""Deterministic demo data: expense claims plus a matching card statement with seeded problems."""
import random
from datetime import date, timedelta
import pandas as pd

EMPLOYEES = ["A. Menon", "R. Iyer", "S. Khan", "P. Nair", "D. Shah"]
MERCHANTS = {
    "Meals": ["Taj Cafe", "Starbucks", "Olive Bistro", "Barbeque Nation"],
    "Hotel": ["Marriott Hyderabad", "Hilton Bangalore", "Taj Vivanta"],
    "Taxi": ["Uber", "Ola Cabs"],
    "Airfare": ["IndiGo Airlines", "Air India"],
    "Train": ["IRCTC"],
    "Client Entertainment": ["Paradise Restaurant", "Social Club"],
}
RANGES = {"Meals": (12, 48), "Hotel": (110, 215), "Taxi": (8, 40), "Airfare": (150, 850),
          "Train": (20, 140), "Client Entertainment": (45, 115)}
STATEMENT_NAMES = {"Taj Cafe": "TAJ CAFE HYD", "Starbucks": "STARBUCKS #2231", "Uber": "UBER *TRIP",
                   "Ola Cabs": "OLA CABS", "IndiGo Airlines": "INDIGO AIR", "Air India": "AIR INDIA LTD"}


def generate(seed: int = 7, n: int = 40, today: date = date(2026, 9, 30)):
    rng = random.Random(seed)
    rows = []
    for i in range(1, n + 1):
        cat = rng.choice(list(MERCHANTS))
        lo, hi = RANGES[cat]
        spent = today - timedelta(days=rng.randint(3, 40))
        rows.append({"claim_id": f"CLM{i:04d}", "employee": rng.choice(EMPLOYEES), "expense_date": spent,
                     "submitted_date": spent + timedelta(days=rng.randint(1, 10)), "category": cat,
                     "merchant": rng.choice(MERCHANTS[cat]), "amount": round(rng.uniform(lo, hi), 2),
                     "receipt": "Y", "description": f"{cat} for client visit"})
    claims = pd.DataFrame(rows)

    # seeded problems the tool must catch
    claims.loc[2, ["category", "amount", "merchant"]] = ["Meals", 96.50, "Olive Bistro"]          # over limit
    claims.loc[5, ["amount", "receipt"]] = [78.00, "N"]                                           # missing receipt
    claims.loc[9, "description"] = "Team dinner with wine"                                        # non-reimbursable
    claims.loc[14, "submitted_date"] = claims.loc[14, "expense_date"] + timedelta(days=95)        # late
    claims = pd.concat([claims, claims.iloc[[20]].assign(claim_id="CLM0041")], ignore_index=True)  # duplicate

    stmt = []
    for _, c in claims.iterrows():
        if c["claim_id"] in {"CLM0007", "CLM0013"}:   # claimed but not on the card statement
            continue
        name = STATEMENT_NAMES.get(c["merchant"], c["merchant"].upper())
        stmt.append({"txn_date": c["expense_date"] + timedelta(days=rng.randint(0, 2)),
                     "merchant": name, "amount": c["amount"]})
    stmt += [{"txn_date": today - timedelta(days=11), "merchant": "AMAZON MKTPLACE", "amount": 63.40},   # unclaimed
             {"txn_date": today - timedelta(days=6), "merchant": "UBER *TRIP", "amount": 27.15}]
    stmt = pd.DataFrame(stmt).sort_values("txn_date").reset_index(drop=True)
    stmt.insert(0, "txn_id", [f"AMX{i:04d}" for i in range(1, len(stmt) + 1)])
    return claims, stmt


if __name__ == "__main__":
    c, s = generate()
    c.to_csv("data/sample_claims.csv", index=False)
    s.to_csv("data/sample_amex_statement.csv", index=False)
    print(f"Wrote {len(c)} claims and {len(s)} statement lines to data/")
