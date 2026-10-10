# SOP: Expense Claim Review

**Purpose:** Review expense claims against the Travel & Expense policy consistently and quickly.
**Scope:** Claims submitted by Executive Assistants on behalf of partners and directors.

## Steps
1. **Load data.** Upload the claims CSV and the card statement CSV, or use the sample data.
2. **Check policy limits.** Confirm the limits in the sidebar match the current policy.
3. **Review flagged claims.** Open *Claim review*. Each flag has a reason in plain language.
4. **Decide.**
   - *Approve*: no flags.
   - *Needs Review*: over limit, missing receipt, late submission, non-reimbursable item. Ask the EA for the missing item.
   - *Reject*: duplicate claim. Tell the EA why.
5. **Reconcile.** Open *Card reconciliation*. Chase claims that are not on the statement and statement lines nobody claimed.
6. **Track.** Every non-approved claim opens a ticket. Set status to *Waiting on EA* when you are waiting for a reply.
7. **Close.** Mark tickets *Resolved*, download the Excel report and file it in the team folder.

## Priority and service levels
| Priority | Triggers | Target |
| --- | --- | --- |
| High | Duplicate, non-reimbursable item | 4 hours |
| Medium | Over limit, missing receipt, late, invalid amount | 8 hours |
| Low | Everything else | 24 hours |

## Quality checks
- Never approve a claim that has an open flag.
- Keep a written reason for every rejection.
- File the report and EA correspondence in the designated team folder.
