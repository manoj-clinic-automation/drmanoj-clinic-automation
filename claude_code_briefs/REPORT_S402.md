# REPORT S402_SALECHECK_RETURNS — Bhati sees the day's sale returns at a glance

Written 25-Sep-2026 by Claude Code (kit S402, on top of S400). All times IST, read from the box.

## For the owner
- In Bhati's **Medical sale check**, a day now shows one line right after the Marg bills: **Sale return — 3 · ₹1,240**. Closed by
  default; a tap opens one row per return — bill number, the name as the system shows it, the amount. Nothing more. A day with no
  return reads `Sale return — 0` and does not open.
- On each day's card in his list, the same figure in one short line — `Sale return 3 · ₹1,240` — so he sees it without opening the day;
  the line is left out when there are none.
- The numbers are the very same the day panel on your approvals page uses (that day's credit notes). Nothing else changed: no new
  entry, no change to your pages or to who can see what.
- Installed on the server at 21:16 IST; its test passed 16 of 16 on a copy of the live data, and S400's own 63-check test was re-run on
  the changed files and stayed green. `https://followup.dr-manoj.in/finance/salecheck`

## For the chat
### Live files — FROM → TO, md5 read back on the box after placing (installer output, 21:16 IST)
| file | FROM (S400; matched on the box at 21:11 IST) | TO (read back) |
|---|---|---|
| /root/finance/sale_check.py (v1.0 → v1.1) | 81cccad3c48a894298b3694a7b3b5118 | 92ca5cb2d3a4388bbf6a29e35af2d492 |
| /root/finance/sale_check.html | 4202d11baee4c9309a518e3aed8cf817 | 9c70af26456092285a9545083365bfff |

Only these two were touched (`finance_app.py` read back unchanged at d7ee72c5). Both were built ON THE BOX from the live bytes
by `make_s402.py` (four anchored edits in the .py, four in the .html, each anchor exactly once) and compared with the kit's pins
before the walk. S401 (slips) was not running when this started (no installer process; clinic-finance last restarted 20:46:19 by S400).

### What changed in the code
- `sale_check.py` `day_payload`: a return row is `{bill, name, amount}` with `amount = rs(abs(amount_p))` (positive, whole rupees) —
  the `items` list S400 attached to returns is gone; `day_lines` (the list card) gains `returns={count, total}` from the owner's
  `day_view` figures (`sale_bill.is_credit_note` of that day).
- `sale_check.html`: the S400 `− Sale return` line in the day's sum card is replaced by `retBlock()` — `− Sale return — N`, collapsed;
  tap → a table of bill · name · amount; N = 0 does not expand. The card gets `Sale return N · ₹T` when N > 0. Header stamp `S402_SALECHECK_RETURNS`.

### Data and services
- `finance.db.bak_S402_20260925_211558` (backup API, by rule 6) — nothing in the database changes with this kit; no new table, no new write.
- Backups beside the files: `sale_check.py.bak_S402_81cccad3`, `sale_check.html.bak_S402_4202d11b`.
- Restarted: `clinic-finance` only. After: active, `/finance/healthz` 200 (local and public), `/finance/salecheck` without a login 302
  (the login gate — expected), no "NOT mounted" in the journal.

### The walk (`walk_s402.py`, 16 checks — the installer's run at 21:16 IST, scratch copy of the live database, own rows 2099-12-05/06 found by key)
```
-- own rows planted: 2099-12-05 (sale 1,500; two credit notes 300 + 200) · 2099-12-06 (no return) · real unapproved day 2026-09-24
-- 1  the day's returns block
  ok   sale_check v1.1 answers; the walk day reads Sale return count 2, total 500
  ok   expanded: exactly bill no · name · amount per return, amounts positive, whole rupees   [W402C001 300 · W402C002 200]
  ok   no item fields for returns although a medicine line exists on W402C001
  ok   the sale side of the same day is unchanged: 1 Marg bill, 1,500, its cash received 1,000
  ok   a day with no return: count 0, total 0, no rows
-- 2  the card line
  ok   the card carries returns {count 2, total 500} -- the same figures as the block
  ok   the 0 day's card carries count 0 (the page omits the line)
  ok   the page carries the block, the words 'Sale return' and the S402 stamp
-- 3  the same figures as the owner's day panel
  ok   the walk day: the owner's panel reads returns count 2, total 500 -- equal to Bhati's
  ok   the real unapproved day 2026-09-24: Bhati's count/total == the owner's panel's (0 · 0)
  ok   the real day's rows are bill · name · amount only, one per credit note
-- 4  access unchanged
  ok   bhati is still refused on every S400 §6 address   [all 302]
  ok   darpan, bhawna, shavez, a stranger still cannot open the page   [all 302]
-- 5  negative control: the box as it is (S400)
  ok   NEGATIVE CONTROL: S400's day view carries item fields on a return row (the block did not exist)   [v1.0]
  ok   NEGATIVE CONTROL: S400's card has no returns line
  ok   NEGATIVE CONTROL: S400's page has no retBlock / S402 stamp
WALK_S402 GREEN -- 16/16
```
Then **S400's own walk re-run** (`walk_s400.py`, 63 checks) on the patched files, against a rebuilt pre-S400 control (the `.bak_S400_*`
files): `WALK_S400 GREEN -- 63/63` — every S400 behaviour (gate, flags, Sahi/Galti, the cash path, the owner's side, the tile) holds.

**Negative control:** the same probes against a copy of the box as it was (S400 files): a return row carries `items`, the card has no
`returns`, the page has no `retBlock` — the three NEGATIVE CONTROL checks pass only because S400 fails them.

### Noted, honestly
- The real unapproved day the walk found (the latest, 2026-09-24) has **no credit note**, so the "same as the owner's panel" check on
  real data proved 0 = 0 there; the crafted day proved the arithmetic with two credit notes (300 + 200 = 500, positive, one row each).
- The name shown on a return row is the same `name · #clinic-id` text the owner's panel shows for that bill — as the brief asked.

### Not done / outside the brief
- Nothing in the brief is left out. No other file, no data, no portal or grants change.

### Publish and the repo-copy check (read from the box)
- Journal after the 21:16:03 restart: no error, traceback or "NOT mounted" line (count 0 at 21:16:29). Both services active.
- The installer was run from `/tmp/s402stage/S402_SALECHECK_RETURNS/` (SUMS.md5 checked OK there first; the S400 kit copied beside it
  for its walk) at 21:15:58 IST.
- `PUBLISH_ALL.bat`: gate clean (8 staged files: the kit, this report, the brief), commit `eb2719f`, pushed, origin HEAD verified.
- On the box at 21:17:22 IST: `/root/deploy/repo` pulled to `eb2719f`; `md5sum -c SUMS.md5` OK in the repo kit; all 6 kit files
  `cmp`-identical to the copy that ran; both live files still at their TO pins; the repo installer's re-run took its ALREADY INSTALLED
  path (rc 0, nothing changed); healthz 200 at 21:17:23. `/tmp/s402stage` removed.
