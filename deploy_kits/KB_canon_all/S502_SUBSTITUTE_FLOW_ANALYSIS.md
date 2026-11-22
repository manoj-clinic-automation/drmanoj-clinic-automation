# S502 — The "not delivered / out of stock / substitute" path: what is wrong, and the flow to build
*Sanjeevni chat · 22-Nov-2026 · read on the 22-Nov 03:17 database copy (device VM only) + the live page as manoj 10:0x IST · code: order_flow.py v1.5 (de570252), order_s778.py, order_track.py*

## 1 · What the owner saw (his words 10:06) and what the data says

| His words | What is actually there |
|---|---|
| "CHEXID D, OLMETIME etc are confusing entries — seem from the 13-Nov order, yet not delivered, no way to confirm this" | CHEXID D: ordered 13-Nov (order 99) 20 strips, **15 came on the bill, 5 missing**; the 5 went into the Old-orders box (carry 45); **Darpan tapped "Ab nahi milta" 20-Nov 12:12** on that carry → the team row. OLMETIME H 20: ordered 10-Nov (order 89) 10 strips, **1 came**, 9 carried; Darpan's tap 20-Nov 12:11. Neither was on the 20-Nov Gunina order. The team row shows only "9 strips · Tapped 20-11 · Last bought 13-11 · out of stock" — the order, the came/missing split, who tapped and what "out of stock" means (the DEALER's word, not our shelf) are all hidden. |
| "old ones keep piling up" | **"Ordered again" is treated as settled.** VFER 500 was ordered 24-Oct, 02-Nov, 04-Nov, 10-Nov, 13-Nov — five orders, nothing came since 18-Sep — and every older row reads "settled · ordered again"; only the newest row shows a problem, and only after Darpan's tap. PANTAVIN 40 the same across 04/10/13-Nov (carry chain 20→26→35→42); RIB BELT 04/13-Nov; TYRO BR, C2CALZ, FLACORT 6, LINVIZ 600 the same pattern (Kedar). Nothing ever escalated to him; the chain is in `order_carry` (from_line_id → done_order_id) but never read as one shortage. |
| "TOLTRIS PLUS now substituted with TOLIVANT is still showing with no proper resolution path" | TOLTRIS PLUS: ordered 12-Oct (order 28) 50 strips, nothing came; **he** tapped out of stock 12-Nov (a month later); TOLIVANT PLUS was then bought 02-Nov (36) and 13-Nov (24) — the substitute in practice — but **no link exists**: TOLTRIS stayed on his list 41 days (the page's "oldest 41 days") with only Wait / Drop. He pressed Drop this morning; the row now reads "settled · your word given". **Drop = `na_answer('stop')` = item rule `never` (never suggested again until a Marg bill brings it)** — the right outcome by accident; the button never said so. |
| "multiple options for such items are not there, no flow for substitute" | For an out-of-stock row his buttons are: *Order from <other dealer>* (only when another dealer has ever billed that medicine — none of the five qualifies), *Wait — order next week* (7 days, then silently back on the ordering list as 'keep'), *Drop it* (rule never). **No substitute path at all for an out-of-stock medicine.** The only "substitute" the system knows is reception's "Substitute aaya" on an arrived-short line (`order_flow_mark` kind 'sub', no name — reads "<item> → substitute"), answered by *Substitute OK / Not OK — return*; it links to no bill line and changes no ordering rule. |

## 1b · VFER 500 — the real cause (his word 10:26: "V FER is in 2 names and both are in stock")
Marg renamed **VFER 500 → V FER 500 on 27–28 Oct** (the Marg watch found it on 05-Nov: `marg_hand_change` rows 22/23, kind `rename`, status **open** ever since; the same for ANKLE BINDER XL TYNOR ↔ ANKLE BINDER TYNOR XL, 09-Oct). Since then Shivaaz bills it as V FER 500 — **9 strips on bill 4043 (02-Nov), 12 on bill 4100 (05-Nov); Marg stock today 25:4**. The order lines still say VFER 500; `norm()` keeps the space, so the two are different items to the name list (`med_names.forms`), to the order<->bill match (`stock_figure.carried` by the spine key), to `order_s778.forms` (so `clear_by_bills` never clears na 9) and to the ledger (two pages: VFER 500 frozen at 3:5 of 27-10; V FER 500 live). Result: a phantom "not delivered 5 times" shortage, four re-orders the dealer HAD supplied, a wrong out-of-stock ask, and the ordering list still suggesting VFER 500 from a stale 3:5.

**The fault is structural:** the rename memory (`item_alias`, `marg_item_rename`) knows only PLANNED renames (the 22 orthotic names); a rename made in Marg without a plan is detected by the Marg watch and goes nowhere. **Fix (in this kit):** a detected rename pair becomes a one-tap question for him — on the shortage row itself and in Needs-you — "VFER 500 and V FER 500: the same medicine, renamed in Marg 27-Oct? **Yes, same medicine** / No, two items". Yes -> a `marg_item_rename` row (planned_by 'marg watch', verified from the detection) + the pair in the one name list + the hand-change rows closed -> `detect_supplies` marks the four lines billed (came), na 9 clears by bills, the ledger and the stock pages read one item. No -> the pair is remembered as two items and never asked again.

**Inline stock and ledger (his ask):** every shortage row opens the medicine's Marg stock, expected stock and the ledger inline (the ledger page in a frame of the row, same origin) — and names its partner name's stock when a rename pair exists, before anyone calls it missing.

## 2 · The faults (to mint at the close; F-1574 onward)
1. **Team row without its facts** — order day/number, ordered/came/missing, who tapped and when, that "out of stock" is the dealer's word; "Last bought" unexplained. (OLMETIME, CHEXID, all five.)
2. **"Ordered again" = settled** — a medicine the dealer never sends is re-ordered week after week and nothing escalates (VFER 500 ×5, PANTAVIN 40 ×4, RIB BELT ×2, TYRO BR, C2CALZ, FLACORT 6, LINVIZ 600). The carry chain is never read as one shortage.
3. **No substitute flow for an out-of-stock medicine** (TOLTRIS PLUS → TOLIVANT PLUS lived only in people's heads for 6 weeks).
4. **"Drop it" hides its meaning** (rule `never`); no "not needed now" option that merely leaves the list and lets the normal ordering rule speak again.
5. **"Order from another dealer" only when one has billed before** — none of the five; no way to choose a dealer.
6. **Reception's "Substitute aaya" records no name, ties to no bill line, changes no rule**; his OK/return has no effect on ordering.
7. **The Hub's one line said "21 medicines still missing" while the page said 6** (10:1x) — the same reader, two numbers; to find at the build (needs_you_line vs owner_body).
8. **A rename made in Marg without a plan is detected and then ignored** — no path from `marg_hand_change` kind 'rename' to the identity (item_alias / med_names / spine key); VFER 500 <-> V FER 500 open since 05-Nov, ANKLE BINDER XL TYNOR since 09-Oct. The gravest of the list: it manufactures false shortages and re-orders.
9. **The shortage pages never show the medicine's stock** — a row says "nothing came" beside a shelf holding 25 strips.
10. Darpan's and reception's team blocks say only "Doctor sahab ka faisla baaki" — after his word they learn nothing (what to order instead, from whom).

## 3 · The flow to build — one shortage per medicine, start to end

**A shortage** = a medicine a dealer did not send (short / came less / open past due), followed across its re-orders as ONE thing: *first missed order · times re-ordered · last answer · state*. Read from `order_carry` chains + `order_s778_na` + `order_flow_mark`; a new table `order_flow_short` is NOT needed — one derived reading (`shortages(con)`) in order_flow.py, used by every page.

**Before any state: the identity check** — a row whose medicine has an open Marg-rename pair shows the question first; a medicine whose Marg stock (either name) is above its reorder level is shown as "on the shelf — not a shortage" with its figure, not as missing.

**States and who moves them**
1. **Missing** (dealer did not send) → reception/Darpan: *Order again* (counted) · *Dealer: coming <when>* (= 'called') · *Dealer: out of stock* (→ the doctor) · *Substitute aaya: <name>* (picks the bill line or types the name).
2. **Re-ordered N times** — automatic. **After 2 re-orders with nothing come (or 14 days), it goes to the doctor by itself** as "the dealer keeps not sending", with the whole history. No tap needed.
3. **For the doctor's word** (his list, one row per medicine, expandable):
   - *Order from ___* — the other dealer who billed it (as now) **or any dealer picked from the phone book** → an again-row on that dealer's next order.
   - *Substitute: ___* — pick from the medicines bought in the last 90 days (search as you type) or type a new name, with the dealer → an again-row for the substitute; the old medicine's rule becomes `never` with the note "substituted by X (S502)"; the pair is kept (`order_flow_mark` kind 'sub_by' with sub_item + to_sn); **the Stock check / ledger of the old item say "substituted by X"**.
   - *Wait — ask again next week* (as now, 7 days; the row says the date and that it returns by itself).
   - *Not needed now* — leaves the list; the normal ordering rule decides later (`na_answer('keep')`, a mark 'not_now' so it is not re-asked for 30 days).
   - *Stop ordering it* (was "Drop it") — says plainly: "never suggested again until a bill brings it back".
   - *It came / we have it* — a manual clear with a note (a bill under another name, a shelf count).
4. **Substitute ordered** → **Substitute arrived** (its bill line or an arrival tap) → his *OK — keep as the substitute* (the pair stays; old item never, new item inherits the old one's ordering rule) / *Not OK — return it* (a return job for Amir; the old shortage reopens for his word).
5. **Closed** — by: came on a bill · substitute OK · stopped · not needed. Closed rows leave every page; the history stays in the medicine's ledger.

**What every row shows (his page, PC-first; the same facts in Hindi on reception's and Darpan's blocks)**
`VFER 500 · Shivaaz · 10 strips · not delivered 5 times since 24-Oct (02-11, 04-11, 10-11, 13-11) · Darpan 20-Nov: dealer says out of stock · last bought 18-Sep · Marg stock 0:0` — expandable: each order (day, ordered, came, bill scan thumbnail), the taps (who, when, what), the words given. Two-tap buttons, no dialogs (F-1464). A substitute already bought while this was missing is **suggested** on the row ("TOLIVANT PLUS was bought 02-Nov and 13-Nov — the substitute?") — found by: same dealer, first bought after the shortage began, not on any earlier order.

**Darpan / reception after his word:** "Doctor: substitute TOLIVANT PLUS — on Shivaaz's next order" · "Doctor: order from Ravi" · "Doctor: stop — do not order" · "Doctor: wait till 29-Nov". Their team block changes from a waiting list into an instruction list.

**Counts on the Hub line** = the same `shortages()` reading; one number per state.

## 4 · Where it is built
`/root/finance/order_flow.py` — `shortages()`, the team table rebuilt from it, new doors in `act()`: sub_by, not_now, came, other-with-dealer; `rec_act()`: sub with a name/line. `order_s778.py` — read only (na_answer reused). `porders_s454.py` / `darpan_kal.py` — their team blocks read the new fields (this project's). The Stock check (S501 plan) reads the sub_by pair later. Patient data: none in any of this.

## 5 · Kit
S926 (probe `kit_next > 926` first; deploy_kits newest S925). Walk on a made-up db with a carry chain of 5, a substitute bought meanwhile, every door; control red on the live files; S920–S925's proofs not worse (S837 rule); rehearsal; cold review; placed; his publish + one line.

## 6 · As built (written at the S502 close, 12:4x IST)
- **S926_SHORTAGES_AND_RENAMES — live 11:34.** `order_flow.py` v2.0: `identity()` (the newest closing; dead names with the partial-closing guard; partners from `item_alias`, `med_name`, his `same` words, the Marg watch's open pairs), `dead_norms()` (→ `order_s778.hidden()`), `shortages()` (states rename / keeps / oos / sub_way / sub_arr / wait / short; `keeps` after two re-orders with the newest failed), the section "Not delivered, out of stock and substitutes" with Stock & ledger inline and the full-page link, the doors (`act_s926`, table `order_flow_word`); `darpan_kal.html` shows his word and the shelf. Faults closed: F-1574 – F-1578, F-1580. Open: **F-1579** — the ordering lane keys the 22 ticked orthotic renames by their OLD names (`item_alias.resolve_map` new → old is for the count and stock lanes); the stock plan carries it.
- **S927_HUB_NEEDS_YOU_INLINE — live 12:38.** The Hub's Needs-you in three tiers, every line opening inline (`hub_panels.py` new; the arrived-not-in-Marg lines with the scan, its read lines, Marg's purchases and Ask Amir · It is this Marg line · Never came) — F-1584 closed. The rest of the panels: S928.
- **Pending his tap:** "Yes — same medicine" on VFER 500 (25:4 strips as V FER 500).
