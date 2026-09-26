# Claude Code brief — S418_LOSS_DESK_PILES (the owner's Loss desk rebuilt as four piles, one tap each; no causes, no second page)

Written 26-Sep-2026 by the Sanjeevni chat (S283). Read `CLAUDE.md` first. **Kit S418 · decision D631 · fault F-641** (claimed on the
System Board). Runs AFTER S417. **Owner-facing, English. Sanjeevni-owned** (stock_app.py, stock_loss.html, the diffs/decisions tables).

## 1 · The owner's words (26-Sep evening, on the live Loss desk)
"These products were kept somewhere else and were not counted. Why make such a long path? I take it, it is there, it should be accepted back
into the system as it is. It is a very long list, very difficult to pursue, and the flow is so elaborate — it is not curated for easy
redressal for me." Three items he had with him (ETOZOX 90, HYORTH XL, DOLOGESIC SP) sit as "PARKED — kept elsewhere" and still count in
the ₹84,332 short; closing them today needs a cause on `/page/diffs` (whose vocabulary is for the checker, "turned up later"), a decision
on another route, and vouchers on a third. Small shortages after six months without a proper count are normal shop loss and should be
written off as a group, not line by line.

## 2 · What exists (`/root/finance/stock_app.py`, as S404 left it — read live; `stock_loss.html`; the hub)
`stock_diff` (cause / cause_note / cause_by / status), the decision route `/api/diff/<did>/decision` (WRITE_OFF | RECOVER | EXPLAINED),
the cause route `/api/diff/<did>/cause`, the lanes (`LANES`: consume · ortho · recount · bill · marg · loss · **allowance** · over · salt ·
dead; `_allowance_units()`, setting `stock.allowance_scale`), the Loss desk `/finance/stock/page/loss` (D389: ticks → the sheet for Darpan
via `/api/loss/<cid>/share`, frozen JSON + PDF), the voucher maker `/api/pad/vouchers/<cid>/make` (rounds ≤ 6 lines, ISSUE/RECEIVE, D541/D542)
and Amir's board (`stock_amir.html`), the section-close logic of S404. **Keep every table and route; the desk becomes the one door.**

## 3 · The build (D631) — `/finance/stock/page/loss` rebuilt; nothing else on the hub moves
Four piles on one page, every open line in exactly one, the system's suggestion as the starting pile, totals at the top
(`open · with me · written off · to pursue · recount`, at MRP and at cost, live as he taps):
1. **With me / back in store** — for a line here (parked, or any line he moves here): ONE tap **Accept back** → `EXPLAINED`, cause
   `found -- not short` (the existing vocabulary value; map "kept elsewhere / turned up later" to it), status closed, the shelf figure
   corrected to Marg's, audited "owner: back in store". Nothing else. The three named items are the first three lines.
2. **Write off as normal loss** — the allowance lane by default plus anything he moves in; the pile shows N lines · ₹X at MRP · ₹Y at cost.
   **Write off this pile** (a second button "Yes, write off N lines" for 10 s): every line → `WRITE_OFF`, and the stock-issue vouchers are
   made in rounds of ≤ 6 on Amir's board in the same call (`/api/pad/vouchers/…/make` restricted to those lines), audited. A dial on the
   pile — **Allowance: normal / wide / very wide** (`stock.allowance_scale` 1 / 2 / 3, the owner's ruling: six months without a proper
   count) — with a live preview "wide would move 37 more lines, ₹6,120". The consumables lane (BLADE, gloves, syringes: `consume`) is a
   sub-pile here, written off *as clinic consumption* with the same tap.
3. **Pursue** — the real gaps (the `loss` lane above the allowance, `bill`, `marg`): **Make the sheet for Darpan** as today (`/api/loss/share`);
   the line stays open with `RECOVER` until Marg agrees.
4. **Recount** — `recount` lane and any line he moves here (INTACOXIA-60 +719): **Ask Darpan to recount** → the items appear on Darpan's
   Stock milaan as *Phir se gino* with a count box; his figure replaces the shelf and the line re-piles itself.
Moving a line: a small **→ pile** menu on each line (four names), no dragging needed on the phone. Over-on-shelf lines are listed under a
collapsed "Over (never a loss)" note. The lane names, causes and decisions are never shown as vocabulary; the audit trail (who/when/what)
sits under a collapsed "record" at the foot. The orthotic lines stay on the S404 section and are not on this desk.

## 3a · The owner's rulings (26-Sep night, after the plan) — these override anything in §3 that differs
- **Allowance starts at WIDE for this count** (`stock.allowance_scale` = 2 seeded); the width is per item and turnover-related, as
  `_allowance_units()` already does (sold volume, loose selling) — a fast seller carries a wider allowance than a slow one. The dial stays.
- **The Write-off pile holds TWO documented groups, one tap for both:** (a) *within allowance* — short within the item's allowance;
  (b) *small real gap* — short beyond the allowance but under `stock.pursue_floor_p` (setting, default ₹1,000 at MRP). Both are written off
  by the one tap, both go to Amir's vouchers, and the count's record (the desk's "record" foot, the hub status card, the PDF report) lists
  them as two named groups with counts and totals, item by item — a write-off that is documented, never hidden.
- **The Pursue pile exists, for accountability:** every real gap of ₹1,000 or more at MRP starts there (plus whatever the owner moves in);
  the sheet to Darpan, his answer on Stock milaan, the line stays open until settled — never auto-written-off.
- **Hub totals and desk totals are ONE figure**: define the five totals once (open · back in store · written off (allowance / small gap) ·
  to pursue · recount) in one function and have the hub status card, the desk and the report read the same numbers (today the desk says
  ₹84,332 and the hub ₹64,338 for the same 155 lines — F-641's second half).
- **Retire from the owner's path**: the Differences page's cause chips, the Decision desk, the paper "cut the next list" and the
  "type Darpan's answers" steps (keep the routes for audit/reading; remove them from the hub's step list; the hub becomes a status card
  with links). Darpan's Stock milaan carries medicine recounts and pursue answers (§3.3–3.4).

## 3b · Every ruling is a SETTING on the desk (owner, 26-Sep: "so that we can alter them without going back to the code")
A collapsed **Settings** card at the foot of the Loss desk, owner-only, each with a one-line hint; stored in the `setting` table, every
change audited (who, when, old → new) and listed in the count's record so an auditor sees the rules in force when a group was written off:
- `stock.allowance_scale` — Allowance width: normal 1 / wide 2 / very wide 3 (default 2 for count #1; per-item width from turnover as today)
- `stock.pursue_floor_p` — Pursue floor at MRP (default ₹1,000): a real gap at or above it starts in Pursue
- `stock.small_gap_ceiling_p` — Small-gap ceiling (default = the pursue floor; may be set lower): a real gap below it is written off but
  recorded as a real loss
- `stock.recount_trigger` — a surplus, or a shortage of ≥ N units (default 50), starts in Recount
- `stock.voucher_batch` — lines per Marg voucher for Amir (default 6, D541)
- `stock.accept_back_by` — who may tap Accept back (default: owner only)
- `stock.consume_auto` — consumables (BLADE, gloves, syringes…) written off as clinic consumption with the pile (default on)
- `stock.rolling_section_items` and `stock.rolling_day` — the weekly rolling count's section size and start day (read by S419; seeded 90 / Monday)
The piles re-compute from the settings on every read; changing a setting never decides a line by itself.

## 4 · Pins — read live: stock_app.py (S404 TO 586ae78a), stock_loss.html, stock_amir.html (c2ea41b2), stockmatch.py/html (S404; the
recount box). No parent file. Restart `clinic-finance` only.

## 5 · Walk (scratch copy; own count rows keyed W418*)
Accept back closes a crafted parked line (EXPLAINED, cause found, shelf = Marg, audited) and the totals drop · Write off this pile decides
every line in the pile, makes vouchers in rounds ≤ 6 on Amir's board, never touches a line outside the pile; the 10-s confirm gate; a repeat
does nothing twice · the allowance dial preview counts right and moving it re-piles without deciding anything · the sheet for Darpan
unchanged (S227/D389 assertions hold) · recount lands on Darpan's page and his figure re-piles the line · the → pile menu moves a line and
records it · bhati/darpan/shavez refused on the desk · orthotic lines absent · S404 walk (on the 14:04 backup) and S403 re-run green ·
negative control on the old files.

## 6 · Done means
Kit `deploy_kits\S418_LOSS_DESK_PILES\` · installed · published · `claude_code_briefs\REPORT_S418.md` — owner lines first: the four piles
as he will see them with today's real figures (how many lines and ₹ in each before he touches anything), the three named items in pile 1;
ending with `https://followup.dr-manoj.in/finance/stock/page/loss?count=1`.
