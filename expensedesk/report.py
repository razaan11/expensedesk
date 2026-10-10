"""Excel export of the review and reconciliation results."""
from io import BytesIO
import pandas as pd


def to_excel(reviewed, matched, unmatched_claims, unmatched_stmt, tickets) -> bytes:
    buf = BytesIO()
    r = reviewed.copy()
    r["flags"] = r["flags"].apply(lambda f: ", ".join(f))
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        r.to_excel(xw, sheet_name="Claim Review", index=False)
        matched.to_excel(xw, sheet_name="Matched", index=False)
        unmatched_claims.to_excel(xw, sheet_name="Claims not on statement", index=False)
        unmatched_stmt.to_excel(xw, sheet_name="Statement not claimed", index=False)
        tickets.to_excel(xw, sheet_name="Tickets", index=False)
        for ws in xw.book.worksheets:
            ws.freeze_panes = "A2"
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width = min(
                    60, max(len(str(c.value)) if c.value is not None else 0 for c in col) + 2)
    return buf.getvalue()
