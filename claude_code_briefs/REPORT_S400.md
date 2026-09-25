# REPORT S400_MEDICAL_SALE_CHECK — Bhati checks the pharmacy days

Written 25-Sep-2026 by Claude Code (kit S400, decision D616). All times IST, read from the box.

## For the owner
- Bhati has a new tile, **Medical sale check**. It lists the Sanjeevni days not yet approved, oldest first, with red lines
  where something is off (Darpan wrote no handover · handover ≠ cash received, with the difference · Marg sheet not in ·
  a bill with no name · a Home/Procedure bill not deducted). A day opens to its Marg bills (tap → medicines), returns, UPI
  from the bank, Home/Procedure medicine and **Cash received** — the same figures your day panel shows, nothing else.
- He taps **Sahi hai**, or **Galti hai** and picks the bill and the problem from two drop-downs (a note only for "Aur kuch").
  He types **one amount** — the cash Darpan handed — Dr Bhawna by default, one tap for you; the date is the sale date. It
  lands in the same cash record Darpan's own entry uses, so your cash arithmetic is unchanged. A big green card says what
  was saved; a repeat does not save twice.
- On your approvals page each day now carries one small line — `Bhati ✓ 09:40` or `Bhati: 2 mistakes` (tap → the list) — and his
  cash entry, with Darpan's figure in red if they differ; you can change the person or move the date there. **Needs you**
  says "Bhati found mistakes on N day(s)". Everything else on your page is exactly as before, and you can still do all of
  it yourself when Bhati is absent. Bhati sees no month, no bank, no other cash part; his login reaches nothing else.
- Installed and tested on the server at 20:45 IST; the test passed 63 of 63 on a copy of the live data; both services are up.
  `https://followup.dr-manoj.in/finance/salecheck`

## For the chat
### Live files — FROM → TO, md5 read back on the box after placing (installer output, 25-Sep 20:45 IST)
| file | FROM (pinned in the brief; matched on the box at 20:22 IST) | TO (read back) |
|---|---|---|
| /root/finance/finance_app.py | 70cff4981c2ebf554308545fb071f0d4 | d7ee72c51564a397f4e847e98eb80ddc |
| /root/finance/sanjeevni_day.py | 5d16eff5b6e2f0fd561e22d91e4794ab | 22a38006a4e3be59b47ea091ea1f971f |
| /root/finance/sanjeevni_approvals.py | 7ab5fec63db83af3e11c6ac08599be93 | 5fdfa364dee3dd9dcef9ad5fed3233d9 |
| /root/finance/finance_ui/finance_approvals.html | 750f89e008a89a372af25cf7898a7d17 | 6622587e47faff016bf280d380bd4564 |
| /root/portal/portal.py | 80d6dc44acc07ebb0b974fb792507fee | 592ccf99d02c361d4d5eb580995599c3 |
| /root/portal/tile_grants.json | 7d1954760181b4e36e732a974599fd35 (v25) | 9231cefad0897a64aa127ce4a448f4fe (v26) |
| /root/finance/sale_check.py (NEW) | — | 81cccad3c48a894298b3694a7b3b5118 |
| /root/finance/sale_check.html (NEW) | — | 4202d11baee4c9309a518e3aed8cf817 |

`darpan_kal.py` (pin 1958ee7c) was **not** touched: the module is mounted from `finance_app.py` (the estate's guarded-mount
pattern) and imports darpan_kal's `_row / compute_day / _decide / _audit`. The `finance_app.py` edit is the allowed one: the
path→unit line (`/finance/salecheck/...` → `salecheck`) plus the guarded mount block. All six were built ON THE BOX from the
live bytes by `make_s400.py` (every anchor exactly once) and compared with the kit's pins before the walk.

### Data
- `finance.db.bak_S400_20260925_204545` (sqlite backup API) before the seed.
- Seed: `business_unit` `salecheck` · `unit_role` bhati **maker**, manoj **checker** (note `S400`). Bhati has **no medical row**
  (the seed refuses if he had one). The three tables `sale_check_day / sale_check_issue / sale_check_cash` are created on first
  request. No other row changed.
- Backups beside each replaced file: `finance_app.py.bak_S400_70cff498`, `sanjeevni_day.py.bak_S400_5d16eff5`,
  `sanjeevni_approvals.py.bak_S400_7ab5fec6`, `finance_ui/finance_approvals.html.bak_S400_750f89e0`, `portal.py.bak_S400_80d6dc44`,
  `tile_grants.json.bak_S400_7d195476`.
- Services restarted: `clinic-finance`, `clinic-portal` (only those). After: both active; `/finance/healthz` 200 (local and public);
  `/finance/salecheck` without a login 302 (the login gate — expected); journal has no "NOT mounted".

### The walk (`walk_s400.py`, 63 checks) — the installer's run at 20:45 IST was GREEN 63/63; the full output below is the
staged run of the same kit bytes at 20:44 IST on a scratch copy of the live database (own rows dated 2099-12-01..04, found by key)
```
-- own rows planted: 2099-12-01 (clean, Darpan 1,000 to Dr Bhawna) · 2099-12-02 (crafted) · 2099-12-03 (approved) · 2099-12-04 (no Marg sheet) · real unapproved day 2026-09-24
-- 1  the unit, the page, the gate
  ok   finance_app resolves /finance/salecheck/... to the unit 'salecheck' and mounts sale_check
  ok   bhati opens his page (200) and it is the S400 page
  ok   bhati is refused on every §6 address: approvals, day/days/months/bank/needs-you, Darpan's month page + APIs, owner card, an APPROVED day   [all 302]
  ok   the owner keeps everything on the same addresses (all 200)
  ok   darpan, bhawna, shavez, a stranger cannot open Bhati's page   [all 302]
  ok   the approved day answers 200 to the owner on Bhati's own API
-- 2  the list, one day, what is never shown
  ok   the list carries the three unapproved walk days oldest first and NOT the approved one
  ok   the list is in date order from the log-from date (oldest first)
  ok   a card: date, weekday, Marg bills count and sale, one status chip
  ok   a day opens: Marg bills each with bill no, name as the system shows it, amount, its medicines
  ok   returns · UPI from the bank (time, last 4 of the reference) · Home/Procedure · Cash received
  ok   what Darpan recorded as handed is shown (1,000 to Dr Bhawna)
  ok   NEVER shown to Bhati: drawer, where it went, position/pool, deposits, banks, months, other days' totals
  ok   every rupee here is the owner's day panel's own (cash_received_p = 1,00,000 paise)
-- 3  the red flags: each fires on a crafted day, all quiet on a clean one
  ok   crafted day: 'Darpan recorded no handover' fires
  ok   crafted day: 'a bill with no patient name' fires and names it
  ok   crafted day: 'a HOME bill with no deduction' fires (identity_resolution text, no day_noncash_bill row)
  ok   a day with no Marg sale report: 'Marg ki sale report abhi nahi aayi' fires
  ok   the clean day carries no flag at all
  ok   after Bhati counts 900 against 1,000 expected: 'handover ≠ cash received' fires with the difference (100 kam)
  ok   the list's card carries the same flags as the day
-- 4  Sahi hai · Galti hai
  ok   Sahi hai stores once (verdict ok, by bhati)
  ok   a second tap does not create a second entry (answers 'already'; still ONE row)
  ok   Sahi hai on an approved day is refused to Bhati (403)
  ok   a galti with bill + problem stores
  ok   'Aur kuch' without a note is refused (400)
  ok   'Aur kuch' with a note stores against 'Poora din'
  ok   the same galti again is refused (409 already) -- no duplicate
  ok   a bill not of the day is refused
  ok   stored in English keys; two active issues; verdict 'wrong'
  ok   Sahi hai while a galti stands is refused (409)
  ok   Bhati removes his own galti; one remains
  ok   the day's chip reads 'Galti — 1'
-- 5  the cash Darpan handed: one movement through darpan_kal's own path
  ok   Bhati's amount lands: darpan_kal_day row created by bhati, party dr_bhawna BY DEFAULT, state decided
  ok   exactly ONE cash_movement on the day, reference '[kal] <date> -> dr_bhawna', 2,000
  ok   a re-save (1,900) UPDATES the same row -- same id, new amount, still one
  ok   the toggle to Dr Manoj changes the same row's party
  ok   the date is always the sale date (the movement sits on that day's own entry; no date is typed)
  ok   a bad amount 400, an approved day 403, a bad party 400
  ok   Darpan recorded 1,000, Bhati counted 900: Bhati's figure is the checked one, the difference (100) shown, Darpan's figure kept
  ok   that day too has exactly one movement, 900 (the row Darpan's own entry would have used)
  ok   every write is in darpan_kal_audit under bhati
-- 6  the owner's side
  ok   the owner's days API carries Bhati's mark: 'Bhati ✓ <time>' on the checked day, with his cash entry and Darpan's differing figure
  ok   'Bhati: 1 mistake' with the list (bill, problem, note) on the day with a galti
  ok   nothing on an unchecked day
  ok   Needs you gains 'Bhati found mistakes on 1 day'
  ok   the day panel's Checks say what Bhati found (the galti list) and the cash he entered
  ok   on the checked day: his verdict (ok) and his cash with Darpan's figure named
  ok   the approvals page carries the S400 line and the owner's change control
  ok   the owner changes the PERSON of Bhati's entry (-> Dr Bhawna): the same movement's party changes
  ok   Bhati cannot use the owner's change (403)
  ok   the owner moves the DATE (02 -> 04): the movement now sits on the new day only, the kal row and the check row follow
  ok   a move onto an APPROVED day is refused (409); onto a day that already has a handover is refused (409)
  ok   both owner changes are audited
  ok   after the move the days API shows the cash on the new day, none on the old
-- 7  a real unapproved day is unchanged; the negative control (the box as it is)
  ok   the owner's day panel for the real unapproved day 2026-09-24 is unchanged (every key, every rupee; Checks identical)
  ok   Needs you is unchanged except the new Bhati line
  ok   NEGATIVE CONTROL: on the box as it is, bhati's page does not open (the route is behind the medical gate)   [302]
  ok   NEGATIVE CONTROL: on the box as it is, bhati is refused on every §6 address too (the leak never existed; this kit adds his door without opening another)
  ok   NEGATIVE CONTROL: the old days API carries no Bhati mark, the old Needs you no Bhati line, the old page no S400 code
-- 8  the portal tile
  ok   the tile 'Medical sale check' shows for bhati (staff) and the owner (doctor)
  ok   darpan, bhawna, shavez and every other staff login see NO change; nothing is lost anywhere
  ok   tile_grants.json is v26 and grants the tile to bhati by name
WALK_S400 GREEN -- 63/63
```
**Negative control:** the same probes against a copy of the box as it was (unpatched `finance_app.py`, no `sale_check`):
Bhati's page 302, `sale_check` not mounted, no Bhati mark on the days API, no Bhati line in Needs you — the three
NEGATIVE CONTROL checks pass only because the old app fails them. (The §6 addresses were already closed to bhati before this
kit — he never had a medical row — so the control shows this kit opens exactly one door, not that it closed a leak.)

### Design notes the chat should know
- Access is per unit as S340/S251 did it: unit `salecheck`, bhati maker, manoj checker. The route calls `require("maker","checker", unit="salecheck")`
  after the front gate; a maker is refused an approved day (403) inside the module.
- Bhati's cash: `darpan_kal_day` is inserted (created_by = bhati) or, when Darpan's row exists, its `handed_p/handed_to` are set to
  Bhati's figure, then `_decide()` runs — the same verdict/state/landing as Darpan's own entry (short → open/needs reason, over → owed,
  within tolerance → complete). Darpan's original figure is kept in `sale_check_cash.darpan_p` and shown as the difference. A row
  already `received_at` or with an `owner_decision` is refused (409) as `api_handover` does.
- The owner's date move deletes the old landed `cash_movement` (+ its `cash_handover_cover` row), withdraws any open owed row, removes
  the old `darpan_kal_day` row (only when Bhati created it — a Darpan-typed row answers 409 "change it on his page"), inserts the new
  day's row and re-lands through `_decide()`; the target must be an unapproved filed day with no handover.
- "Marg's sale report not in" = `day_view.source != 'marg'` (no `sale_bill` rows for the day). The HOME/PROSIJER flag reads the same
  `noncash.home_words / noncash.proc_words` settings as `day_resync` (review queue + identity_resolution + identity_dispute text), and
  is quiet once a `day_noncash_bill` row or a `cash_bill_ruling` exists.
- Version stamps: `sanjeevni_day` 1.1 → 1.2, `sanjeevni_approvals` 1.3 → 1.4.

### Not done / outside the brief
- Not done: nothing in the brief is left out.
- Noticed, not touched: `portal.py` line ~1361 (S370) carries a `"\/"` escape in a JS string inside a Python string that py_compile flags
  as a SyntaxWarning on newer pythons (fine on the box's 3.9); pre-existing, unrelated.
- The publish and the repo-copy check are recorded below.

### Publish and the repo-copy check (read from the box)
- Journal after the restart: the only lines are gunicorn's own `reentrant call inside <_io.BufferedWriter name='<stderr>'>`
  shutdown-logging race at the SIGTERM of 20:45:49 — the identical trace is in the journal at the 24-Sep 09:52:45 restart
  (an earlier kit), nothing after 20:46, two workers running since 20:46:19. Not this kit; noted, not touched.
- The installer was run from `/tmp/s400kit/` (SUMS.md5 checked OK there first) at 20:45:45 IST.
- `PUBLISH_ALL.bat`: gate clean (10 staged files), commit `6c2beb6`, pushed, origin HEAD verified.
- On the box at 20:49:19 IST: `/root/deploy/repo` pulled to `6c2beb6`; `md5sum -c SUMS.md5` OK in the repo kit; every one of the
  8 kit files `cmp`-identical to the copy that ran; `sale_check.py` / `sale_check.html` placed == the repo kit; the six patched
  files still at their TO pins; the repo installer's re-run took its ALREADY INSTALLED path (rc 0, seed re-checked, nothing
  changed); healthz 200 at 20:49:20. `/tmp/s400kit` removed.
- Live `sale_check_*` tables are created on the first request to the page (the S340 pattern); at 20:48 none existed yet — nobody
  had opened it. The unit and the two role rows are in place (read back: `salecheck` bhati maker, manoj checker; bhati medical rows 0).
