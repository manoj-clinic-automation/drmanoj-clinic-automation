# Claude Code brief — S428_STOCK_WATCH (Sunday full counts, spot counts three mornings a week, arrivals as provisional stock, the trace, the leakage budget, the watch list)

Written 27-Sep-2026 by the Sanjeevni chat (S283). Read `CLAUDE.md` first. **Kit S428 · decision D633** (claimed on the System Board).
Runs AFTER S427 (read its report and pins live). **Owner-facing English; Darpan's and Amir's pages Hindi. Sanjeevni-owned.** Touches ONE
parent file by one anchored line (finance_ui/finance_approvals.html — declared in §4).

## 1 · The owner's words (27-Sep)
"A full stock check is only possible on a Sunday — three hours — and those Sundays are coordinated between Amir and Darpan; Darpan is
necessary." "Random and purchase-triggered checks: minimum load in one sitting, frequency can be higher — three mornings a week, not a
daily chore; the cap flexible in settings; any item can be selected by me or reported by Darpan." "Auto-selected on movement, turnover,
purchase and such metrics." "The best time is the morning: when he comes there are no sales, only the two Marg exports — two minutes —
then half an hour free." "The arrival is tapped in the purchase app by the responsible staff with the scanned bill; provisional stock
does not depend on Darpan." "When Darpan flags an unusual loss — he could not find one or two boxes — the system should analyse the sale
and purchase history since the last matched stock check and narrow down on human errors of purchase entry or other things." "Over 1%
is not recoverable but must be explained; full count once in two months, escalate to monthly or downgrade to quarterly." A flag that
ends unexplained reaches the owner the same day (his yes).

## 2 · What exists (read live)
The spine `/root/finance/spine/spine.db` (`sp_close` per stock export, `sp_sale_line`, `sp_purchase_line`, `sp_item.packing/unit_kind`,
`sp_alias`, `sp_move`); the counts (`stock_count`, `stock_diff`, the S404/S418/S427 desk and `stock_writeoff_run`); Darpan's Stock milaan
(`stockmatch.py/html`, cards: Phir se gino → S427's Dobara ginna hai, Bina bill?, the staff block); Amir's board `stock_amir.html`;
purchase orders `purchase_order` / `purchase_order_line` (`packs, pack_size, units, supplied, short, missing, arrived_by, arrived_at`;
`/finance/porders/api/arrive`, S403/S410) and the ordered-vs-supplied log; the scan link (S409, asset app — read-only); `order_rules.py`
(the setting pattern with hints, `order_notice`); `sanjeevni_approvals.py` v1.10 (Needs-you lines, each fail-soft) and the approvals
tree's Month section (S368); `darpan_kal.py` `_month_rows`; the S408 Shavez checklist page; `qty_words.py` (S427).

## 3 · The build (D633) — NEW `/root/finance/stock_watch.py` (blueprint, tables, the 06:30 job), mounted from stock_app the S418 way
### 3.1 Stock points — the one table every count writes
`stock_point (id, item_norm, item, at, qty_units, source, by, expected_units, gap_units, status, settled_at, note)`; `source` ∈ full_count ·
spot · darpan · sales_test · receipt; `status` ∈ settled · provisional. A closed full count writes one point per counted item; S427's
sales-after-count closes write `sales_test`; everything below writes its own. The trace (3.5) and the watch (3.6) read only this table
plus the spine.

### 3.2 Full counts — Sundays only, every two months, Amir picks and Darpan confirms
Settings `count.cadence_months` 2 · `count.window_sundays` 4 · `count.auto_adjust` 1 · `count.good_pct` 1.0 · `count.bad_pct` 2.0.
Table `stock_count_plan (id, due_from, sunday, picked_by, picked_at, confirmed_by, confirmed_at, status)`. When a count falls due
(cadence months after the last closed full count's day), the plan opens: Amir's board shows the next `window_sundays` Sundays as buttons
("Ginti ka Sunday chunein"); Darpan's Stock milaan shows the picked date with "Theek hai" (or "Nahi ho payega" → back to Amir); the
confirmed date is one line on the owner's Needs you and one line on Shavez's checklist. No Sunday confirmed by the window's end → one
Needs-you line. The full-count sheet opens for a *full* count on the confirmed Sunday only; a count begun on another day is a spot
count and does not move the cadence. Auto-adjust: two closed counts running with leakage ≤ good_pct → cadence 3; one ≥ bad_pct →
cadence 1; each change is one Needs-you line ("Full count moved to monthly: last count 2.4%") and the setting is the owner's to reset.

### 3.3 Spot counts — three mornings a week, up to a cap, chosen by score
Settings `spot.days` MON,WED,SAT · `spot.cap` 2 · `spot.watch_size` 20 · `spot.high_value_p` ₹500 · `spot.repeat_gap_days` 7 ·
`spot.arrival_days` 3 · weights `spot.w_turnover 3 · w_movement 2 · w_arrival 3 · w_loss 3 · w_value 1 · w_stale 2` (advanced).
The 06:30 IST job (one root cron line, declared) writes the day's roster `stock_spot_roster (day, item_norm, item, reason, rank,
asked_at, answered_at, qty_units, point_id)`: first the owner's asks (`stock_watch_ask`), then the items ranked by a weighted rank-sum
over the spine — turnover (value sold since the item's last stock point), movement (strips or pcs per day), arrival (received within
`arrival_days` and not counted since — from purchase_order_line.arrived_at or a new sp_purchase_line), loss history (short at the last
closed count; twice for two running), value per piece (MRP ≥ high_value_p), staleness (days since the last point); countability gate:
packing known, `unit_kind` WHOLE, loose-sold share under 50%, else excluded unless asked by the owner. Nothing repeats within
`repeat_gap_days` unless flagged; a seeded tie-break so two runs on one day agree. Cap 0 = off.
**Darpan's card "Aaj ki ginti"** on Stock milaan (present from the morning on a spot day, on top): each item with patte + goli boxes
(pcs box for a non-strip item), one "Bhej do". Each answer → a `stock_point` (spot); expected = the latest sp_close + sales since −
returns + provisional arrivals (3.4); provisional if any arrival term is provisional. Short within S427's allowance-for-the-item (pro
rata of sales since the last point) → written off quietly as a loss point; larger → a dated loss line appended to the pinned staff
block ("Aaj: TYRO BR 12 patte kam") and to the owner's watch card; surplus → the shelf corrected (the S418 shelf-fix layer) and noted.
Unanswered → carried to the next roster day; three misses in a week → one Needs-you line.
**Owner "Count this"**: a button on every Loss-desk line and on the close-watch card, plus a search box (sp_item) on the desk's watch
card → `stock_watch_ask`, head of the next roster. **Darpan any day**: "Stock batao" (item search + boxes → a `darpan` point, counted like
a spot answer) and "**Kuchh gadbad hai**" (item + what he sees → a loss point + the trace 3.5). Both are on Stock milaan, below the card.

### 3.4 Arrivals as provisional stock — from the purchase app's tap, never a Darpan step
Setting `arrival.bill_grace_days` 3. Expected stock for any point reads arrivals from `purchase_order_line` (arrived_at after the spine's
latest `as_on`, quantity = supplied packs × pack_size) that the spine's `sp_purchase_line` does not yet carry for that item and
supplier; such a term is provisional. When the purchase reaches the spine (Amir's Marg entry via the export, or the bill read), the
point is re-evaluated and settled; tap ≠ bill quantity → one line on the owner's desk "tap 8 strips, bill 10" (reuse the S403
ordered-vs-supplied log; the diff-desk cause `received but not entered` is written by the system, never asked). A tapped arrival with no
purchase in the spine after `bill_grace_days` → a line on Amir's board "bill entry baaki: <supplier> <date>". An item with no tapped
arrival simply has a zero arrival term — no stopgap.

### 3.5 The trace — automatic, on every flag and on every Big-loss line
`stock_trace (id, item_norm, opened_at, trigger, anchor_at, window_from, window_to, gap_units, verdict, findings_json, fix_json, status)`.
Anchor = the last settled point with gap 0 (or the last closed full count). Rebuild from the anchor to now: sales (sp_sale_line),
purchases (three sources side by side: the tap, the scan link if any, sp_purchase_line), returns, consumption vouchers, shelf fixes,
points. Checks, in order, each either explaining the gap exactly or ruled out: (1) the same purchase bill twice (supplier + bill + qty);
(2) an arrival tapped, no entry; (3) a pack-multiple gap (× pack_size, ×10/×15 strip confusion, boxes as strips); (4) a twin item —
an sp_alias or a name within edit-distance 2 / same salt with a mirror-image surplus in the window; (5) scheme strips on a bill not
entered (free qty on sp_purchase_line where present); (6) short delivery (tap < bill); (7) a mistyped point (a point ×10 off its
neighbours). Verdict: **explained** (fix pre-filled as one line on Amir's board — "bill 4432 do baar: ek hataayein"), **partly** (the
found part fixed, the rest a dated loss), **unexplained** (nothing in the records accounts for it; window = between the last clean
point and the first short one). Owner's desk: a "Traces" card (gap in strips words, window, verdict, findings, the fix line). Darpan
sees "Dekh liya" and, when an entry error was the cause, "Aapki baat sahi thi". Unexplained → one Needs-you line the same day. Two
unexplained traces on one item within a month → the item joins close-watch.

### 3.6 The budget and the watch — owner only
Settings `leak.budget_pct` 1.0 · `leak.red_periods` 2. Leakage of a month = every loss point + every count write-off (allowance,
small, big; not consumption) at cost, dated by the point or the count day. The approvals page's Month section gains one line per month
"Leakage ₹X = Y% of sales · budget 1%" green/red (sanjeevni_approvals.py + ONE anchored line in `finance_ui/finance_approvals.html`,
the parent's file, declared, read live before the patch); `leak.red_periods` red months running → one Needs-you line. Watch list =
top `spot.watch_size` by sales value + MRP ≥ high_value_p + short at two closed counts; **close-watch card** on the Loss desk (item, last
three points in strips words, gaps, a monthly trend line, Count this). Staff pages never show the budget or a percentage.

### 3.7 Settings — the second heading "Counts & watch" on S427's card, strips words, audited; the 06:30 job reads them live.

## 4 · Pins — read live AFTER S427 lands: loss_piles.py, stock_loss.html, stock_app.py (the mount + Count this), stockmatch.py/html,
stock_amir.html, sanjeevni_approvals.py (Needs-you lines, fail-soft), darpan_kal.py (read-only), `finance_ui/finance_approvals.html`
(PARENT'S — one anchored line, declared), the S408 checklist page (one line; its file is named in REPORT_S408). READ ONLY: porders.py,
purchase_app.py, the spine. NEW stock_watch.py (+ its Hindi/English strings in the pages it patches). One root cron line 06:30 IST,
declared. Restart `clinic-finance` only.

## 5 · Walk (scratch copy; own rows keyed W428*)
A crafted last closed count 60 days back → a plan opens with four Sundays; Amir picks, Darpan confirms, Needs you and the checklist
carry the date; a count begun on a Tuesday is a spot, the cadence unmoved; auto-adjust moves 2 → 1 on a 2.4% count and 2 → 3 after two
0.8% counts, one line each · roster: on a MON/WED/SAT the job writes ≤ cap items, an owner ask first, an arrival within 3 days next, a
loose-heavy item never, no repeat inside 7 days, the same roster on a re-run · Darpan's answer: short within allowance → quiet point,
short beyond → block line + watch card, surplus → shelf fix, unanswered → tomorrow, three misses → Needs you · arrivals: a tapped
order line not yet in sp_purchase_line raises expected stock and marks the point provisional; the purchase's arrival settles it;
tap 8 / bill 10 → the owner's line; 4 days with no entry → Amir's line · trace: seven crafted cases, one per check, each explained
with the right fix; an unexplained case names its window and reaches Needs you · leakage line green at 0.6%, red at 1.4%, Needs you
after two red months · no "unit" in any rendered string · bhati/darpan/shavez refused on the owner cards; darpan allowed on his ·
S427's walk still green · negative control.

## 6 · Done means
Kit `deploy_kits\S428_STOCK_WATCH\` · installed · published · `claude_code_briefs\REPORT_S428.md` — owner lines first: whether a full
count is due today and what Amir will see; tomorrow's roster (the real items and why each was chosen); the watch list as it stands;
this month's leakage line; ending with `https://followup.dr-manoj.in/finance/stock/page/loss?count=1` and
`https://followup.dr-manoj.in/finance/stockmatch`.
