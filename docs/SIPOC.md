# SIPOC: Expense Claim Review and Card Reconciliation

| Suppliers | Inputs | Process | Outputs | Customers |
| --- | --- | --- | --- | --- |
| Executive Assistants (EAs) | Expense claims (CSV) | 1. Validate required fields | Approved claims list | Partners / Directors |
| Corporate card provider | Card statement (CSV) | 2. Check each claim against T&E policy | Flagged claims with plain-language reasons | EAs |
| Travel & Expense policy owner | Policy limits (caps, receipt rule, submission window) | 3. Reconcile claims to statement lines | Unreconciled items on both sides | Finance / Quality Assurance |
| Partners / Directors | Ad hoc requests | 4. Open tickets and set SLA by priority | Ticket queue with due times | EAs |
|  |  | 5. Resolve, record and file evidence | Excel report and updated ticket status | Team lead |

## Process map

```
Receive claims + statement
        |
Validate required fields --(missing)--> Return to EA
        |
Apply policy rules per claim
        |
   Clean? --yes--> Approve
        |no
  Duplicate? --yes--> Reject + ticket (High)
        |no
  Needs Review + ticket (Medium / High)
        |
Reconcile claims <-> card statement
        |
Chase unmatched items, update tickets
        |
Export report, file in team folder
```
