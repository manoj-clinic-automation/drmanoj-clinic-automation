# Claude Code brief — S402_SALECHECK_RETURNS (Bhati sees the day's sale returns at a glance)

Written 25-Sep-2026 by the Sanjeevni chat (S283). Read `CLAUDE.md` first — every rule binds. **Kit number S402** (claimed on
the System Board). The owner has approved this WHAT. Build → test on a copy → install → verify → publish → report, in one run.
It builds on S400 (live since 20:45 IST 25-Sep); read `claude_code_briefs\REPORT_S400.md` and `deploy_kits\S400_MEDICAL_SALE_CHECK\` first.

## What the owner wants, in his words
"Bhati should also be seeing the sales returns of the day populated in his app so that he can easily have a glance at the
total sale returns. They should come as collapsible, expandable: sale returns, their number, their total amount; expand to
the bill number, name, and amount. More granular details are not required in Bhati's app."

## The change (Bhati's page only; the label is the English words "Sale return", owner's ruling 25-Sep -- never "Vaapsi")
1. **In a day** (`Medical sale check` → a day): one block, **collapsed by default**, placed right after the Marg bills:
   `Sale return — 3 · ₹1,240` → tap → one row per return: **bill no. · name as the system shows it · amount**.
   Nothing more: **no medicine lines, batch, expiry, quantity or item detail** for returns (replace whatever S400 shows for
   returns in the day view with this block, so returns appear once). A day with no returns shows `Sale return — 0` and does not
   expand. Amounts in whole rupees, Indian grouping, the same figures the owner's day panel uses (credit notes of that day,
   `sale_bill.is_credit_note`, amount shown positive).
2. **On the day's card in the list:** one short line `Sale return 3 · ₹1,240` (omitted when 0), so he sees it without opening.
3. Nothing else changes: no new write, no new table, no change to the owner's pages, his access or anyone else's.

## FROM pins (read the live md5 first; mismatch = stop and report)
| file | FROM |
|---|---|
| /root/finance/sale_check.py | 81cccad3c48a894298b3694a7b3b5118 |
| /root/finance/sale_check.html | 4202d11baee4c9309a518e3aed8cf817 |
Touch only these two. Restart `clinic-finance` only if `sale_check.py` changes. No `finance_app.py`, portal or grants change.

## The walk (scratch copy of the live DB, own rows dated 2099-12-xx found by key; S400's walk re-run must stay green)
A walk day with 2 credit notes: the block reads count 2 and the right total; expanded it carries exactly bill no, name,
amount for each and **no item fields** · a day with 0 returns shows 0 and no rows · the card line matches the block and is
absent on a 0 day · the total equals the owner's day panel's returns total for the same day · a real unapproved day
(2026-09-23 or 24) shows the same count/total as `/finance/sanjeevni/api/day/<iso>` · Bhati's access unchanged (every S400 §6
refusal still holds) · **negative control:** the S400 files give no returns block / no card line.

## Done means
Kit `deploy_kits\S402_SALECHECK_RETURNS\` · installed, md5s read back · healthz 200 · published with `PUBLISH_ALL.bat` ·
`claude_code_briefs\REPORT_S402.md` (owner lines first, ending with `https://followup.dr-manoj.in/finance/salecheck`).
If the clinic chat's kit S401 (slips) is mid-install when you start, wait for it to finish; it touches none of these files.
