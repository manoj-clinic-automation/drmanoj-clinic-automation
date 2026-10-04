# S475_YES_INTEREST_ROW -- session 293, 04-Oct-2026 -- F-720

**What was wrong.** On 04-Oct the statement shelf refused the branch's September statements of two Yes Bank savings
accounts: *a row dated 2026-10-01 falls outside the printed period 2026-09-01 to 2026-09-30*. The row is the bank's own
quarter-end interest -- `CREDIT INTEREST CAPITALISED ON SB A/C`, TXN DATE 01-OCT-2026, VALUE DATE 30-SEP-2026 -- which the
bank counts inside September's totals. Every arithmetic proof had passed; only the date check, which looked at the txn
date alone, refused the file. Both Yes Bank readers (the branch layout, the e-statement PDF) carry the same check.

**The rule now.** A row is inside the printed period when its value date **or** its txn date is. Nothing accepted before is
refused now; a row whose both dates fall outside is refused as before, and the message names both dates.

| file | from | to |
|---|---|---|
| `/root/finance/yes_branch.py` | `378539d9` | `fec5c520` |
| `/root/finance/finance_yesbank.py` | `5a088cd9` | `3509f728` |

**Then, on the box only:** the shelf rows carrying that refusal are given back to the reader (their `read_status`
cleared; the slot stays) and the shelf is run once (`stmt_shelf.py run`, as the 05:40 cron runs it), so the two
statements are read today. The installer prints each row before and the Yes Bank rows of September after.

**Walk** (`walk_s475.py`, hermetic): made-up statement text in each layout; SHOWN refused on the old readers, read on the
new; both-dates-outside still refused; a missing value date judged by the txn date; the arithmetic proofs refuse exactly
as before; the CSV path untouched. 26 checks.

**Install (one line, the owner's):**
`cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S475_YES_INTEREST_ROW/install_S475_YES_INTEREST_ROW.sh`
`DRY=1` runs every gate and the walk and places nothing. Restarts clinic-finance (~8 s). Needs the build lock free (F-694).
