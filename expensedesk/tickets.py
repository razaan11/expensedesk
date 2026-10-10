"""Request / ticket queue with priorities and SLA due times (ServiceNow-style)."""
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import pandas as pd

SLA_HOURS = {"High": 4, "Medium": 8, "Low": 24}
HIGH_FLAGS = {"DUPLICATE", "NON_REIMBURSABLE"}
MEDIUM_FLAGS = {"OVER_LIMIT", "MISSING_RECEIPT", "LATE_SUBMISSION", "FUTURE_DATED", "INVALID_AMOUNT"}
STATUSES = ["New", "In Progress", "Waiting on EA", "Resolved"]
COLUMNS = ["ticket_id", "requester", "summary", "priority", "status", "created", "due", "related_claim"]


@dataclass
class Ticket:
    ticket_id: str
    requester: str
    summary: str
    priority: str
    status: str
    created: datetime
    due: datetime
    related_claim: str = ""

    def to_dict(self):
        d = asdict(self)
        d["created"] = self.created.strftime("%Y-%m-%d %H:%M")
        d["due"] = self.due.strftime("%Y-%m-%d %H:%M")
        return d


def priority_for(flags) -> str:
    f = set(flags)
    if f & HIGH_FLAGS:
        return "High"
    return "Medium" if f & MEDIUM_FLAGS else "Low"


def new_ticket(n: int, requester: str, summary: str, priority: str, related_claim: str = "",
               now: datetime | None = None) -> Ticket:
    now = now or datetime.now()
    return Ticket(f"REQ{n:05d}", requester, summary, priority, "New", now,
                  now + timedelta(hours=SLA_HOURS[priority]), related_claim)


def tickets_from_review(reviewed: pd.DataFrame, start: int = 1, now: datetime | None = None) -> pd.DataFrame:
    """Open one ticket per claim that needs review or was rejected."""
    rows, n = [], start
    for _, r in reviewed[reviewed["decision"] != "Approve"].iterrows():
        t = new_ticket(n, r["employee"], f"{r['decision']}: {r['reasons']}", priority_for(r["flags"]),
                       r["claim_id"], now)
        rows.append(t.to_dict())
        n += 1
    return pd.DataFrame(rows, columns=COLUMNS)


def overdue(tickets: pd.DataFrame, now: datetime | None = None) -> pd.DataFrame:
    now = now or datetime.now()
    due = pd.to_datetime(tickets["due"])
    return tickets[(due < now) & (tickets["status"] != "Resolved")]
