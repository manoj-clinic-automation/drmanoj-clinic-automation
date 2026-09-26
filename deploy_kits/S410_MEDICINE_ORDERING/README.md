# S410_MEDICINE_ORDERING — the medicine buying rules as settings · fixed order days · the ordering team's day · the owner's page

**Session 283 · 26-Sep-2026 · decision D626 · Sanjeevni.** The owner finalised the WHAT on 26-Sep after a full sitting; his approval of
these rules is the standing approval — the paper purchase-order sheet is retired; the system's record (who sent, when, what arrived, what
was billed) replaces it. Runs after the S405–S408 paste (S407 and S409 moved `purchase_app.py` / `porders.py`; every pin read live).
Orthotics are NOT touched (S403's keep-in-stock runs them).

## What was built
**NEW `/root/finance/order_rules.py`** (mounted by `porders.init`, fail-soft; every path under `/finance/porders/` so the porders unit's gate
holds; the cron worker under the venv python because the push library lives there).
1. **Per-supplier rules** (`order_supplier_rule`; every change audited in `order_rule_audit` who / when / old → new). Seeded from the
   shop's own rhythm over 90 days of effective bills: the **median gap between bill days → the nearest of weekly / fortnightly / monthly
   (nearest, never rounded up; a tie goes to the faster)**; fewer than 3 bill days → the money tiers (₹20,000 / ₹4,000 a month) decide.
   Re-seeded on the 1st; **a field the owner set is never overwritten** (`owner_fields`). Lead 1 (same-evening delivery), 2 where the
   supplier's own orders show later arrival (learned from `purchase_order` arrival taps / Marg bill dates, shown, editable); safety 3;
   single-source extra 3 unless waived; cover cap 14 / 21 / 45 by cadence; minimum order ₹500; pause with a reason; review date + target;
   note. **Kedar (D626, owner-set from the seed): custom Mon + Fri, blocked Sunday only (Thursday open), extra waived, cap 14, review
   4 weeks after go-live → weekly.** The orthotics vendor never gets a row.
2. **Fixed order days.** weekly → Monday; fortnightly → alternate Mondays from an anchor (the first Monday on/after go-live); monthly → the
   first Monday; custom → the named days. Blocked days per supplier (`SUN,THU` default); a nominal order day on a blocked day or on a
   holiday (`order_holiday`, Shavez's list on his page) moves to the previous working day. Cover per order = the longest gap to the next
   order day + lead + safety (+ the extra), capped: weekly 11 (single-source 14), Kedar 8, fortnightly 18 (21).
3. **The engine is S225's, not a second one.** `purchase_app._latest_snapshot / _pace / _last_purchase / _in_transit / _carried_shorts /
   plan_line / _staff_qty / _staff_send` are called; the rule's cover is handed to `plan_line` as its cadence so the engine's own lead /
   safety / extra cancel exactly and every rail (box, dead, thin, spike, ₹50 line, the owner's 10-then-tens) stays. On top: per-item
   overrides (`order_item_rule`: keep-in-stock, max-on-shelf, never, on demand, internal), the lists, the minimum order (a proposal under
   ₹500 is HELD for the next order day unless an item is out of stock), the pause, the freeze.
4. **Interim orders** (`order.interim`, ON from `order.interim_from` = go-live + 7): an item whose cover would fall under lead + safety
   before its supplier's next order day raises one interim proposal for that supplier for the shortfall to that day — never on a blocked
   day (a Thursday need is caught on the Wednesday check, a Sunday need on the Saturday), never for a supplier ordering that day.
5. **The day** (`order_proposal`): the 05:30 nightly merges yesterday's unsent proposals into each supplier's next order day (one order,
   never two; the next proposal says "28-Sep ka order bhi isme"); 09:00 prepares one proposal per supplier due + the interim ones and
   sends the first notice; 12:00 / 15:00 / 17:00 the contextual reminder ("Aaj 3 order: 1 bheja, 2 baaki — Kedar, Jubilee"), **silent once
   all are sent**; once per slot (`order_notice`). Channels: **Web Push** to each sender's subscribed phones through `ring_common.push_user`
   (portal_push's own store and VAPID key; the payload the S366 service worker already shows; tap opens `/finance/porders`) + the line on
   Darpan's Kal ka hisaab card + the count in the screen's own section. Recipients `order.notice_to` = darpan, shavez, shivani, alisha —
   never the owner. **Not done: the count on the portal TILE** — the portal has no generic badge (its counts are per-tile scripts inside
   `portal.py`), and this brief does not open `portal.py`; named in the report.
6. **Sending** (`POST /finance/porders/api/day/send {proposal_id, lines}`, senders + owner): refused while frozen (423) or before the
   owner's approval (403, S403's row); the sender's ± and removals are honoured; the order is written by `_staff_send` (SENT, audited, the
   wa.me link returned), section Medicines, the proposal marked sent (who, when, order id), a merged earlier proposal closed with it.
7. **Owner's Needs you, only:** an order still unsent on its next order day · a supplier's month running more than `order.spend_alert_pct`
   (25 %) above its 90-day pace (pro-rated to the day, from the 10th) · the Kedar review line with the peak on-hand of the big four in
   boxes of 10 strips and the one tap **Move Kedar to weekly** (and back) · the freeze · the Sunday one-liner (`order.sunday_line`).
8. **The owner's page** (`/finance/approvals`, section Purchase orders): the rules fold rewritten — one plain line per supplier ("Kedar —
   Mon & Fri, delivered same evening, cover 8 days, cap 14, Thursday ok, single-source extra waived; review 26-Oct-2026 → weekly"), tap to
   edit / pause / move; the shop-wide numbers; **candidates**: never-reorder (in stock, no sale in 60 days) and on-demand (≤ 2 sales in 180
   days, unit value ≥ ₹200) with figures, a tick lands in `order_rules.json` (the spine's copy, version bumped, `orthotics_cycle` kept
   empty) AND the live rules; the item overrides; **Freeze all medicine ordering** with a reason shown to staff; **Approve rules** (S403's
   row). **Top of page, red, only when N > 0: "Out of stock both ends — N"** (item · shelf qty · supplier · date said no; out or thin at the
   pharmacy and the supplier answered Nahi mila on the last order line; clears when a purchase lands or another supplier fills it).
   **Collapsible "New items this month — N"**: every item whose first-ever purchase line falls in the month — name · salt
   (`purchase_salt_marg`) · supplier · manufacturer · MRP · purchase rate · first bill; manufacturer from the spine's `company` fact (Marg's
   ITEM_MASTER), MRP from its `mrp` fact (SALT_WISE_ITEM_LIST), **"not in export" where absent, never guessed**; last month one tap away.
9. **Staff screen** (`/finance/porders`, Hindi): section 4 "Aaj ke order (N)" — per proposal the lines (item · shelf · qty, ±, hatao), bhejo,
   SENT marks, "Beech ka order" cards, the contextual text, the freeze / paused reason; section 5 "Chhutti ke din" for the senders; the
   engine's full plan one tap away. **Darpan's card**: "Aaj ke order — N (M bheja)". Bhati: nothing new.

## Pins (FROM read live 26-Sep-2026 10:43 IST → TO; built by `make_s410.py` from the live bytes)
| file | FROM | TO |
|---|---|---|
| /root/finance/porders.py (v1.0 → v1.1: the mount, `today`, the freeze gate) | d08f59e2fb4e42e173f135f06da28787 | c75fc91060d127fd05c56b6b81ad9b97 |
| /root/finance/porders.html (section 4 + 5) | 76a173af5faee643fa0d0139731b10e8 | 5913e99302930d9fae24c42ac630f010 |
| /root/finance/sanjeevni_approvals.py (v1.9 → v1.10; `NEEDS_YOU_WITHOUT_S410=1` for S400's frozen walk only) | 3cde91fbfead8e698ca1e3981362a6d3 | c5b93455a69083a6b8d634014898bd30 |
| /root/finance/finance_ui/finance_approvals.html (clinic, declared) | 77c79211845f3416a3211d22ced3d7db | 7de583154b87bd4d3ba13ce6de1c53a9 |
| /root/finance/darpan_kal.py | 401ee01c7cbd49cea1c34665c99bab60 | 803970bd04c7203632b98d9659923b3b |
| /root/finance/darpan_kal.html | 1bedb46991bc5b531e809519c50ee990 | a4eecb21a88f793ab5c81b75dab20a51 |

Read only, not patched: `purchase_app.py` (cdd4e9c0), `spine/order_rehearsal.py` (02582fbe; it reads the same `order_rules.json` the ticks
write), `spine/order_rules.json` (data; written by the owner's ticks at run time), `portal_push.py` / `ring_common.py` (called, never edited).
Restarts `clinic-finance` only. `finance.db` and the crontab backed up first. One root cron line
`0,30 5-17 * * * … order_rules.py tick` (the worker acts only at 05:30 · 09:00 · 12:00 · 15:00 · 17:00).

## Proof
`walk_s410.py` — the REAL finance app over a scratch copy of finance.db, its own suppliers / items keyed W410*, today fixed to Monday
28-Sep-2026, the push to a stub file, no WhatsApp opened: the mount and the gates · the seed (9 bill days 10 apart → weekly; 4 days 14
apart → fortnightly, nearest not up; 2 bills → the money tier; Kedar's D626 row; Yuvika absent; the real 90 days: L.K. and Gunina weekly)
· an owner-set cadence survives a re-seed · the calendar (Mondays; Kedar Mon + Fri; alternate Mondays; first Monday; Thursday → Wednesday
for everyone but Kedar; Sunday → Saturday; Shavez's holiday moves the day; bhati cannot) · cover 11 / 14 / 8 / 18 / 21 · the plan (cover
and quantity per rule; the ₹1 line dropped; the ₹400 proposal held; the short line carried; Yuvika never) · interim (one order for the
shortfall, off before `interim_from`, not on Thursday / Sunday, on Saturday / Wednesday) · 09:00 prepare + notice to the four senders ·
12:00 / 15:00 / 17:00 texts count sent / unsent · send refused before the approval, bhati refused, darpan sends with an edit, one SENT
order, the repeat guard · the freeze (423 on both send doors, the reason on the staff state and in Needs you) · the merge into the next
order day, the owner's line on that day, one order (carried_from), the line gone after the send · the month above pace (the on-pace
supplier silent) · the Kedar review line with the boxes figure and the one tap, and back · nothing else about ordering in Needs you ·
Out of stock both ends fires and clears · New items (salt, supplier, "not in export", rate, first bill; a re-bought item absent) ·
candidates · a tick lands in `order_rules.json` and holds the item back; untick · the pages · no 10-digit number anywhere ·
**negative controls on the unpatched files**; then **S409's, S408's, S407's, S406's, S405's, S404's, S403's, S400's and S402's own walks
re-run** on the patched files.

## Run
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S410_MEDICINE_ORDERING/install_S410_MEDICINE_ORDERING.sh
```
Undo: the six `.bak_S410_<from8>` files back, remove `order_rules.py`, remove the S410 cron line (`crontab.bak_S410_<stamp>` holds the old
crontab), `systemctl restart clinic-finance`, healthz 200. The tables, rows and settings are inert data; the database backup is used only
if the owner says so.
