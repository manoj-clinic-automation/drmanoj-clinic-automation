# S428_STOCK_WATCH — Sunday full counts, spot counts three mornings a week, arrivals as provisional stock, the trace, the leakage budget, the watch list (D633)

**Sanjeevni project · session 283 · 27-Sep-2026 · brief `claude_code_briefs/S428_STOCK_WATCH.md` · runs after S427.**

## What the owner said (27-Sep)
"A full stock check is only possible on a Sunday — three hours — coordinated between Amir and Darpan." "Random and
purchase-triggered checks: minimum load in one sitting, three mornings a week, the cap flexible in settings; any item can
be selected by me or reported by Darpan." "Auto-selected on movement, turnover, purchase and such metrics." "The arrival
is tapped in the purchase app by the responsible staff; provisional stock does not depend on Darpan." "When Darpan flags
an unusual loss the system should analyse the sale and purchase history since the last matched stock check and narrow
down on human errors." "Over 1% is not recoverable but must be explained; full count once in two months, escalate to
monthly or downgrade to quarterly." A flag that ends unexplained reaches the owner the same day.

## What was built — `stock_watch.py` (new), mounted from `stock_app` and `stockmatch`
**3.1 Stock points.** `stock_point (item_norm, item, at, qty_units, source, by, expected_units, gap_units, status, settled_at, note …)`,
`source` ∈ full_count · spot · darpan · sales_test · receipt; `status` settled | provisional. A closed full count (the
S427 close) writes one point per counted item; every spot / Darpan answer writes its own. The trace and the watch read
this table and the spine only.

**3.2 Full counts — Sundays only, every `count.cadence_months` (2).** `stock_count_plan` opens by itself when a count
falls due (cadence months after the last closed full count's day). Amir's board shows the next `count.window_sundays`
(4) Sundays as buttons ("Ginti ka Sunday chunein"); Darpan's Stock milaan asks "Theek hai?" / "Nahi ho payega" (back to
Amir); the confirmed date is one line on the owner's Needs you and one line on Shavez's checklist (fetched by the page
from `/finance/stock/api/watch/plan/line`). No Sunday confirmed by the window's end → the plan lapses, one Needs-you line.
A count closed on a day that is not a confirmed Sunday does not move the cadence (the baseline count of 06-09 does; a
count on a confirmed Sunday does). **Auto-adjust** (`count.auto_adjust`): after each closed count with a frozen run,
leakage = allowance + small + big at cost against the period's sales (spine); two good counts running (≤ `count.good_pct`
1.0) → cadence 3; one bad count (≥ `count.bad_pct` 2.0) → 1; each move is audited, one Needs-you line ("Full count moved
to monthly: the count of dd-mm lost 2.4% of sales"), and the setting stays the owner's to reset. Each run is looked at once.

**3.3 Spot counts — three mornings a week (`spot.days` MON,WED,SAT), up to `spot.cap` (2).** The 06:30 job (one root cron
line, `stock_watch.py job`) writes `stock_spot_roster`: the owner's asks first (`stock_watch_ask`), then yesterday's
unanswered (carried), then items by a weighted rank-sum over the spine — turnover (value sold since the item's last
point), movement (strips or pcs a day), arrival (received within `spot.arrival_days` and not counted since — the tap or a
new `sp_purchase_line`), loss history (short at the last closed count), value (MRP per strip ≥ `spot.high_value_p`),
staleness (days since the last point) — weights `spot.w_*`. Countability: packing known; a strip item sold mostly whole
(loose share under 50%) or a WHOLE item; nothing counted within `spot.repeat_gap_days` (7) unless asked; a seeded
tie-break so two runs agree; a re-run on a day writes nothing new; cap 0 = off. If the job did not run, the first read of
Stock milaan on a spot morning builds the day's list. **"Aaj ki ginti"** on Stock milaan (on top): patte + goli boxes (nag
for a non-strip item), one "Bhej do" per item → a spot point: expected = the latest Marg closing − sales since + purchases
since (spine) + provisional arrivals; short within S427's allowance for the item (pro rata of its sales since its last
point) → a quiet loss point; larger → a dated loss line under the pinned staff block ("Aaj: TYRO BR 4 patte kam") and a
trace; a surplus → noted, never a loss. Unanswered → carried to the next roster day; three unanswered mornings in a week
→ one Needs-you line. **Owner "Count this"** on every Loss-desk line and on the watch card (a search box) → the head of
the next list. **Darpan any day:** "Stock batao" (any item → a darpan point) and "Kuchh gadbad hai" (item + what he sees +
his count if he has one → a point and the trace).

**3.4 Arrivals as provisional stock (`arrival.bill_grace_days` 3).** Expected stock reads `purchase_order_line` rows
tapped as arrived after the spine's latest closing (supplied packs × pack_size) that the spine's `sp_purchase_line` does
not yet carry for that item and supplier; such a term makes the point provisional. When the purchase reaches the spine
the point is re-evaluated and settled (`settle_provisional`, on every owner read and in the job). Tap ≠ bill quantity →
one line on the owner's watch card ("tap 8 strips, bill 10 strips" — read from S403's `billed_qty` log, never asked). A
tapped arrival with no purchase in the spine after the grace days → Amir's board "bill entry baaki: <supplier> <date>".

**3.5 The trace (`stock_trace`).** On every "Kuchh gadbad hai", on every spot loss beyond the allowance, and on every
Big-loss line of the desk (once per item per 30 days, when the desk is read). Anchor = the last settled point with gap 0,
else the last closed full count. From the anchor to now: sales, purchases (the spine; the tap beside), returns, points.
Seven checks in order, each explaining the gap exactly, in part, or ruled out: (1) the same purchase bill twice; (2) an
arrival tapped, no entry; (3) a pack-multiple gap (× pack, ×10/×15, boxes as strips); (4) a twin item — an alias, a name
within edit distance 2 or the same salt with a mirror-image surplus; (5) scheme strips on a bill; (6) short delivery (tap
under the bill); (7) a mistyped point (×10 off). Verdict explained / partly / unexplained; the fix pre-filled as one line
on Amir's board ("bill 4432 do baar: ek hataayein"). The owner's Traces card: gap in strips words, window, verdict,
findings, the fix. Darpan sees "Dekh liya" and, when an entry error was the cause, "Aapki baat sahi thi". Unexplained →
one Needs-you line the same day; two unexplained traces on one item within a month → the item joins the close-watch list.

**3.6 The budget and the watch (owner only).** Leakage of a month = loss points (gap < 0, at cost; the spine's MRP stands
in where no rate is on record) + count write-offs (allowance, small, big — not consumption) at cost, against the month's
sales (spine bills). The approvals page's Month section gains one line "Leakage ₹X = Y% of sales · budget 1%" green / red
(`sanjeevni_approvals.month_view` + ONE anchored line in `finance_ui/finance_approvals.html`, the parent's file, declared);
`leak.red_periods` (2) red months running → one Needs-you line. Watch list = top `spot.watch_size` by sales value + MRP ≥
`spot.high_value_p` + short at two closed counts + close-watch items: the close-watch card on the Loss desk (item, why,
last three points in strips words with their gaps, a three-month trend of sold / lost, Count this). Staff pages never
show the budget or a percentage.

**3.7 Settings** — the second heading "Counts & watch" on S427's card (`stock_watch.settings_view`; the desk's
`/pile/setting` door routes `count.` / `spot.` / `arrival.` / `leak.` keys to the watch), audited; the job reads them live.

**Calls made where the brief left room** (each reason in one line): a spot surplus is noted, not written as an S418 shelf
fix (the S418 layer compares to the count day; a spot point compares to today's expected stock); a count closed on a
weekday still writes its points but does not move the cadence (the brief: a count begun on another day is a spot count);
the cadence baseline is every closed count before the first plan existed (count 1 of 06-09); the "same bill twice" check
keys on supplier + bill + quantity; the scan link (S409) is read-only and not joined — the tap and the spine stand side by
side; auto-adjust reads the frozen run's `cost_p`, falling back to `mrp_p`; the roster job is also run once by the
installer so the log carries its first line; the trace on Big-loss lines is capped at 40 items per read.

## Pins (FROM read on the box 27-Sep-2026 after S427 → TO; built by `make_s428.py` from the live bytes, anchored edits)
| file | FROM | TO |
|---|---|---|
| /root/finance/stock_app.py (S427's TO) | 24c2b5fe7cacfe238751e487e52eb6d0 | 0e0fc043c4bbae75c6f1fc8149547cb7 |
| /root/finance/stockmatch.py (S427's TO) | e85807dab1f8672d482272e0d355fe28 | df5501ea436d887dfe14ed618adce7ea |
| /root/finance/stockmatch.html (S427's TO) | ecd039f4f64d5be6a15d7ffbbcdf3950 | 4ddf0073099086f024c9e12412abf1ec |
| /root/finance/stock_amir.html (S427's TO) | 244ac6eeb0117b14f2c3c7fa1576f728 | e5e229270de7a71a624505bfd0ca11b7 |
| /root/finance/stock_loss.html (S427's TO) | fdd913e75677580a7897fe2631196c4c | 29809ba1e3ce415fc43f5df614f7ea0e |
| /root/finance/sanjeevni_approvals.py (v1.10 → v1.11) | 64548b9b36770992dd3da2081e52ffe1 | 3999c4ced7aaf098eeeb00d696014cab |
| /root/finance/finance_ui/finance_approvals.html (PARENT'S — one anchored line) | 588975fcff2644db115b63058c4d62dc | 9d1eddc8f96856674e1dc3638490bbeb |
| /root/finance/packs_checklist.html (one anchored line) | 6f027a7e74314584bfb5ae88607e6275 | 12ac3f27f532e9604b77f8affd47c742 |
| /root/finance/stock_watch.py (new) | — | ec3999093387d979b754276b9911929d |

One root cron line: `30 6 * * * cd /root/finance && FINANCE_DB=/root/finance/finance.db /root/wa/venv/bin/python3 -B
/root/finance/stock_watch.py job >> /root/finance/stock_watch.log 2>&1 # S428_STOCK_WATCH` (the crontab is backed up first).
Read only: `porders.py`, `purchase_app.py`, `darpan_kal.py`, the spine. Not touched: `loss_piles.py`, `qty_words.py`,
`stock_hub.html`, `packs.py`, `finance_app.py`, `portal.py`. Restarts `clinic-finance` only. `finance.db` is backed up
first; the tables `stock_point`, `stock_count_plan`, `stock_spot_roster`, `stock_watch_ask`, `stock_trace`,
`stock_watch_loss_line`, `stock_watch_notice`, `stock_watch_adjust` are additive; `seed_s428.py` writes the settings only
where absent, after a green restart.

## Proof
`walk_s428.py` — the REAL patched app over SCRATCH copies of the live database AND the spine (crafted W428 items, sales,
closings, purchases, MRPs, salts), lines found by key: the gates (bhati, darpan, shavez refused on the owner's watch;
darpan allowed on his; amir picks, bhati and darpan cannot) · the wiring (the watch card on the desk's JSON, the four
piles unchanged, 'Count this' and the second heading on the page, a watch setting saved through the desk's door and
audited, a bad value refused, a loss-desk key still working) · the plan: the cadence set to half a month makes the count
due → a plan with four Sundays; Needs you says so; Amir's board has the buttons; Amir picks, Darpan says "Nahi ho payega"
→ back to Amir; picks again, "Theek hai" → confirmed; Needs you and the checklist line carry the date; a repeat writes
nothing; a count closed on a Tuesday leaves the last full count at 06-09; a count on a confirmed Sunday moves it · auto-
adjust: a 2.4% count moves 2 → 1 with its line; two 0.8% counts move 2 → 3 (the first alone moves nothing) · the roster:
the preview is the same twice; on the Monday the ask comes first, then ≤ cap items; the arrival with high turnover ranks
first; a loose-heavy item never; an item counted two days ago never; a re-run writes nothing; a Tuesday writes nothing ·
Darpan's answers: 1 tab short within the allowance → a quiet point; 4 strips short → a dated loss line under the block
and a trace; a surplus → "zyada", no loss line, provisional while the tap is unmatched; unanswered → carried to the
Wednesday; a repeat writes nothing; others refused; three unanswered mornings → Needs you; "Stock batao" in botal words;
his search box · arrivals: a tapped order line the spine lacks raises the expected stock and marks the point provisional;
the purchase reaching the spine settles it; tap 8 / bill 10 → the owner's line; 5 days with no entry → Amir's line ·
the trace: seven crafted cases, one per check, each explained with the right fix; an unexplained case names its window
and reaches Needs you; two unexplained → close-watch; "Kuchh gadbad hai" through his page → the trace and "Aapki baat
sahi thi"; "Dekh liya"; Amir's fix line; a trace on every Big-loss line once · leakage green at 0.6%, red at 1.4%; the
Month section's line; two red months → Needs you; the watch list with TYRO BR and ROSIKA FORTE, costly items, three-month
trends · the word gate on the rendered pages and the watch's texts; no percentage on Darpan's texts · the S427 doors kept.
**Negative control:** the same scenario on the box as it is goes red. Then **S427's walk**, **S404's walk** (on the 14:04
backup of 26-Sep) and **S403's walk** (on the 17:45 backup) are re-run on the patched files. `figures_s428.py` prints
whether a count is due and what Amir sees, the next morning's roster with its reasons, the watch list, this month's line.

## Run
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S428_STOCK_WATCH/install_S428_STOCK_WATCH.sh
```
Undo: put back the eight `.bak_S428_<from8>` files, remove `/root/finance/stock_watch.py`, restore
`/root/finance/crontab.bak_S428_<stamp>` (or delete the one S428 line), `systemctl restart clinic-finance`, healthz 200.
The seeded settings and the new tables are data and stay; the database backup is used only if the owner says so.
