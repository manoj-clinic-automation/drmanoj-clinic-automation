# S195 — LIVE PINS (end of 22-Aug-2026 morning)

| file | live md5 | smoke |
|---|---|---|
| `/root/finance/finance_app.py` | **`df75024392e31ae99bb3fde9fab24062`** | **654/654** |
| `/root/portal/portal.py` | `ff08980737c107c3babb78b0c5c169c2` | portal gate 26/26 |
| `/root/deploy/email_agent.py` | `e535c4f8116abd2fe60b7fda334f33ec` | SELFTEST OK |
| `gas/VPS_Push_UPI.gs` (project "UPI Reconciliation", clinic account) | `fac84c5b4a5a14b6345d4cce52c1ad39` | backfill Complete |

Backups: `_backup_S195_SIGN_20260822_102952`, `_backup_S195_CLUB2_20260822_085359`.

### Pin history, 22-Aug

| pin | smoke | kit |
|---|---|---|
| `e3a4ba79…` | 573 | health tile (session start) |
| `8c7dc966…` | 613 | A123D — drawer checks + the correction checklist |
| `3e2f707b…` | 637 | SHARE — Excel / WhatsApp / email handover |
| `af617bf0…` | 648 | CLUB2 — tile accuracy · email subjects · the month check |
| **`df750243…`** | **654** | SIGN — the credit-note sign in one place |

Five installs, five rollbacks avoided or recovered cleanly; the service stayed up throughout.

---

## What is live that was not, this morning

- **The correction checklist** — `/finance/marg-worklist`, self-closing, floored at
  `FINANCE_CORRECTION_FROM=2026-08-01`, with Excel / WhatsApp / email / CSV handover.
- **Darpan's accuracy** on his own portal tile and in his own save response.
- **The email agent** recovers folded and RFC2047-encoded subjects — every command longer
  than ~75 characters used to arrive corrupted.
- **The month check** — `/finance/api/marg-month`, plus the never-filed days on the health
  page.
- **`marg_net_sql()`** — one signed-net expression for all three readers.
- **The bank can see 56 days instead of 8** (medical; clinic 55, lab 50, back to 06-Jun).

## Where the books stand

- **18-Aug: corrected and approved at 25,176.** The applied export had been partial (22 of
  30 bills). A fresh export, validated by the guard, confirmed 30 bills / NET 25,176.
- **20-Aug: approved.**
- Cash/UPI split, now that the bank can judge it: **8 disagreements across ~56 checkable
  days, exactly one since 1-Aug — ₹30 on 06-Aug.** Darpan's morning split is being done well.

## Still owed

1. **Rotate `FINANCE_MARG_TOKEN` and `FINANCE_CRON_TOKEN`** (the cron token also lives in the
   GAS Script Properties). Both were printed in plain text during the 401 crisis.
2. **17-Aug ₹20,000 → Staff Ledger.** Until then the drawer will not read 175,201 — that
   figure is `193,904 + 1,297 − 20,000`, and only the first of those two corrections is done.
3. **8 bills, ₹4,577, in the review queue for 18-Aug** — patient attribution only, money
   unaffected. `/finance/approvals` → 18-Aug.
4. Club 3 (Marg report signatures — needs one sample each) and Club 4 (the three email
   questions, of which *how Amir gets a file onto the medical PC* unblocks the most).

## The lesson of the day, stated once

Five rollbacks, and behind all of them one habit: **asserting against shapes I had not
looked at.** An invented fixture (`diff_p`), a guessed JSON body (the workbench cross-check),
a search string that matched itself, a scratch variable that collided with one forty lines
above, a diagnosis of "Gmail encodes long subjects" that turned out to be folding instead.
Reading the code did not catch any of them; printing the actual shape caught every one.

And the larger one, from 18-Aug itself: a screen said 23,879 and a piece of paper written by
the man who counted the money said 25,176. I stopped the correction on the screen's word.
The screen was wrong — and it was *more* convincing because its wrong figure landed exactly
on another wrong figure. **Where a hand-written record and a computed one disagree,
regenerate from source before believing the computation.** Ninety seconds of re-export
settled what an hour of reasoning had got backwards.
