# Claude Code brief — S400_MEDICAL_SALE_CHECK (Bhati checks the pharmacy days)

Written 25-Sep-2026 by the Sanjeevni chat (S283). Read `CLAUDE.md` in the repository root first — every rule there binds.
**Kit number S400. Decision D616** (the owner's words, 25-Sep). Numbers are already claimed on the System Board; use these.
The owner has approved this WHAT in chat. Build → test on a copy → install → verify → publish → report, in one run.

## 1 · What the owner wants, in his words
- Bhati becomes the **checker of the Sanjeevni days**. Next morning he gets the days **not yet approved**, checks
  Darpan's physical copy and the Marg sale sheet against what the system shows, "as I do right now".
- Whether Darpan did his job or not must be **flagged** there.
- Bhati enters **only the amount** of cash Darpan handed over. It goes to **Dr Bhawna by default**, one tap for Dr Manoj.
  **The date is the sale date**, fixed. "If needed I can change these in my login." Quick, frictionless.
- A wrong day: **minimum typing, maximum drop-downs.**
- Bhati must **not** see month totals or any other cash part — only the days not yet approved.
- The owner stays the approver and the final pass, and **can do all of it himself exactly as today** when Bhati is absent.
- **Tile name: `Medical sale check`.**

## 2 · Facts you need (read from the code of 24/25-Sep; verify on the box before relying on them)
- The owner's day panel: `/root/finance/sanjeevni_day.py` (`day_view(con, iso)`, route `/finance/sanjeevni/api/day/<iso>`,
  checker only). The approvals page: `/finance/approvals` → `finance_ui/finance_approvals.html`, its API
  `/root/finance/sanjeevni_approvals.py` (`/finance/sanjeevni/api/days`, `needs-you`, `months`, `bank`).
  Both are mounted from `darpan_kal.init()` in `/root/finance/darpan_kal.py`.
- Darpan's handover: `darpan_kal.py` → table `darpan_kal_day` (handed_p, handed_to ∈ `dr_manoj`/`dr_bhawna`, created_by,
  received_by …), written by `api_handover` and by `_log_one` (the doctors' log); both call `_decide()` which lands ONE
  `cash_movement` row via `_land_movement()`. **Bhati's amount must go through this same path** (`_decide`/`_land_movement`),
  never a second register — the one cash calculation (`sanjeevni_cash.py`) reads it. Every write → `darpan_kal_audit`.
- Access is per server unit (`unit_role` table, `finance_app.py` gate). Bhati (login `bhati`, portal role staff) today holds
  rows only in `physio` and `slips`; **he has NO medical row and must not get one.** Follow how S340 added the unit
  `checks` (and S251 `physio`): a NEW unit for this page only, e.g. `salecheck`, with a `unit_role` row for bhati.
  If a new unit needs an edit to `finance_app.py`'s path→unit map, that edit is allowed — anchored, declared in the README.
- Portal tiles: a tile in `/root/portal/portal.py` with roles `['doctor']`, granted BY NAME in
  `/root/portal/tile_grants.json` (bump its version, add a `_note` line in the file's own style). Model: v24/v25 entries.
- The day's figures: Marg bills `sale_bill` + lines `sale_line_item`; UPI from the bank `upi_statement`/`upi_txn`;
  home/procedure medicine `day_noncash_bill` (+ `cash_bill_ruling`); Cash received = sale − returns − UPI − without cash
  (exactly `day_view`'s `cash_received_p`). Unapproved = `day_entry.status IN ('submitted','draft')`, unit `medical`,
  from the setting `darpan_kal.log_from` (2026-08-17) on.

## 3 · FROM pins (read the live md5 first; a mismatch = stop that file and report)
| file | FROM | owner |
|---|---|---|
| /root/finance/darpan_kal.py | 1958ee7c620d890f10a609473b2a8f1d | Sanjeevni |
| /root/finance/sanjeevni_day.py | 5d16eff5b6e2f0fd561e22d91e4794ab | Sanjeevni |
| /root/finance/sanjeevni_approvals.py | 7ab5fec63db83af3e11c6ac08599be93 | Sanjeevni |
| /root/finance/finance_ui/finance_approvals.html | 750f89e008a89a372af25cf7898a7d17 | clinic — declared |
| /root/portal/portal.py | 80d6dc44acc07ebb0b974fb792507fee | clinic — declared |
| /root/portal/tile_grants.json | 7d1954760181b4e36e732a974599fd35 (v25) | clinic — declared |
| /root/finance/finance_app.py | 70cff4981c2ebf554308545fb071f0d4 | clinic — ONLY if the unit needs it |
Touch only what the build needs from this list; a NEW module (e.g. `/root/finance/sale_check.py` + its Hindi page) is preferred
over growing an existing file. Restart `clinic-finance` and `clinic-portal` only.

## 4 · Bhati's screen — `Medical sale check` (Hindi, Roman script, phone-first)
- **List:** the unapproved days, oldest first, one card each: date + weekday, Marg bills count and sale, and one status chip
  (`Jaanch baaki` / `Sahi hai ✓` / `Galti — 2`), plus red flags (below). An approved day disappears from his list.
- **A day opens into** (read-only figures, same as the owner's day panel for that ONE day):
  Marg bills — each bill no., name as the system shows it, amount, tap to see its medicines · returns · UPI from the bank
  (payments with time and last 4 of the reference) · Home / Procedure medicine (without cash) · **Cash received** for the day ·
  what Darpan recorded as handed (amount, to whom), if anything.
  **Never shown:** drawer, pool, "where it went", deposits, banks, month table, other days' totals, returns approval.
- **Two buttons:** `Sahi hai` (one tap, done) · `Galti hai` → drop-down **Kaunsa bill** (the day's bills + `Poora din`) →
  drop-down **Kya galti** (`Amount alag hai` · `Marg mein bill nahi` · `Kaagaz par bill nahi` · `Home/Procedure nahi laga` ·
  `Cash/UPI galat` · `Aur kuch`) → a short note box appears ONLY for `Aur kuch` → `Jodo`. He may add more than one galti to a day,
  and remove his own before the owner approves. Stored in English keys (amount_differs, missing_in_marg, missing_on_paper,
  noncash_not_marked, mode_wrong, other).
- **Cash from Darpan:** one amount box, prefilled with Darpan's figure if Darpan recorded it (else empty) · a two-way toggle
  `Dr Bhawna` (default) / `Dr Manoj` · date = the sale date, not editable · `Save`. It lands through the existing handover path
  (created_by = bhati, audited). If Darpan had recorded a different amount, Bhati's figure is kept as the checked figure, the
  difference is shown red, and the owner decides on his page (as he does today for a short handover).
- **Red flags on the card and in the day** (computed, never typed): Darpan recorded no handover · handover ≠ Cash received
  (show the difference) · Marg's sale report for the day not in · a bill with no patient name · a HOME/PROSIJER bill with no
  deduction. Say each in one Hindi line.
- A message after every save, large and green, naming what was saved (the S394 petty-book pattern). A double tap within
  10 minutes must not create a second entry (S393 lesson).

## 5 · The owner's side (English) — "nearly the same"
- On `/finance/approvals`, each day row gains **one small line**: `Bhati ✓ 09:40` or `Bhati: 2 mistakes` (tap → the list:
  bill, problem, note) or nothing if unchecked. Inside the day panel's Checks: Bhati's verdict, his galti list, his cash entry.
- `Needs you` gains one line when Bhati has marked mistakes on unapproved days: `Bhati found mistakes on N day(s)`.
- The owner can **change the person and the date** of a cash entry Bhati made (amount already changeable via the existing log).
  A date move is allowed only to another unapproved day and is audited.
- Nothing is blocked if Bhati has not checked: approving, logging, everything works exactly as today.

## 6 · Access — enforced on the server, proven by the walk
Bhati's login may reach ONLY the new page and its own API. The walk must show **403 (or the login redirect)** for bhati on:
`/finance/approvals`, `/finance/sanjeevni/api/day/<iso>`, `/finance/sanjeevni/api/days`, `.../months`, `.../bank`,
`.../needs-you`, `/finance/darpan/kal/month`, `/finance/darpan/kal/api/month`, `/finance/darpan/kal/api/owner`,
and the new API for an **approved** day. And 200 for his page and an unapproved day. The owner keeps everything.
`darpan`, `bhawna`, `shavez` see no change.

## 7 · The walk (on a scratch copy of the live DB, own rows dated 2099-12-xx, found by key)
At least: an unapproved day lists, an approved one does not · Sahi hai stores once, a second tap within 10 min does not duplicate ·
a galti with bill + problem stores, `Aur kuch` without a note is refused · Bhati's amount lands ONE cash_movement through
`_decide` and a re-save updates the same row · default party dr_bhawna, toggle dr_manoj · date is always the sale date ·
Darpan-different amount shows the difference · every red flag fires on a crafted day and stays quiet on a clean one ·
the owner's `days` API carries Bhati's mark · owner date/person change works and is audited, refused onto an approved day ·
every access line of §6 · **negative control:** the same access checks against the unpatched gate show the leak is closed by
this kit (or the route absent) · the owner's day panel and `needs-you` for a real unapproved day are unchanged except the new line.

## 8 · Done means
Kit `deploy_kits\S400_MEDICAL_SALE_CHECK\` complete (CLAUDE.md shape) · installed on srv1746119, every md5 read back ·
clinic-finance + clinic-portal active, `/finance/healthz` 200 · the tile shows for bhati · published with `PUBLISH_ALL.bat` ·
`claude_code_briefs\REPORT_S400.md` written (owner lines on top; then pins FROM→TO, walk output, backups, anything not done).
Owner lines to end with the page address in full: `https://followup.dr-manoj.in/<the page's path>`.
