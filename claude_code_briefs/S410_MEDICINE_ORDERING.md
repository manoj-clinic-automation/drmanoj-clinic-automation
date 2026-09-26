# Claude Code brief — S410_MEDICINE_ORDERING (the medicine buying rules as settings; fixed order days; the ordering team's day; the owner's page)

Written 26-Sep-2026 by the Sanjeevni chat (S283). Read `CLAUDE.md` first — every rule binds. **Kit S410 · decision D626.** The owner
finalised this WHAT on 26-Sep after a full sitting; **his approval of these rules IS the standing approval — the paper purchase-order sheet
Darpan prints and the owner signs is retired by this kit; the system's record (who sent, when, what arrived, what was billed) replaces it.**
**Runs on its own, AFTER the S405–S408 paste is fully done** (S407 and S409 move `purchase_app.py` / `porders.py`; read every pin live).
Build → test on a copy → install → verify → publish → report, in one run. Orthotics are NOT touched: they run on S403's keep-in-stock.

## 1 · What exists (read the live bytes first)
- The S225 engine copied into `/root/finance/purchase_app.py` (~line 1138: `TIER_WEEKLY_P` 20,000/month, `TIER_FORTNIGHT_P` 4,000/month,
  `CADENCE_DAYS` 7/14/30, `LEAD_DAYS` 2, `SAFETY_DAYS` 3, `SINGLE_SOURCE_EXTRA_DAYS` 3, `MAX_COVER_DAYS` 45, `MIN_LINE_P` ₹50, `DEAD_AFTER_DAYS`
  60, `cadence_for()`, `plan_line()`, `_vendor_cadence()` from 90 days of bills, `_pace()` over `PACE_DAYS`, the strips rounding 10-then-tens),
  the same engine in `/root/finance/spine/order_rehearsal.py` (S341) with `order_rules.json` (never_reorder / on_demand / internal_use /
  orthotics_cycle; only internal_use seeded: BLADE, ZIG ZAG COTTON 500GM, GLOVES SURGICAL 7).
- S403: `/root/finance/porders.py` + `porders.html` — the Purchase orders screen (unit `porders`; senders/viewers/vendor in `setting`
  `porders.*`), section 4 "Medicines (rules ka intezaar)" with **send disabled** until the owner's approval row exists; the owner's approvals
  page section "Purchase orders" with the one-sitting rules page (the text the owner found out of context: "fortnightly above ₹4000").
  Arrival taps Aa gaya / Kam aaya / **Nahi mila** per line; `purchase_order`, `purchase_order_line` (+ S403 columns), `porder_keep`.
- Notifications: the Clinic app's Web Push (`/root/portal/portal_push.py`, S366/S370 — subscriptions per login in push_subs.json; not yet
  proven on every staff phone, so push is ON TOP of the tile count and Darpan's card, never the only channel).
- Data: `purchase_bill` / `purchase_line` (item, packing, qty, free, rate_p, net_rate_p, purchase_rate_p — **no manufacturer, no MRP column**),
  `stock_snapshot` (daily closing; `as_on` DD-MM-YYYY TEXT — parse, never max() the text), `sale_line_item`, `purchase_salt_marg` (item → salt),
  the spine read door when green. **Kedar Pharmaceutical (90 days): 30 bills, ~2.3/week, ₹2.67 lakh = 23 % of purchases, 23 items, four of
  them the bulk (TYRO BR ≈ 29 strips/day, PATOPAN DSR ≈ 20, MEG QCS ≈ 12, FLUXIC P ≈ 9), none bought elsewhere.**

## 2 · The rules (D626) — every number below is a SETTING on the rules page, seeded with these values; the engine reads settings, not constants
### Per supplier (table `order_supplier_rule`: supplier_norm, cadence, order_days, blocked_days, lead_days, safety_days, cover_cap_days,
single_source_extra 0/1, paused 0/1, review_on, review_target, min_order_p, note; every change → `order_rule_audit` who/when/old→new)
1. **Cadence** from the shop's own rhythm: bills per month over 90 days → days between orders → nearest of weekly / fortnightly / monthly
   (**nearest, not rounded up**; weekly is the fastest unless custom). The money tiers (20,000 / 4,000) are the fallback only for a supplier
   with fewer than 3 bills in 90 days. Re-seeded monthly for suppliers without an owner-set cadence; an owner-set value is never overwritten.
2. **Fixed order days**, not "every N days": weekly → Monday; fortnightly → alternate Mondays (anchor date stored); monthly → first Monday.
   **Kedar = custom, Monday + Friday.** Blocked days: **Sunday for everyone**; **Thursday blocked by default, OFF for Kedar** (delivers Thursdays).
   A holiday list (`order_holiday`, Shavez keeps it on his page) moves an order day to the previous working day.
3. **Lead 1 day** (same-evening delivery) — 2 where the supplier's own bills show later delivery (arrival date − order date, learned; shown, editable).
   **Safety 3.** Single-source extra 3 stays for everyone **except Kedar (waived)**.
4. **Cover cap: 14 days** for weekly and Kedar, **21** fortnightly, **45** monthly. Per order: weekly 7+1+3 = 11 days; Kedar 4+1+3 = 8 (≈ 55 boxes
   of the big four at most); fortnightly 18.
5. **Kedar ramp:** `review_on` = 4 weeks after go-live, `review_target` = weekly (Mon). On that date a Needs-you line shows what twice-weekly
   actually held (peak on-hand of the big four, in boxes) and offers one tap **"Move Kedar to weekly"** (and back). Any supplier may get custom
   days/review the same way.
6. **Minimum line ₹50** and **minimum order value per supplier** (default ₹500: a smaller proposal waits for the next order day). Strips rounding
   as today. `paused` = proposals shown, sending off, reason shown to staff.
### Shop-wide (`setting` `order.*`)
7. **Interim orders ON:** daily at the closing-stock read, an item whose cover falls below lead + safety (4 days) before its supplier's next order
   day raises an interim order for that supplier the next morning — only the shortfall to the next order day, never on a blocked day (a
   Thursday need → Wednesday; a Sunday need → Saturday) — shown as **"Beech ka order"**. Interim orders switch on automatically one week after
   the first fixed-day orders ran (`order.interim_from`), so the two are not confused.
8. **Notices to the ordering team** (senders: darpan, shavez, shivani, alisha — never the owner): the day's orders prepared and the first notice
   at **09:00**; reminders **12:00 / 15:00 / 17:00** — **contextual** ("Aaj 3 order: 1 bheja, 2 baaki — Kedar, Jubilee") and silent once all are
   sent. Channels: Web Push to each sender's subscribed phone + the count on the Purchase orders tile + the line on Darpan's Kal ka hisaab card.
   Unsent after 17:00 → merges into the supplier's next order day (one order, never two) and the owner's Needs you names it.
9. **Owner's Needs you, only:** an order still unsent on its next order day · a supplier's month running > `order.spend_alert_pct` (25 %) above
   its 90-day average · the Kedar review line. Optional Sunday one-liner "This week: N orders, ₹X, all arrived" (`order.sunday_line`, default on).
10. **Lists:** `orthotics_cycle` RETIRED (removed from the page; the json key kept empty). `never_reorder` / `on_demand` shown as **candidates**
    with figures: never-reorder = in stock, no sale in 60 days; on-demand = ≤ 2 sales in 180 days and unit value ≥ `order.on_demand_min_p`
    (₹200). The owner ticks; ticked names go to `order_rules.json` (the spine's copy AND the live rules), unticked are simply not proposed.
    `internal_use` kept as is. Per-item overrides on the same page: keep-in-stock, never-reorder, on-demand, max-on-shelf (bulky items).
11. **Freeze:** one owner tap "Freeze all medicine ordering" with a reason shown to staff; unfreeze the same.

## 3 · The screens
- **Owner — approvals page, section "Purchase orders"** (English): the rules page rewritten in plain words per supplier, e.g. "Kedar — Mon & Fri,
  delivered same evening, cover 8 days, cap 14, Thursday ok; review 24-Oct" — one line each, tap to edit; the candidates lists; the freeze;
  **one tap "Approve rules"** writes the approval row S403 waits for → medicine send unlocks. Two new blocks on the same page:
  **top of page, red, only when N > 0: "Out of stock both ends — N"**: items out or thin at the pharmacy (cover < safety) whose supplier
  answered *Nahi mila* on the last order line for that item — item · shelf qty · supplier · date said no; clears when a purchase lands or
  another supplier's line fills it. **Collapsible "New items this month — N"**: every item whose FIRST-EVER purchase line falls in the month:
  name · salt (`purchase_salt_marg`, blank if unknown) · supplier · manufacturer · MRP · purchase rate · first bill date — manufacturer and
  MRP **as the system holds them**: find which lane carries them (the stock/closing export's company column, the sale export's MRP, the Marg
  master); show "not in export" where absent; **never guessed**. Kept the whole month; last month one tap away.
- **Staff — Purchase orders screen** (Hindi): section 4 becomes "Aaj ke order (N)": per supplier the proposed lines (item · shelf · order qty,
  ± allowed, a line removable), **bhejo** → the S403 wa.me flow, marked SENT; "Beech ka order" cards the same; the contextual reminder text
  at the top; the freeze/paused reason when set. Shavez's holiday list on his page.
- **Darpan — Kal ka hisaab**: the count line. **Bhati**: nothing new.

## 4 · FROM pins (read live first — S407/S409 moved these; mismatch = stop that file and report)
| file | FROM |
|---|---|
| /root/finance/purchase_app.py · /root/finance/porders.py · porders.html | as S409 left them — read live (Sanjeevni) |
| /root/finance/spine/order_rehearsal.py · order_rules.json | 26-Sep bundle — read live (Sanjeevni; the rules json is data) |
| /root/finance/sanjeevni_approvals.py · finance_ui/finance_approvals.html | as S408 left them — read live (Needs-you lines + the two blocks; html is clinic — declared) |
| /root/finance/darpan_kal.py · darpan_kal.html | as S403 left them (401ee01c / 1bedb469) — the count line only |
| /root/portal/portal_push.py | read live — CALL its send path from finance (an HTTP or import door it already offers); do not edit it unless a one-line hook is unavoidable (clinic — declared) |
New module preferred: `/root/finance/order_rules.py` (settings, engine wrapper reading settings, the day scheduler) + one root cron line
(09:00 prepare/notice; 12:00/15:00/17:00 reminders; the nightly interim check after the closing-stock read), declared. No `finance_app.py`,
no portal tile, no grants. Restart `clinic-finance` only.

## 5 · The walk (scratch copy; own suppliers/items keyed W410*; the real 90 days as a read-only check; never sends, never pushes for real)
Cadence seed: a crafted supplier with 9 bills/90 d → weekly; 4 bills/90 d → fortnightly (nearest, not up); 2 bills → fallback tier; an
owner-set cadence survives re-seed · order days: Monday orders, Thursday skipped for everyone but Kedar, Sunday for all, a holiday moves the
day earlier · Kedar Mon+Fri, cover 8, cap 14, no single-source extra; another weekly supplier cover 11; fortnightly 18 capped 21 · interim:
an item falling under 4 days' cover raises exactly one interim order for the shortfall, on the right morning, not on a blocked day; off
before `order.interim_from` · min line ₹50 and min order ₹500 hold a small proposal · the 09:00 preparation makes one order per supplier due
that day; 12:00 text counts sent/unsent correctly and is silent when all sent; 17:00 unsent merges into the next order day (one order) ·
Needs-you: stuck order, > 25 % month, Kedar review with the boxes figure; nothing else about ordering reaches the owner's line list ·
"Out of stock both ends" fires on a crafted thin item + Nahi mila and clears on a crafted purchase · "New items" lists a first-ever item with
its fields and "not in export" where the lane lacks the value; a re-bought item is absent · candidates lists compute; a tick lands in
order_rules.json and the live rules · Approve rules unlocks medicine send (S403's 403 → 200) · freeze blocks send with the reason ·
real 90 days read-only: Kedar reads Mon+Fri custom, L.K. weekly, Yuvika untouched (orthotics) · S400–S409 walks re-run green.

## 6 · Done means
Kit `deploy_kits\S410_MEDICINE_ORDERING\` · installed, md5s read back · healthz 200 · published · `claude_code_briefs\REPORT_S410.md`
(owner lines first: the rules page as it now reads, the two new blocks, what the team sees at 09:00 and what his one tap does; ending with
`https://followup.dr-manoj.in/finance/approvals` and `https://followup.dr-manoj.in/finance/porders`).
