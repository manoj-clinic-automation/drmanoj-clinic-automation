# S432 — THE MARG WATCH: one integrated plan for review
*The Sanjeevni chat · session 432 · 11-Nov-2026, 21:3x IST · a plan, nothing built · supersedes `S429_MARG_REPORTS_FLOW_PLAN.md` (kept as the record of how it began)*

**For the reviewer (next session):** read this whole, check every "as found" line against the live code in the newest bundle (`D:\Downloads\_kbtools\vps_code\code_nightly.tar.gz`), refine where needed, and answer §12 (the open points). The owner's words of 11-Nov are in §1; nothing in this plan may contradict them without his OK.

---

## 1 · What the owner asked, and what he ruled (11-Nov-2026, in his words where they matter)

| time (IST) | the owner | effect on the plan |
|---|---|---|
| 14:46 | "Yes, add this feature in the next build": refuse a **MAIN STORE** stock export on arrival — only WHOLE STORES is filed | §4 |
| 14:46 | the section *"Stock changed in Marg without a bill or voucher"* to be a **table**, period-wise, with added / subtracted totals | §5 |
| 15:03 | the section is for **UNEXPLAINED** moves only — no sale, purchase, stock-issue or stock-receive voucher. Anything with a record, even a wrong one, goes to *"Explained after all"*, not counted. Each period expands to its own moves table; "Each move" kept separately, without notes | §5 (mock v2 shape, approved) |
| 18:04 | monitor later modifications of sales, purchase bills, stock vouchers; suggest a simple system | §6 |
| 18:12 | minimum new manual exports; an AutoHotkey-style runner on the medical PC with the reports-only login, set up **without him touching the PC** (through the agent's Drive kit) | §9 |
| 20:20 | "manual is okay till AutoHotkey is set up" | then refined at 21:09 → |
| **21:09** | **no fixed weekly cadence.** Constant monitoring with the **existing** reports; a report is made **as per need** — the need is flagged, then he, Shavez or AutoHotkey makes it | §6, §7 |
| **21:12** | **money-only changes to sale bills (rate, discount, cash → UPI) carry no weight**: the day's sale report is printed and submitted, cash handed over against it the same evening, UPI matched to the POS totals and confirmed next morning by the MPR and bank SMS | §6.3 — not watched; one free safety net only |
| **21:15** | from the watch page, **send the needed finding** to the right person — a **copy block / WhatsApp** (Amir, Darpan, anyone), **and** the same item in **their own app** in the relevant place; **their answer comes back here** or where recommended | §8 |
| 21:18 | a detailed final plan, to be reviewed in the next session | this paper |

**Standing rules that bind every part:** owner pages in English, staff screens in Hindi · nothing live rebuilt without his OK; the manual path stays · a mock first for every screen, his word before every kit · no technical choice put to him · no patient data anywhere in this (none is involved: items, bills, suppliers only) · no phone number stored in the repository.

---

## 2 · The whole flow on one page

```
 MARG (medical PC)
   │  daily reports   : staff on the reports login, from the flows page  ── LATER: the runner (AutoHotkey)
   │  on-need reports : asked by a flagged row (§7) — the owner, Shavez  ── LATER: the runner reads the same request list
   ▼
 THE WATCHER on the medical PC captures every saved file → Drive → server            (live, unchanged)
   ▼
 THE DOOR — every file checked on arrival
   · stock files: WHOLE STORES only — a MAIN STORE / DTH / SCRAP file is REFUSED, the reason said   (§4, new)
   · dates, period, settings (Pur. Rate etc.)                                                      (live)
   ▼
 THE MARG WATCH — one owner page, two sections, the same shape                                     (§5, §6)
   A · Stock moved with no record     (daily closings vs sales, bills, vouchers — live engine, page redesigned)
   B · Changed after the day          (the same bill seen in two exports of the same period — new)
       each row: Asked → Answered → Closed;  a "who changed it" note when the audit trail was read
   ▼
 ASK (§8) — from any row: a Hindi message (copy block + WhatsApp) AND a card in Amir's or Darpan's own app;
            their one-tap answer returns to the same row; the owner is told by the existing owner notices
```

---

## 3 · The reports — final table (no new fixed-cadence export)

| report | when | made by now | later | feeds |
|---|---|---|---|---|
| Closing stock, WHOLE STORES | daily | staff, reports login (flows page) | runner | A |
| Sale bill-wise (detail) | daily | staff, reports login | runner | A, the cash day (live) |
| Purchase bill-wise + item-wise, month to date | on each of Amir's visits (as today) | Amir | Amir stays; runner may add | A (purchases), **B (free)** |
| Batch Stock (whole), Valuation (Pur. Rate, whole) | 1st – 7th of the month | Amir / Shavez (as today) | runner | expiry, value |
| Salt · Item · Category lists | as today | staff | runner | item facts |
| **Any report a flagged row asks for** (a sale day again, a stock voucher list for given dates, a purchase period) | **on need only** | **the owner or Shavez** | **runner** | A, B |
| Marg User Audit Trail (Daily Reports → Audit Trail → User Audit Trail) | **on need only**, when he wants to know *who* | owner or Shavez | runner, if the reports login may open it | the "who" note |

**Dropped from the S429 plan (owner, 21:09):** the weekly (Monday) and 1st-of-month look-back exports of sale bill-wise, purchase bill-wise and stock voucher list. The monthly sale bill-wise on the 1st was also considered and dropped (owner, 21:12).

---

## 4 · The door: MAIN STORE refused on arrival

**As found (11-Nov bundle):**
- `marg_ingest/lib/marg_stock.py` reads the store from the title row (DTH / MAIN STORE / SCRAP STORE / WHOLE STORES), never the file name.
- `marg_ingest/lib/push_expected.py`, `push_snapshot.py` and `finance/push_snapshot.py` already pick WHOLE STORES only.
- `finance/reports_tile.py` (F-799) already judges a closing stock that is not the WHOLE STORES totals list as *wrong*, with a fix (`stock25`).
- `finance/marg_flows.py` / `reports_guide.py` already tell staff in Hindi: *"DTH, MAIN STORE ya SCRAP STORE nahi."*
- The archive: every stock export since 9-Oct is WHOLE STORES; main-store files exist only for 06-Sep (valuation ×2), 04-Oct (valuation), 08-Oct (closing), each replaced the same day or next morning.

**What is new (the gap the owner named):** the refusal happens **at arrival**, for **every** stock-type export (closing, batch stock, valuation), not only in the daily tile's judgement:
1. The file is filed aside as REFUSED (kept, never read as stock), with the reason.
2. The staff's reports tile says at once, in Hindi, which file was refused and why, and that the WHOLE one is still needed — the existing "wrong" path, extended to batch stock and valuation.
3. An owner notice line only if the WHOLE file has not followed by the tile's normal due time (no noise when staff fix it at once).

**The reviewer checks first:** how much of 1–3 `reports_tile.py` and the router already do; the kit builds only the gap.

---

## 5 · Section A — Stock moved with no record (the engine is live; the page is redesigned)

**As found:** `finance/marg_hand_change.py` (S706, D828, live since 05-Nov). Per item, over Marg's daily closings (`spine.db sp_close`): E = Marg − the spine's own balance − Amir's filed vouchers; a step in E is a shift. It already sets aside a purchase Marg had not caught up with (OWED), a step undone within three closings, and renames (kind `rename`). Rows are refreshed by `owner_notice.py`'s five-minute tick; the owner is told the morning after (`owner_notice` key `hand:<found at>`). The page today is the collapsed section `_hand_section` in `finance/expiry_watch.py` (line ~1157) on `https://followup.dr-manoj.in/finance/sanjeevni/expiry` — cards with long notes.

**What the S429 analysis found on the live rows (11-Nov, 33 open + 4 renamed):**
- Marg's before / after figures match Marg's own daily closing files on all 33 — the engine's figures are right.
- **15 of the 33 had a record after all**, which the engine does not yet recognise: a voucher on the wrong item or size; a voucher quantity that differs; a sale Marg did not take off; a bill timing (e.g. TRAMAVIN GEL −11 / +12 around bill 4100); the same stock under two names (THIO Q AP +120 tabs / THIO Q AP TAB −12 strips); a free quantity later corrected (DOLONEX +7 / −7, bill 19612). BIO D3 MAX +150 (6–8 Nov) = Gunina bill 92592, in Marg, not yet in the system.
- **The explanation line is wrong on three rows:** THIO Q AP 2–4 Nov says "system moved nothing" (it moved +120, bill 748); DOLONEX 16–18 Oct says "+2" (it was +72); the three CCM rows repeat one note that fits none. → **a fault to mint at the close** (Sanjeevni's own file).
- **Truly unexplained: 18 moves, +₹6,611 / −₹4,020, net +₹2,591** at Marg purchase rate.

**The redesign (mock v2 shape, approved — `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S429\screen\stock_moved_no_record_MOCK_v2.html`):**
1. **Counted:** only moves with no sale, purchase, stock-issue or stock-receive voucher anywhere near them.
2. **"Explained after all"** (not counted): every row with a record, even a wrong one, with the record named in one short line (bill / voucher number, what differs).
3. **Period table:** period · items · added (units, ₹) · subtracted (units, ₹) · net; each period opens to its moves table: item · Marg before · Marg after · system moved · added / subtracted · ₹ at purchase rate · status (open / asked / answered / closed).
4. **"Each move"** kept separately, flat, without notes.
5. **Pairs** (same stock under two names, a + and − that cancel) shown as one line with both names.

**Engine changes (in `marg_hand_change.py`, the Sanjeevni chat's file):** the "has a record" matchers of the 15 (wrong item / size within the same family, quantity differs, sale not taken off, bill timing, two-name pairs, free-quantity corrections); the three explanation-line errors; ₹ at purchase rate per row. The page reads the table only (no new writes from the page except the ask and status rows of §8).

---

## 6 · Section B — Changed after the day (new; on existing reports only)

### 6.1 What it compares
The archive keeps every export; `marg_ingest/lib/marg_effective.py` decides which one *counts* (a later export of a period supersedes the earlier). **B reads the pairs that rule throws away:** for every bill seen in two exports of an overlapping period, the earlier and the later are compared bill by bill.

| source of the pairs | how often they arise | catches |
|---|---|---|
| **Purchases** — Amir's month-to-date bill-wise / item-wise exports, each covering the month again | every Amir visit | a purchase bill deleted, added with an old date, supplier changed, quantity / free / rate / discount / amount changed |
| **Sales** — any day exported twice (a re-export, or an on-need report of §7) | whenever it happens | a sale bill deleted or added afterwards, quantity / amount changed (A004591 was found this way) |
| **Stock vouchers** — when a voucher list is exported on need | on need | a voucher deleted, re-dated, quantity changed |

### 6.2 What a B row says
bill date · bill number · supplier / party · **what changed (was → now)** · ₹ effect · first seen in (export, date) · noticed in (export, date) · status. Period table and totals exactly as section A. An item renamed in Marg is noted as a rename, never counted.

**First run:** back through the archive to August. Already proven on old files (S429, read only): sale bill A004591 (03-Nov, ₹1,760 cash) gone from the 05-Nov re-export; two 18-Aug sale bills cash → UPI; PRETOL 8 purchase rate 57.60 → 56.00 (October, between the 10-Nov and 11-Nov exports); JAKMAC 5 rate 172.86 → 172.89 on three September bills; August: CCM quantity 6 → 5, TRAMATEE P rate 82.50 → 85.00, a KEDAR bill of ₹6,400 (07-Aug) replaced by one of ₹800 (04-Aug).

### 6.3 What B does **not** watch, by the owner's ruling (21:12)
Money-only changes to **sale** bills (rate, discount, cash ↔ UPI) after the day: the day's cash and UPI are already locked by the printed sale report, the cash handover, the POS totals, the next-morning MPR and bank SMS. Such a change, if seen in a pair, is listed in B as **"for the record"** — never counted, never told.
- A deleted or back-dated **sale** bill still shows in A (it moves stock), so the money-only gap is only a rate / discount edit — accepted as remote.
- **One free safety net:** the system keeps each day's **first** sale total. When the owner takes Marg's **quarterly** sale figure for the composition GST return, the page compares it with the sum of the first daily totals of that quarter; a difference is one line in B. *(GST filing belongs to the parent's accountant-pack area; this check only reads the figure. See §12.)*

---

## 7 · Reports on need — the request list

When a row cannot be settled from what has arrived, the row says **which report, for which dates**, e.g. *"Sale bill-wise, 01–10 Nov"*, *"Stock voucher list, 02–04 Nov"*, *"User Audit Trail, 03–05 Nov"*.

- The request is kept in one list on the server (a small table), each with: the report, the dates, the reason (the row), asked on, made by, arrived on.
- **Now:** the row shows the request with the Marg path in Hindi as a copy block for Shavez (or the owner does it himself). When the file arrives through the watcher, the request closes itself and the row is re-judged.
- **Later:** the runner reads the same open requests (published to Drive `ToMedical`) and makes them on its next run. Nothing else changes.
- **The audit trail:** read only when the owner wants to know *who*. Its reader needs one real sample of the file before it is built (§12). Until then the owner reads it in Marg and types a one-line note on the row.

---

## 8 · Ask — send a finding to the right person, and get the answer back

### 8.1 On the owner's page (English)
Every row in A and B (and every on-need request) has **Ask**.
- **Who:** suggested by the row, changeable — **Amir** for purchase bills and stock vouchers (he enters them); **Darpan** for sales and counter stock; **Shavez** for reports; any other named staff.
- **Several rows** can be ticked and sent as one message to the same person.
- **The message**, made by the system in **Hindi**, short: item / bill · dates · what moved or changed · the question. Shown as a **copy block** plus a **WhatsApp button** (opens WhatsApp with the text filled in; **he chooses the contact** — no phone number is stored anywhere).
- The row then reads **Asked — Amir, 11-Nov 21:20**.

*Example (Amir):* `Amir ji, Marg mein THIO Q AP TAB ka stock 2 Nov se 4 Nov ke beech 12 strip kam hua, koi bill ya voucher nahi mila. Kya aapne koi voucher ya badlaav kiya tha? Apne page par jawab dijiye.`

### 8.2 In the staff's own app (Hindi)
| who | where | as found |
|---|---|---|
| Amir | a **"Sawaal"** card at the top of his day page `https://followup.dr-manoj.in/finance/amir/day` | `finance/amir_day.py` (3,150 lines; has `amir_job`, `amir_claim`, *pichhla baaki*) |
| Darpan | a **"Sawaal"** card at the top of his page `https://followup.dr-manoj.in/finance/darpan` | `finance/darpan_app.py` (1,594 lines; day card, claims) |
| Shavez | copy block / WhatsApp only (no pharmacy page of his own) — the owner, or Shavez on the owner's page, types the answer on the row | — |

*Correction to what was said in chat at 21:15:* Darpan's card goes on his **main page**, not on `/finance/darpan/corrections` — that desk is Amir's by the S218 contract (`page_corrections` docstring).

**The answer — one tap, plus an optional short line:**
- *Marg mein theek kar diya* (put right in Marg)
- *Sahi hai, galti nahi* (correct, not a mistake) — with the reason in a line
- *Pata nahi* (don't know)
- (purchase rows) *Supplier ka credit note / bill badla* (the supplier changed the bill)

Unanswered after **2 days**: the card stays at the top of their page, the row turns **amber** on the owner's page.

### 8.3 Where the answer comes back — recommended
**To the same row on the owner's Marg watch page:** status **Asked → Answered → Closed**, with the answer, who, and when. **Only the owner closes a row**, or asks again.
**He is told** by the **existing owner notices** (`finance/owner_notice.py`, the channel that already tells him of hand changes and reports) — one line per answer: *"Amir answered: THIO Q AP TAB — put right in Marg"*. If he answered "put right in Marg", the next morning's closing proves it: section A marks the row *put right* by itself (the engine already does this).
*(Correction to the chat at 21:15, which said "the board": the System Board is the assistant's channel to him; the server's own channel is the owner notice. The reviewer may add a board line in the close only.)*

### 8.4 One table for all of it
A small table (one row per ask): which section and row, to whom, the Hindi text, asked at / by, answer kind, answer line, answered at, closed at / by. Read by the owner's page and both staff cards; written only by them. Nothing else in the system changes when an ask is made.

---

## 9 · The runner (AutoHotkey) — unchanged from S429 except the request list

- **Delivered without a visit** through the medical-PC agent's Drive kit (`G:\My Drive\Clinic Data Archive\ToMedical\_kit`); AutoHotkey in its no-install form. The owner types the reports-login password **once**, in a box on the PC, never in chat.
- **When:** at power-on in the SET account, before the counter switches user (a Hindi notice: *reports ban rahi hain, 5 minute*); again at night if the morning run was cut short. Never while the counter is billing.
- **Stops at once** if a key or the mouse is touched, a Marg screen title is not the one expected, or Windows switches user; closes Marg cleanly and says why in the heartbeat (`FromMedical\heartbeat.txt`).
- **Only the reports login.**
- **Take-over, report by report:** shadow beside staff → after **7 clean days in a row** (its file = staff's file) the report moves to the runner; staff asked only on a missed day (the existing 10:00 banner); any report can go back to staff by one switch; the flows page and buttons stay for ever.
- **New:** it also makes the **open on-need requests** of §7 (and the audit trail, if the reports login may open it).
- The WiFi dongle (from 11-Nov) is the medical PC's second road out; the heartbeat says which road was used.

---

## 10 · Build order — a mock first, his word before each kit

| # | what | touches | his part |
|---|---|---|---|
| 0 | **Mock v3** — the owner's Marg watch page (A + B + Ask + the request list), Amir's and Darpan's *Sawaal* cards, a sample Hindi message — built on the real figures (A's 18 + 15; B's proven cases) | nothing live | **his word on what he sees** |
| 1 | **Kit 1:** the door refuses MAIN STORE (the gap of §4) · section A's engine changes (§5) · the new Marg watch page with section A · the expiry page's section becomes a one-line link with the counts (after the new page is proven) | server only (`marg_hand_change.py`, `expiry_watch.py`, a new page module, the door) | the install line |
| 2 | **Kit 2:** Ask (§8) — the owner's buttons, the Hindi message, the two staff cards, the answer path, the owner notice line, the 2-day amber | server only (`amir_day.py`, `darpan_app.py`, `owner_notice.py`, the new page) | the install line |
| 3 | **Kit 3:** section B (§6) — the pairs from the archive, the first run back to August, the quarterly GST cross-check | server only | the install line |
| 4 | **Kit 4:** the on-need request list (§7) | server only | the install line |
| 5 | **Runner trial** on one report, one Sunday morning | medical PC, through the kit | the password, once |
| 6 | **Runner:** the daily pair in shadow → take-over; then the monthly set; then the open requests | medical PC + server | none |

Each kit: the maker, the walk on made-up rows with a CONTROL that goes red, the rehearsal on a copy of the live database (in the device VM only, D656), the proof — then his install line; the publish is his double-click (`D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`).

---

## 11 · Safety

- **Read only on Marg** at every step; the system never writes into Marg. The runner uses the reports-only login.
- **No staff screen changes before the mock is approved.** Staff cards are additive (a card at the top), nothing removed.
- **The expiry page's live section stays** until the new page has run beside it and he says so.
- **Off switches** as today: `/root/finance/_off/ALL_OFF`, `/root/marg_ingest/OFF`, `hand.on = off`; each new part gets its own setting.
- **No numbers in the repository** (the number gate); no phone numbers anywhere (WhatsApp opens without a number).
- **Files owned by another chat:** `owner_notice.py` is Sanjeevni's (S702); `expiry_watch.py`, `marg_hand_change.py`, `amir_day.py`, `darpan_app.py`, `reports_tile.py`, `marg_ingest/` are Sanjeevni's. **No PLANNED line needed** unless the GST cross-check touches the parent's accountant-pack files (§12).

---

## 12 · Open points — for the reviewer to settle (never to be put to the owner as technical questions)

1. **§4:** how much of the arrival refusal `reports_tile.py` (F-799) and the router already do for closing stock — and whether batch stock and valuation are covered. Build only the gap.
2. **§5:** the exact rules for the 15 "has a record" cases — confirm on the live table, written as matchers with the CONTROL that a truly unexplained row stays counted.
3. **§6.1:** whether the archive keeps every superseded export of sales and purchases in full (it should — `marg_effective.py` is a read-side rule); the bill identity across exports (bill number + date + party; rename-proof).
4. **§6.3:** where Marg's composition-GST file lands (is it saved in a watched folder?). If not, the quarterly figure is one box on the page he types once a quarter. GST filing is the parent's area — a read only; a PLANNED line if any parent file is touched.
5. **§7:** the exact Marg report and menu path for a stock voucher list, and whether the reports login may open it and the User Audit Trail — settled by the runner trial or by Shavez once, not by the owner.
6. **§7:** one real sample of the User Audit Trail export before its reader is built.
7. **§8:** the staff answer words (Hindi) — shown to the owner on the mock; Darpan takes to new flows slowly (`people/darpan` memory) — the card must be one tap.
8. **Page address:** proposed `https://followup.dr-manoj.in/finance/sanjeevni/marg-watch`, owner-only (checker), and a link on his command console.
9. **The S429 session** never closed: its notes (`03_WORKING_PAPERS\S429\S429_NOTES_FOR_CLOSE.md`) and this plan are closed by the S432 close.

---

## 13 · Evidence and files

- `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S429\S429_NOTES_FOR_CLOSE.md` — the analysis notes
- `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S429\marg_units_by_day.json`, `marg_rates.json` — working figures
- `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S429\screen\stock_moved_no_record_MOCK_v2.html` — the approved shape of A
- `S429_MARG_REPORTS_FLOW_PLAN.md` (project knowledge, root and `claude/`) — the plan this one supersedes
- Code read (11-Nov bundle): `finance/marg_hand_change.py`, `finance/expiry_watch.py` (`_hand_section`), `finance/owner_notice.py`, `finance/reports_tile.py`, `finance/marg_flows.py`, `marg_ingest/lib/marg_stock.py`, `marg_ingest/lib/marg_effective.py`, `finance/amir_day.py` / `darpan_app.py` (routes and tables only)

*S432_MARG_WATCH_PLAN · 11-Nov-2026 · the Sanjeevni chat · nothing built*
