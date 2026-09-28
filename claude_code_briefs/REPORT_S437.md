# REPORT S437 — S437_COUNT_PAGES_FINAL (F-659) · installed 28-Sep-2026 23:09 IST · published (see the foot)

## For the owner
- **The STOCK RECEIVE vouchers are made.** Every line where the shelf held more than Marg is now on Amir's board: 34 STOCK RECEIVE lines on
  6 vouchers (the biggest: INTACOXIA-60 +47 strips + 14 tabs, ALCOXIB 120 +19 strips + 7 tabs, PARI CR 12.5 +18 strips + 13 tabs, ZIBON EXTRA
  +15 strips + 6 tabs, ASTOFEN P +6 strips + 4 tabs, NEWTEL H 40 +6 strips, PRIME CAST 5" +45 pcs). The same round also carries the 15
  short lines you wrote off on 06-Sep that had never reached a voucher (GEMCAL XT TABLETS, XGESIC LA, SYSFOL 5, CEECIT MZ, RUNVACE TP …) as
  3 STOCK ISSUE vouchers. Your hub now says "Every line is on a voucher". None of this is a loss; the leakage figures are untouched.
- **Amir's board is the vouchers only:** STOCK ISSUE — वाउचर 1 to 28, then STOCK RECEIVE — वाउचर 1 to 9. Each line reads item (packing) ·
  Marg से → तक · कितना, nothing else; he types Marg's voucher number and taps "Marg में डाल दिया"; a keyed voucher folds to one line. Naam badlo
  stays hidden until Marg and the shelf are proven equal.
- **CCM now reads bottles everywhere:** on Amir's board "CCM (1*40) · Marg से 8 botal → तक 5 botal · − 3 botal"; on your desk "short 3
  bottles (Marg 8 bottles, counted 5 bottles)". A new list on the desk's Settings card, "Whole-piece items", holds CCM = bottle; it also shows
  13 candidates you can add with one tap each (CALAPTIN 40, COLOSPA 135, DENGEN PLUS, DROTIN DS TAB, FELBATE, HAIRBLESS 15T, JARDIANCE 10,
  LINTIDE 145 MCG, NEWTEL 40, NEWTEL H 40, NIMREX P, OSMEGA 500, RIFAGUT 550) — these were flagged only because every sale of theirs was a whole
  strip; add only the ones Marg truly counts by the piece.
- **Darpan's block is a table now:** "Ginti 06-09-2026 · kul kami Rs 61,076.40", then Badi kami — Rs 29,314 (22 rows: item · Marg on the
  count day · gina · kami · Rs, with a total row; ROSIKA FORTE Marg 72 patte + 3 goli, gina 55 patte + 3 goli, kami 17 patte, Rs 4,760 …), Chhoti
  kami — Rs 31,762.40 collapsed (87 rows), and the page ends with "Orthotics band ho gaya — kami Rs 5,420 (10 line, bina bill) · 2 bina
  daam" with its 10 rows collapsed under it. The lines after it are gone. Your desk shows the same tables in English, and the record PDF too.
  Everything was tested on a copy first and works on the live site.

## For the chat
**Kit** `deploy_kits/S437_COUNT_PAGES_FINAL/` (14 files, SUMS.md5, KIT_ID `kit id S437_COUNT_PAGES_FINAL`). Ran on the box from `/tmp/s437kit`
(byte-identical to the repository kit: SUMS.md5 on both sides, `diff -r` after the publish — the foot). Build lock
`/root/deploy/.claude_code_build.lock` taken 20:26:22 IST (owner S437), held through eight dry runs (20:26 → 22:44), the install and this report.

**Live files, FROM → TO (md5 read back on the box after placing, 23:09 IST; read again 23:13):**
| file | FROM | TO |
|---|---|---|
| /root/finance/stock_amir.html (whole) | d32f39fad196c84a2cdf1ef5ca2f2598 | 1ec8663dbbad397fe46f093966352e0a |
| /root/finance/stockmatch.html (whole) | bdfb25e38cbc5a4c71171962089e1ccd | 0dc4d303434d6f87d9e470bccb79f54c |
| /root/finance/loss_piles.py (whole, v2.4) | 47d6acb35a84f9eb81235cad0de2b915 | 202bfc4e3fd798501c6db95373c2a7d4 |
| /root/finance/qty_words.py (whole, v1.2) | f4c15d7e88c84b14c7686d5b28148877 | 706db7ccfa7489fb8d296f663590f107 |
| /root/finance/stock_app.py (anchored, make_s437.py) | ec9abc4801599d9acd1ab34f66a21a83 | 4f2625c0a88e450c88e0b23d499d6fa8 |
| /root/finance/stock_statement.py (anchored, v1.3) | 24a040b1b58a21f043ff92ffce1e2860 | 1a4f6c9ecb2546dae954c0414074f406 |
| /root/finance/stock_hub.html (anchored) | 7b2ea5065c1b1bf110a4301ccd0384a1 | a710a98a568227d4b2ba220d792e6a2c |
| /root/finance/stock_loss.html (anchored) | 5ead2a32949ec6e77e95b8645db350e2 | 0f0dfed658d05d182811005ebce49df3 |

Pins checked before touching (all eight at their FROM, read 14:4x and again by the installer at 22:47). `stockmatch.py` f09d9516: pinned, read,
NOT changed — Darpan's block rides `loss_piles.block_view` (the tables ride with it) and the page simply no longer prints the verdict tail.
Restarted `clinic-finance` only. No cron, no portal, no parent file.

**Backups:** `finance.db.bak_S437_20260928_224714` (backup API, 26,963,968 bytes) and, beside each file: `stock_amir.html.bak_S437_d32f39fa`,
`stockmatch.html.bak_S437_bdfb25e3`, `loss_piles.py.bak_S437_47d6acb3`, `qty_words.py.bak_S437_f4c15d7e`, `stock_app.py.bak_S437_ec9abc48`,
`stock_statement.py.bak_S437_24a040b1`, `stock_hub.html.bak_S437_7b2ea506`, `stock_loss.html.bak_S437_5ead2a32`.

**Health after placing (23:08–23:13 IST):** service active since 23:08:34; local healthz 200; `/finance/stock/page/amir` and `/finance/stock/page/loss`
302 (login gate, expected); public `https://followup.dr-manoj.in/finance/healthz` 200, the four pages 302; journal since the restart: only
gunicorn's "Worker was sent SIGTERM" line of the restart itself, no traceback, nothing "NOT mounted".

**The seed on the live database (23:08:40–23:08:52 IST, `seed_s437.py`):** `stock.whole_unit_items` = `["CCM = bottle"]` (audited `stock_setting`,
seeded, by S437) · `loss_piles.receive_close(all_pending=True)` for count #1: `stock_writeoff_run` id 3, kind `receive_close`, at 23:08:43, by
"rule F-659, 28-Sep", 49 lines, mrp 0, groups receive (34) / issue_earlier (15); 19 shelf-more lines that the maker did not carry got the
rule's lane word EXPLAINED ("rule F-659, 28-Sep: the shelf held more than Marg -- Marg corrected up to the shelf, never a loss") at 23:08:43:
ALCOXIB 120, BELL CAST 5, CALBERT K27, DECA INSTABOLIN 50, FLUPIVAMP 100, FORECOX, INTACOXIA-60, MECOVIXR FORTE INJ, MET4MIN GL 1, NEWTEL 40,
PARI CR 12.5, PRIME CAST 4", PRIME CAST 5", PRIME PAD 4", PRIME PAD 6", SHIGRU 60, TFCT-NIB, TOFZA TAB, TRAMAVIN P; round 5 made by the rule at
23:08:52 (ISSUE 3 vouchers / 15 lines, RECEIVE 6 vouchers / 34 lines, ≤ 6 a voucher); audit `receive_close`; pending 30 → 0. The desk's cache
rebuilt itself on the changed setting (CCM in bottles on the first read).

**The figures (figures_s437.py on a fresh scratch copy through the live files, 23:09):** as listed for the owner; the rounds now: 1 (ISSUE 1
voucher), 2 (ISSUE 20), 3 (ISSUE 2 + RECEIVE 2, Darpan's last answer), 4 (ISSUE 2 + RECEIVE 1, rule D638), 5 (ISSUE 3 + RECEIVE 6, rule F-659)
→ Amir's board STOCK ISSUE 1..28, STOCK RECEIVE 1..9, 37 vouchers, 0 keyed, pending 0. Statement: 28 shelf-more / Marg-negative medicine lines
all "Marg corrected -- on STOCK RECEIVE voucher N". Naam badlo hidden (proof state wait). Darpan's block: kul Rs 61,076.40 · Badi kami Rs 29,314
(22 rows) · Chhoti kami Rs 31,762.40 (87 rows) · Orthotics band ho gaya — kami Rs 5,420 (10 line, bina bill) · 2 bina daam.

**The walk (`walk_s437.py`, on scratch copies of the live database and the spine, the seed run on the copy first):** `WALK_S437 GREEN -- 42 of 42
passed` in the install (and in the final dry run at 22:2x). Every real line by key from the maker's pending list and the report's shelf-more
lines before the seed (15 RECEIVE + 15 ISSUE pending, 19 shelf-more lines with no carrying word); crafted rows keyed W437: a 1*30 medicine sold
only whole (a candidate), a 1*10 medicine with a loose sale (not one), a shelf-more line nobody worded (the rule at a later close). Highlights:
ONE `receive_close` run by the rule with 34 receive + 15 issue_earlier rows, mrp 0; every shelf-more line one RECEIVE line with Marg से → तक = the
shelf, change = the difference, ≤ 6 a voucher; the rule's EXPLAINED words on the 19; none in a loss group, the leakage period line unchanged, no
watch-adjust row; hub pending 0 and "Every line is on a voucher" on its page; the record's run and titles; the statement's "Marg corrected --
on STOCK RECEIVE voucher N" on every shelf-more / Marg-negative medicine line, "on STOCK ISSUE voucher N" on a written-off line, no round number
anywhere; the rule idempotent; the crafted W437 OVER TAB (Marg 5 → shelf 9, no word) worded and put on a RECEIVE line 5 → 9 by the rule; the
close hook wired · Amir's board: STOCK ISSUE 1..28 then STOCK RECEIVE 1..10 continuous across rounds 1–6, every voucher once, ≤ 6 lines; all
202 rendered lines free of "written off / loss / rule / owner / closed / group / swap"; the page draws no reason / rate / value / round; CCM
"− 3 botal" (8 → 5); Naam badlo hidden (wait), every voucher keyed (38, 200 each) and still hidden, then SHOWN (23) only under a crafted proof
(Marg's export after the last voucher moving every item by exactly its voucher: state done, "Marg = shelf") · qty_words v1.2 (CCM = bottle:
"3 bottles" / "3 botal"; an item off the list unchanged); the setting seeded and audited; the desk (3 bottles, Marg 8 bottles, counted 5), the
statement, Darpan's table (3 botal), the record PDF; the candidates (W437 WHOLE TAB in with a guessed word, W437 LOOSE TAB and CCM out); one
tap adds "W437 WHOLE TAB = jar" (audited), a bad word refused, remove; the desk card's data-whole-add and word select, no "unit" word ·
Darpan's block tables (badi = the 22 frozen big lines, largest first, total = the block's big figure; chhoti total = the small figure; kul; the
10 orthotic rows apart with the wording), the page source (tables, dikhao, the block last, no s.conds / verdict_hi / "Koi line baaki nahi" /
"Sab ho gaya", the pairs folded) · the desk's tables in English with the frozen totals and the link, the record PDF's TOTAL rows, the preview
· the gates as before (the same matrix on the old and the new files), the whole-piece door owner-only.
**Negative control:** the same scenario on the box as it was: `13 of 13 checks red` (no receive round, pending stays 30, no numbered vouchers,
CCM in tabs, no tables); the old loss_piles has no `receive_close`, the old board no `vouchers_flat`.

**Earlier walks re-run on the patched files, each against its own pre-kit control (in the install):** S430 42/42 · S427 82/82 · S428 73/73 ·
S431 56/56 · S432 68/68 · S436 48/48 · S404 65/65. Named adjustments, all in files of this kit:
- `walk_s427_s437.py` (S432's copy + ONE): the settings card's key set carries `stock.whole_unit_items` (the brief's 3.3).
- `walk_s436_s437.py` (S436's own walk + TWO): the statement's voucher column reads "on STOCK ISSUE voucher N", not the round number; Naam badlo
  stays hidden after every voucher is keyed (gated on the proof now). Runs on the 13:09 backup of 28-Sep (before S436's seed), as S436's own walk
  must.
- The installer (not a walk): S431's walk (S436's copy, unchanged) also runs on that 13:09 backup — on today's live copy the orthotic section
  is closed by S436's seed, applied after S436 had re-run S431's walk, so three S431 texts (Darpan's reasons, the close's at / by) read the rule's
  outcome. Nothing to do with S437. S430's control stands on the `.bak_S432` files as S436's installer set it.
- Inside `loss_piles._run`: a tap close runs `receive_close` BEFORE its own run row, so the close's run stays the newest (S430's walk reads the
  newest run's groups; the first dry run had the receive run there). An auto-close (the last clear) runs it after.

**Dry runs before the install (DRY=1 NOPIN=1 from /tmp/s437kit, under the lock):** eight, 20:26 → 22:44 IST. Fixed between them, none a change to
what the owner asked for: my crafted proof used a day older than a real export (the proof reads the newest export before the vouchers); two
page comments said "whole-unit" (the walks' word gate refuses "unit" on a screen — the label reads "Whole-piece items"); the old-file control
raised before recording two labels; the run ordering at a tap close (above); S427's key set; S428 looks for a phrase in Amir's page header
comment ("bill entry baaki" — kept in the new page's comment); S431's data (above); and the two real gaps the dry-run figures exposed —
**shelf-more lines the maker never carried**: 17 with no word at all (ALCOXIB 120, CALBERT K27, the cast pads …) and 2 the owner had PARKED on
06-Sep (INTACOXIA-60 +47 strips, NEWTEL 40) — the brief's rule ("every line where the shelf holds more than Marg") now words them EXPLAINED
by the rule and carries them; 34 RECEIVE lines instead of 15.

**Outside the brief / calls made (each as the rulebook asks):**
- The chat's read of F-659 ("the 30 lines where the shelf holds MORE than Marg") was half right: 15 of the 30 pending lines were SHORT lines the
  owner wrote off on 06-Sep, before the piles existed, never vouchered (the desk's "written off earlier" group). They ride the rule's round as
  STOCK ISSUE vouchers 26–28 (group `issue_earlier`, no new loss — they were already in the desk's totals). Without them the count could never
  be proven (the proof needs pending 0).
- The owner's PARKED of 06-Sep on INTACOXIA-60 and NEWTEL 40 is superseded by the rule's EXPLAINED word (Marg corrected up to the shelf);
  PARI CR 12.5's +18 strips + 13 tabs (the wrong-salt pair the owner answered "No" in S436) is likewise corrected up, as an excess, not a loss.
- The whole-piece candidate rule is the brief's own (every sale a whole multiple of N): it flags strip items that only ever sold whole
  (JARDIANCE 10, RIFAGUT 550 …) as well as true bottles. The owner should add only what Marg counts by the piece; the seed added CCM alone.
- The frozen `why` text of CCM in run 1's allowance group ("short 3 tabs -- within the allowance …") is frozen data of 27-Sep and stays; every
  live read (desk, statement, board, PDF, Darpan) says bottles.
- The renames' rows stay in Amir's JSON (the hub and the record read them); only the page hides them until the proof is green.
- The lane `why` texts still call `_qw()` by pack only in a few places; `_qw()` now names the item of the lane being worded, so a whole-piece
  item reads in its word there too (checked through CCM on the desk).
- One PowerShell command was refused by the permission list at 20:2x IST: a single line that chained the parse check, the sums, the phone gate,
  the upload and the start of the dry run (with `rm -rf /tmp/s437kit` over ssh in the middle). I ran the same steps as the separate commands the
  list allows — the same shapes S436 used — rather than another spelling of the chained line.
- Not done: nothing of the brief was left out. `stockmatch.py` was pinned but needed no change.

**After the publish (23:15 IST):** repository published with `PUBLISH_ALL.bat` (gate clean, commit `c555235` on main, origin verified); on the box
`git pull --ff-only` → HEAD c555235; `deploy_kits/S437_COUNT_PAGES_FINAL/` SUMS.md5 13 of 13 OK; `diff -r` repo kit vs `/tmp/s437kit` (what ran):
byte-identical; the repository's own installer run from `/root/deploy/repo`: "ALREADY INSTALLED: the eight files are at the kit's pins;
clinic-finance active; healthz 200"; public healthz 200; the build lock released 23:15:31 IST. This report is published in a second commit.

**Undo:** the eight `.bak_S437_<from8>` files back, `systemctl restart clinic-finance`, healthz 200. The seed's rows (the setting, the rule's
words, run 3, round 5) are data an older loss_piles ignores (round 5 would then show as "Round 5" on the older board);
`finance.db.bak_S437_20260928_224714` only if the owner asks for them to be reversed — say so first.

https://followup.dr-manoj.in/finance/stock/page/amir?count=1
https://followup.dr-manoj.in/finance/stockmatch
https://followup.dr-manoj.in/finance/stock/page/loss?count=1
