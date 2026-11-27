# S967_STOCKCHECK_ONE_PAGE — the one Stock check page, read only (kit A1 of S534_FINAL_BUILD_PLAN; built at Sanjeevni session 535, 27-Nov-2026)

**What he asked (D1090, D1091, D1092):** one page for the whole inquiry — a short count, the allowance, what is on its way to Marg, the old
corrections re-judged, a voucher nobody asked for; every row opening in place to its path, its voucher lines and its item ledger, nothing
needing another page. **His "ok" 09:25 IST 27-Nov on mock-up v9** (`https://claude.ai/artifact/W3U9BfeW9K5QKpsgZ6YoqF`). The plan:
`S534_FINAL_BUILD_PLAN.md` §1, §2.1–2.3, §3, §5 kit A1. **This kit writes nothing** — Write off / Pursue / the allowance button are kit A2.

## The page — `stock_check.py` 83bbed0d → v1.6, `stock_check.html` 69d1fabe
`GET /finance/stockcheck/api/desk` (checker, maker, viewer; cached 60 s; `?fresh=1`): the five boxes, from the stock of record
(`stock_of_record`), the counts (`stock_point`) and the voucher judge — every figure read, none computed here.
1. **Short in the count** — a record row standing on a spot / Darpan count of the last 30 days (no `old_base`), Marg above the shelf, the
   count's own judgment a loss. *Within the allowance* rows form the group below it, each with the allowance the judgment used
   (`record_judges._allow`, the spine's sales; shown only when the spine reads). An evening count still `awaits_sales` is tagged and offers
   nothing; "about a delivery" is tagged *count again*. A short already asked of Amir (a count line or his card; a batch fix moves no total)
   goes to box 2 with its whole path.
2. **On its way to Marg** — every ask the judge reads `waiting` / `beyond` / `gap`, grouped as the S965 page groups them; the Expiry
   watch's night-time batch fixes among them (his word 27-11: they keep running).
3. **Old corrections, re-judged on the whole item** — `voucher_judge.rejudge`: every ask said done and not in Marg, or in Marg not as
   asked, and every Marg line keyed twice / more / less, one entry per item, against today's record row: Marg = shelf → *settled by later
   entries* (shown under Settled) · shelf only from an old count → *count first* (the row carries the existing Count button) · a fresh count
   still differing → *today's gap* (pointing to box 1 or 2) · VINBACTUM DS → *held* (D1077). A batch part is said to stay with the Expiry watch.
4. **Voucher nobody asked for** — every voucher with an unasked line, each item with its whole-item verdict; *history* until his rule date
   (`setting` `stock.voucher_rule_from`, not set — kit B sets it and starts the inquiry).
5. **Settled in Marg** (folded) and **the rules this page reads** (folded, read only; `stock.allowance_scale` shown as retired — S418's
   `loss_piles.RETIRED_KEYS`, the judgment does not use it).
The S965 boxes (every voucher, every correction) stay, folded under the new boxes; the rest of the page below is unchanged.

## The judge — `voucher_judge.py` 81d04b41 → v1.1
**F-1706:** an `S957:` (or `fix:S569` / `fix:S572` / `S829:`) re-ask merged into an earlier ask now keeps each tap's own moment: a re-ask
created after the newest done tap, and not itself done, clears the done mark — the ask reads *waiting*, never *not in Marg* on the older
tap; a re-ask tapped done in its turn moves the mark to its own done. KT ROS DT on the 27-Nov copy: *waiting* (was *not in Marg*).
**The re-judge** (`record_rows`, `record_for`, `whole_item`, `rejudge`): read only.

## The item ledger — `item_ledger.py` fe31f2c3
**F-1707:** every count of the item (`stock_point`: Darpan, the spot mornings, the full count) is a row of its day — counted figure, the
judgment's mark (a replaced / recount-held / awaiting count says so) — moving no balance; amber on the page. `GET
/finance/sanjeevni/ledger/api/fold?k=` (the doctor only, as the page): the newest lines as data for the Stock check's fold; `?embed=1`
the page without its head and search for the fold's *Full ledger · or a date range* (its own links keep the embed view).
**F-1708 assessed:** the batch text is Marg's own print — the ledger foot already says "each line's batch is as Marg billed it"; no fault.
The "bill 4043 for 4100" note: `_late` named the first of two equal purchase lines as certain; it now names each that fits ("one of these
(the same quantity): bill A … or bill B …"). The `purchase_line` duplicates per export (F-1710) are not this kit.

## Proof
* `walk_s967.py` **41/41** on made-up data (a made-up spine, record, counts, asks and voucher reports), twice on one layout; the control on
  the live files red at its first line (no desk). `walk_s965_regress.py` (S965's own walk, unchanged) on the new files: 31/32 — only its
  "healthz says v1.5" line, the version now 1.6.
* **Live shape** — the 27-Nov database copy, device VM only (the spine is not in the bundle, F-1661): box 1 six (NORTIMER TAB 6:0,
  MEG QCS 4:5, CROCAL 2:1, TRAMATEE P TAB 15T 2:12, PANTAVIN 40 2:0, ZUPRINOR 5 2); the allowance two (PRETOL-4, TYRO BR); box 2 fourteen
  (KT ROS DT 7:11 *waiting* + thirteen night batch fixes); box 3 five (TRAMATEE today's gap; CCM, KNEE SUPPORT L / M HINGED count first;
  VINBACTUM DS held); box 4 three vouchers (AD00012, L000031, AD00010 — CAST SHOE L / M, KNEE IMMOBILIZER L / M count first, NORTIMER today's
  gap, ENZOMAC settled); settled nine (GLI-ME SR1, GEN D3 NANO, DOLONEX 2 ML INJ, G DRESS 10, JAKMAC 5, PATOPAN DSR, PEMZOLE D by later
  entries; ZIBON EXTRA, GEMCAL XT written off in Marg). The plan's §2.3 thirteen cards land exactly as it lists them. The installer repeats
  the count line on a copy of the live database.
* Rehearsal on a made-up root (`rehearse_s967.sh`): dry · red@4 · red@5 · install · again · undo · install again · wrong FROM · a read pin
  moved · the lock · a corrupt kit.

## Install
His publish, then one server line (in the installer's head). Four files placed after backups `*.bak_S967_*`, clinic-finance restarted,
the doors and the modules checked, the desk read once on the live database. **Undo:**
`bash /root/deploy/repo/deploy_kits/S967_STOCKCHECK_ONE_PAGE/undo_s967.sh` (the four files back; nothing else to undo).

## Reviews
**Cold review** (a separate agent): SAFE — no write on any GET (proved with a deny-all-writes authorizer on a copy), F-1706 changes exactly
one ask on the real copy (KT ROS DT). Built in: **M1** the allowance looked up the earlier count by the wrong name form (PRETOL-4 would have
shown the wrong figure) — now `stock_watch.norm_name`, and the figure's day by `record_judges.judge`'s own rule; **S2** the fold kept the
day's Marg mark off a day with a count; **S3** the installer now requires "S930 stock_check mounted v1.6" in the log and refuses
"not mounted" (the doors answer 302 unsigned); **S4** F-1706 decided on time (the newest done tap against the newest open re-ask), never on
the order of ids, a day-only done mark standing for the end of its day; **S5** only an ask dated on or after the count moves a short to box 2;
**S6** box 1 only for a short the judgment called a loss (or a delivery's worth, or awaiting its sales); **N8** an old correction is judged
"fresh" only within box 1's 30 days; **N9** the fold's "more"; **N7** the page says so when the voucher judge could not run.
Noted, not changed: the Count button (boxes 3, 4) and the ledger's "Ask Marg's Stock Register" are old write paths, reused; the S965 boxes'
anchors open only with their fold; the control proves the desk missing (F1 against the FROM judge was confirmed red by the review).
**Second look** (a separate agent, on the fixed kit): SAFE — M1 proved on a made-up recording spine (PRETOL-4 06-09→17-11, TYRO BR
12-10→23-11 to its bill: the same windows as `settle_words`); S3's log line is printed by each worker before healthz answers; no write on
any GET with the allowance path running. Built in: **1** a standing done mark keeps Amir's typed Marg day (a merged tap only moves it later);
**2** box 2 takes a short only when the newest asking of it (any figure) is on or after the count — never left in box 1 while on Amir's
card; **3** "never a loss" words keep a short out of box 1; **4** such shorts, and one whose count is not found, are shown in their own
folded group, never lost; **5** boxes 2 and 4 judge "fresh" with box 1's 30 days; **6** "asked again" said only after a real done tap;
**7** the log check reads only these two modules' "not mounted"; **9** the rehearsal proves a log without the v1.6 line puts it back.
Noted: an item can show in box 2 (a night batch fix waiting) and under Settled (the whole item agrees) — by design.

