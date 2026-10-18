# S580_SHELF_EXTRA_BILL_PROBE — brief for Claude Code (v1) — READ ONLY

*Written 18-Oct-2026 by the Sanjeevni chat (session 324), after S577's install. Read `claude_code_briefs/SANJEEVNI_BUILD_CHARTER.md` first.*

**This is a probe, not a build.**
- Nothing is placed, edited, restarted or written on the box, except under `/tmp/s580probe/`; remove it at the end.
- No build lock is needed. Read the live `finance.db` and `spine.db` only through the sqlite backup API copies in `/tmp/s580probe/`.
- Publish only the report.

## 0 · For the owner

On about 13 items, the shelf figure (the 6-Sep count carried forward by Marg's sales and purchases) is above Marg's own figure by exactly the quantity of one purchase bill dated after the count. For example:
- TOLTRIS PLUS: shelf 510 against Marg 10 (bill 3051 of 09-09, 50 strips);
- FLACORT 6: 236 against 36 (Kedar bill 195 of 27-09, 20 strips).

The same gaps are in the old records of 15 and 16-Oct, so this is older than today's kit; today's kit only shows it plainly. While it stands:
- the shelf figure is too high for those items;
- the voucher check and Darpan's spot count for them would be judged on it;
- any order proposal built on the shelf figure would under-order them.

This probe finds why. The repair is a separate kit.

## 1 · The items (from the 18-Oct 01:40 database copy, `s454_shelf_gap` 2026-10-16, gap = shelf − Marg, in tabs/pcs)

| item | gap | the matching bill (dated after 06-09) |
|---|---|---|
| TRAMATEE P TAB 15T | +750 | A000377 of 22-09 |
| TOLTRIS PLUS | +500 | 3051 of 09-09 |
| BIO D3 MAX | +300 | 67925 of 11-09 / 72975 of 22-09 |
| CROCAL | +300 | 3159 of 15-09 / 3290 of 21-09 |
| CHEXID D | +200 | 67093 of 09-09 / 74915 of 25-09 |
| FLACORT 6 | +200 | 195 of 27-09 |
| PREGHYPE NT TAB | +200 | 3463 of 01-10 |
| NUCOXIA P | +150 | 16744 of 18-09 |
| SYSFOL 5 | +150 | 21054 of 25-09 |
| FLORA BC CAP | +100 | 71226 of 18-09 |
| PRETOL 8 | +100 | 182 / 185 / A000203 |
| THIO Q AP | +100 | 623 of 27-09 |
| ZIVOPREG M | +100 | 8749 of 09-09 / 10480 of 10-10 |
| (no bill matches) | | FENARIC T4 TAB +66 · DOLONEX 2 ML INJ +50 · KT ROS DT −101 · DEFVAX 6 −120 · TYRO BR −328 |

**When each gap appeared in the old sets:**
- TOLTRIS PLUS: 139 on 13-10, then 603 on 15-10.
- FLACORT 6: 87 on 12-10, then 277 on 13-10.
- Marg's own series shows each bill entering Marg once, around its date. TOLTRIS: 106 → 610 between 08-09 and 11-09.

## 2 · What to find (on today's live data, with `stock_figure` as installed by S577)

For each item above:
1. **Today's figures.** Print `stock_figure.shelf()` and `marg()` (base, sold, returned, bought, boundary, arrived) and the gap.
2. **The shelf's purchases against Marg's own movement.** List every `sp_move` row of the key since 06-09 by kind, with its `ref`. List every `sp_purchase_line` of the key since 06-09: supplier, bill, date, qty, free, units, direction, `source_md5`, and that export's family, stamp and period. Compare their sum with Marg's own move between the count's closing and the newest usable capture, less the count's vouchers.
3. **Where the extra units come from.** Name the extra by row. Look for:
   - (a) one bill counted twice in `sp_move` (two exports, two families, two dates, or bill-wise against item-wise);
   - (b) `boundary_purchases` taking a bill;
   - (c) `_arrivals` / `scan_arrivals` adding units the spine already carries;
   - (d) a stock point or a fix becoming the base;
   - (e) units read as strips against tabs;
   - (f) anything else.

   For each, say why it started on the day the old series shows.
4. **How widespread it is.** Run the same test over **every** counted item: how many have a gap equal to one of their own post-count bills, and which cause each has.
5. **The spine itself.** Read the spine's own check (`sp_check` / `sp_finding`) for these keys at the newest checkable closing: does the spine equal Marg there? Is the extra in the spine, or only in the shelf arithmetic?

## 3 · Report — `claude_code_briefs/REPORT_S580.md`

- 3–5 plain lines for the owner: what the cause is, how many items, and whether ordering or staff screens are affected today.
- For the chat:
  - per item, the rows that make the extra, and the cause class;
  - the count over all counted items;
  - the exact functions and lines responsible (at their live md5s);
  - what a repair must change (no repair made);
  - any other figure in `stock_figure` that the same cause touches.
- Then publish with `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat` (the report only), and say "done" in two lines.

*S580 probe v1 · session 324 · 18-Oct-2026.*
