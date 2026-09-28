# REPORT S436 — S436_STAFF_PAGES_CLEAN (D638) · installed 28-Sep-2026 13:30 IST · published (see the foot)

## For the owner
- **The orthotic loss is now computed and the orthotic section is closed.** 10 orthotic lines were short: Rs 5,420 at selling price (2 of them,
  FINGER COT SPILNT REMEDE and SOFT COLLAR BODY AID S, have no selling rate yet, so they carry no rupee until Amir enters one in Marg). The
  items: ANKLE BINDER BAMBOO L Rs 325 · ANKLE BINDER BAMBOO M Rs 325 · ARM SLING XL UNISON Rs 470 · DYNA WRIST BRACE REVER LONG Rs 595 · FINGER
  COT M Rs 120 · FINGER COT M TYNOR Rs 155 · L S BELT CONT GRAY UNISON XXX 2 pcs Rs 2,780 · RIB BELT S TYNOR Rs 650 · the two without a price.
  The two extra lines (CERVICAL COLLAR SOFT HOPE L, SHOULDER IMMOBILISE UNISON M) are book corrections, not money. Your hub shows
  "Orthotics section: CLOSED by rule on 28-09-2026"; Needs you has one line about it; the statement reads "orthotic loss" on those lines.
- **The round is on Amir's board:** round 4, 3 vouchers, 12 lines, made by itself. (Round 3, the 18 swap lines, appeared at 12:04 today the
  moment Darpan answered his last orthotic line, as the older rule already did.)
- **Amir's board now has four sections in Hindi, nothing else:** 1 वाउचर — Marg में डालने हैं (rounds 2 · 1 · 3 · 4, each voucher's lines
  inline, one tap "Marg में डाल दिया" with Marg's voucher number) · 2 वाउचर के बाद — Marg से closing stock निकालें (the instruction, the proof's
  confirmation when the next export lands, the upload box as fallback) · 3 सुधार — Marg में ठीक करना है (Salt theek karo, Rate daalo, Naam badlo
  only when the vouchers are done) · 4 बाकी काम. The waiting list, the Excel links, "What is behind them", the old reports list, the typed
  answers and the families cards are gone.
- **The four salt tasks are on his board:** JARDIANCE 25 (ETOROCOXIB 90 → EMPAGLIFLOZIN 25), PARI CR 12.5 (ETOROCOXIB 90 → PAROXETINE CR 12.5),
  LACTOVAX SYP (FEBUXOSTAT 40 → LAXATIVE (LACTULOSE)), LINVIZ 600 (FEBUXOSTAT 40 → LINEZOLID 600). Each clears itself when the next salt export
  shows it. ETOZOX 90 ↔ PARI CR 12.5 and the two LACTOVAX pairs stand "No — not a swap, salt wrong in Marg"; no pair is proposed on those items
  until the salt is fixed.
- **Darpan's Stock milaan** offers one answer per orthotic line ("Galti se bill nahi bana" for a short line, "Bill bana, diya nahi" for an extra
  one); Toota / kharab, Vaapas nahi aaya and Pata nahi are gone. Everything was tested on a copy first and works on the live site.

## For the chat
**Kit** `deploy_kits/S436_STAFF_PAGES_CLEAN/` (16 files, SUMS.md5, KIT_ID `kit id S436_STAFF_PAGES_CLEAN`). Ran on the box from `/tmp/s436kit`
(byte-identical to the repository kit: SUMS.md5 checked on both sides, `diff -r` after the publish — see the foot). Build lock
`/root/deploy/.claude_code_build.lock` taken 11:22:46 IST (owner S436), held through the dry runs, the install and this report.

**Live files, FROM → TO (md5 read back on the box after placing, 13:30 IST):**
| file | FROM | TO |
|---|---|---|
| /root/finance/stockmatch.py (whole, v1.1) | df5501ea436d887dfe14ed618adce7ea | f09d9516a9df73941033591af8878c3e |
| /root/finance/stockmatch.html (whole) | 4ddf0073099086f024c9e12412abf1ec | bdfb25e38cbc5a4c71171962089e1ccd |
| /root/finance/stock_amir.html (whole) | 3cf1f73ee707a2d3cff6781ba4c36012 | d32f39fad196c84a2cdf1ef5ca2f2598 |
| /root/finance/loss_piles.py (whole, v2.3) | 2501b55ad8334bf10c0c19a254d40a02 | 47d6acb35a84f9eb81235cad0de2b915 |
| /root/finance/stock_watch.py (whole, v1.3) | 5114e01f5dc70bd3f90dea3b040f8f02 | 9cca2f2a9e86e6523b9fcefb4f6df3bd |
| /root/finance/stock_app.py (anchored, make_s436.py) | 02ad3d6ac3390dcf940d7a443557ac7c | ec9abc4801599d9acd1ab34f66a21a83 |
| /root/finance/stock_hub.html (anchored) | 38e0537cd7d1eb3fb40d1a5a0b7df0e5 | 7b2ea5065c1b1bf110a4301ccd0384a1 |
| /root/finance/stock_statement.py (anchored, v1.2) | 05c63235a9f78c9f0f6969c683548880 | 24a040b1b58a21f043ff92ffce1e2860 |

Pins checked before touching (all eight at their FROM). `sanjeevni_approvals.py` 3999c4ce NOT touched: its `needs_you` block already reads
`stock_watch.needs_you_lines`, so the Needs-you line came through `stock_watch.py` (the `ortho_closed` kind added there). Restarted
`clinic-finance` only. No cron, no portal, no parent file.

**Backups:** `finance.db.bak_S436_20260928_130938` (backup API, 26,800,128 bytes) and, beside each file: `stockmatch.py.bak_S436_df5501ea`,
`stockmatch.html.bak_S436_4ddf0073`, `stock_amir.html.bak_S436_3cf1f73e`, `loss_piles.py.bak_S436_2501b55a`, `stock_watch.py.bak_S436_5114e01f`,
`stock_app.py.bak_S436_02ad3d6a`, `stock_hub.html.bak_S436_38e0537c`, `stock_statement.py.bak_S436_05c63235`.

**Health after placing (13:29–13:31 IST):** service active since 13:29:39; local healthz 200; `/finance/stockmatch` 302, `/finance/stock/page/amir` 302
(login gate, expected); public `https://followup.dr-manoj.in/finance/healthz` 200, the three pages 302; journal since the restart: only gunicorn's two
"Worker was sent SIGTERM" lines of the restart itself, no traceback, nothing "NOT mounted".

**The seed on the live database (13:29:49–13:29:59 IST, `seed_s436.py`):** causes by rule — 10 short lines Darpan had answered → `sold, no bill was
made` (his name kept, note "rule D638, 28-Sep: sold without bill (was: … by darpan)"), 0 by default (see "outside the brief"), 2 extra lines →
`billed, not handed over`; 12 audit rows `stock_diff / cause_rule` by "rule D638, 28-Sep" · the three pairs answered No with the note "not a swap
-- salt wrong in Marg (rule D638, 28-Sep)" by "owner (S436, said in chat 28-Sep)" at 13:29:49 · the four salt fixes in `purchase_salt_task`
(section change, seq 76–79, ids 70 / 97 / 82 / 87, source S436-owner-28-Sep, b = Marg's salt today, 4 audits `salt_fix_seed`) · `close_by_rule`:
`stock_writeoff_run` id 2, kind `ortho_close`, at 13:29:52, by "rule D638, 28-Sep", 12 lines, mrp_p 542000, unpriced 2, groups ortho_loss (10) /
ortho_fix (2), round_no 4; `stock_section_close` (1, Orthotics, 13:29:52, basis rule D638); lane words WRITE_OFF × 10, MARG_FIX × 2, the 12
stock_diff rows closed; the orthotic round 4 (3 vouchers, 12 lines, ≤ 6 a voucher); `stock_watch_notice` kind ortho_closed at 13:29:59:
"Orthotics closed: 10 lines short, Rs 5,420 at selling price (2 without a price); round 4 of 12 lines on Amir's board".

**The figures (figures_s436.py on a fresh scratch copy through the live files, 13:30 IST):** the loss as listed for the owner (prices from the
spine: S.RATE for eight lines, MRP for ARM SLING and DYNA WRIST; the run's per-line rows carry the source). Amir's board: round 1 (1 voucher,
made 27-09 12:59), round 2 (20, 27-09 12:59), round 3 (4 vouchers / 18 lines, 28-09 12:04 — S404's auto-round on Darpan's last answer), round 4
(3 vouchers / 12 lines, 28-09 13:29); closing stock "अभी बाकी — पहले वाउचर Marg में डालें"; the four salt fixes open; Rate daalo: FINGER COT SPILNT
REMEDE, SOFT COLLAR BODY AID S; renames hidden ("नाम बदलना — बाद में, जब वाउचर हो जाएँ"); rounds order 2 · 1 · 3 · 4. Hub verdict: "Orthotics section:
CLOSED by rule on 28-09-2026 -- 10 lines short, Rs 5,420 at selling price (2 without a price); the round 4 on Amir's board · still to follow: 7
orthotic vouchers not yet entered in Marg; proof pending; 22 of 23 renames not yet verified". Darpan's page: 0 lines still tappable, progress
"all 9 answered"; the staff block's fourth line in Hindi under his block; the statement's Orthotics lines read "orthotic loss -- sold without bill"
on voucher round 3, 4 (the lines that were also in a swap) or 4.

**The walk (`walk_s436.py`, on scratch copies of the live database and the spine, the seed run on the copy first):** `WALK_S436 GREEN -- 48 of 48
passed` in the install (and in the final dry run at 13:0x). Its own crafted rows, keyed W436: a same-salt medicine pair (W436 SALTA / SALTB TAB with
one sale each so they leave the 'dead' lane) and one unanswered orthotic short line (W436 WRIST BAND L) for the default path, since by install
time Darpan had answered every real line. Highlights: one answer a side; the removed words nowhere on the page, in the buttons or on a tappable
line; 11 short + 2 extra converted with 13 audits; the defaulted crafted line tappable by Darpan (200), a closed real line 409, the owner's word
200, a removed key 400; one `ortho_close` run (11 loss rows on the copy, Rs 5,420, 3 unpriced with the crafted one; 2 fixes), lane words, all 13
rows closed; round 4 all orthotic, ≤ 6 a voucher; hub CLOSED with the loss; Needs-you once; the statement's texts; the staff block's fourth line
with the first three unchanged (total 6107640 paise); Darpan's block; the desk's 136 written-off lines unchanged and count #1's medicine run
(122 lines) untouched; `count_periods` and the cadence ignore the orthotic run; the record PDF; make-again idempotent; the pairs' notes; the
matcher leaves out the four salt-fix items; the crafted pair proposed → not proposed with a fix open → proposed again when Marg's list shows the
new salt; the board JSON (the four fixes with Marg's salt today, the two rate tasks, rounds order [2, 1] + [3, 4], renames hidden, "अभी बाकी");
the page (the four headings in order, "Marg में डाल दिया", the removed texts absent, no .xlsx, the upload fallback); 28 vouchers entered → every
round closed, renames shown (23), the hub's vouchers green, the proof line "वाउचर डल गए, Marg का अगला closing stock export आने दें"; no 'unit(s)';
the gates as before (the same status matrix for bhati / shavez / darpan / amir / manoj / alisha on the old and the new files).
**Negative control:** the same scenario on the box as it was: `10 of 12 checks red` (four reasons a line, no close by rule, no run, no notes, the
matcher still pairs a salt-fix item, no board sections), the old stockmatch has no `close_by_rule`.

**Earlier walks re-run on the patched files, each against its own pre-kit control (in the install):** S430 42/42 · S427 82/82 · S428 73/73 ·
S431 56/56 · S432 68/68 · S404 65/65. Named adjustments, all in files of this kit:
- `walk_s404_s436.py` (S432's copy + S436): section 4 and the "answer everything" loop use the one-answer vocabulary (BREAKAGE / NOT_RETURNED /
  DONT_KNOW now 400, wrong side); section 10: the section closes by rule the moment Darpan has answered every line — no owner's word awaited, a
  second orthotic round finds nothing, the verdict reads "CLOSED by rule".
- `walk_s431_s436.py` (S432's copy + one DATA adjustment): the statement's line counts read Medicines 287 / Consumables 20, not 288 / 19 — BELL CAST 5
  was moved to Consumables by S432's seed on the live database at 07:5x, after S432 had re-run this walk. Nothing to do with S436.
- `walk_s432_s436.py` (S432's own walk + one DATA adjustment): its negative control asserted "the old box has no stock_pile_cache table" on a copy
  of the live database, which carries that table since S432's install; it now asserts the old FILES lack the cache code and wrote no cache row.
- The installer (not a walk): S430's pre-kit control now stands on the pre-S432 `stock_app` / `stock_statement` / `qty_words` (the `.bak_S432`
  files) under S430's own `.bak_S430` files — today's live stock_app (S432's) calls S432's loss_piles, so the control as S432 built it raised on
  every step. S430's walk is unchanged. **For the next kit:** every earlier control needs the stock_app of its own day.

**Dry runs before the install (DRY=1 NOPIN=1 from /tmp/s436kit, all under the lock):** seven, 11:22 → 13:06 IST. Fixed between them, each a walk or
kit-test matter, none a change to what the owner sees: my crafted pair had no sales (the matcher skips the 'dead' lane by design); a header comment
on Amir's page quoted the removed section names (reworded); a hardcoded statement total; `Rate daalo` first listed every unpriced differing orthotic
(CLAVICAL BRACE M UNISON, a settled swap line) — now exactly the unpriced short lines of the loss; the gate check now compares old = new; the
S430 / S431 / S432 control matters above; and — the real one — **Darpan answered his last two orthotic lines on the live page at 12:04 IST while
the dry runs were going** (both 'does not know'), which made S404's auto-round 3 and left no unanswered line: the walk was rewritten to read the
section's state before the seed rather than assume the brief's counts, and proves the default path on a crafted line.

**Outside the brief / calls made (each as the rulebook asks):**
- The brief's "10 short lines Darpan answered 'does not know'": on the live rows they were 7 'does not know' + 1 'broken or damaged' (DYNA WRIST BRACE
  REVER LONG) + the 2 he answered today. All 10 converted under the owner's words; the "default — Darpan ne nahi likha" path exists (`defaulted`
  lines, tappable) but no live line needed it.
- LACTOVAX SYP: Marg's own item master says FEBUXOSTAT 40 (wrong), so the task's target is the brief's fallback "LAXATIVE (LACTULOSE)". The older
  cleanup task 126 (S243) still says "change both to LAXATIVE SYP" — two wordings for one item; the chat may want to retire 126.
- The owner's Loss desk page `stock_loss.html` was not in the brief's pins and draws the block's first three lines only; the fourth line
  "Orthotics — Rs 5,420 (10 lines, bina bill) · 2 without a price" shows on Darpan's Stock milaan, in the record PDF and in the JSON. A one-line
  change to that page is for a later brief.
- Old section 1 of Amir's board (the S221 lookups) left the page; the data still rides `/finance/stock/api/pad/amir/1` under `lookups` (with
  `tranches` and `ortho_families`) for the owner's reading. No page draws them now.
- 10 orthotic `stock_diff` rows of count #1 stay `open` after the seed: the swap-pair lines the owner answered Yes (ANKLE BINDER L/M TYNOR, CLAVICAL
  BRACE M UNISON, KNEE CAP UNISON L/M LYCRA, KNEE SUPPORT HINGED XL / XXL, L S BELT L / XXL, TYNOR WRIST SPLINT RT M). That is S404's design (a
  settled line closes when Marg's export reconciles it after the voucher); the rule's 12 lines are all closed.
- Gates as before: shavez (like amir, darpan) can read Amir's board and page; bhati is refused everywhere; darpan is refused on the hub. Unchanged.
- `stock_watch.py` v1.3 also drops a duplicate " IST" on the stored watch's time (S432 cosmetic).
- A stray `__pycache__` folder remains under `_scratch/S432_DESK_GROUP_FLOW/kit/` on this PC (git-ignored; `Remove-Item -Recurse` is denied here).
  Nothing of it is in the repository.
- Not done: nothing of the brief was left out.

**After the publish (13:34 IST):** repository published with `PUBLISH_ALL.bat` (gate clean, commit `6658e2c` on main, origin verified); on the box
`git pull --ff-only` → HEAD 6658e2c; `deploy_kits/S436_STAFF_PAGES_CLEAN/` SUMS.md5 15 of 15 OK; `diff -r` repo kit vs `/tmp/s436kit` (what ran):
byte-identical; the repository's own installer run from `/root/deploy/repo`: "ALREADY INSTALLED: the eight files are at the kit's pins;
clinic-finance active; healthz 200"; public healthz 200; the build lock released 13:34:32 IST. This report is published in a second commit.

**Undo:** the eight `.bak_S436_<from8>` files back, `systemctl restart clinic-finance`, healthz 200. The seed's rows are the owner's rulings as data
(the causes, the notes, the tasks, the run, round 4, the close row, the notice); `finance.db.bak_S436_20260928_130938` only if he asks for them to
be reversed — say so first.

https://followup.dr-manoj.in/finance/stockmatch
https://followup.dr-manoj.in/finance/stock/page/amir?count=1
https://followup.dr-manoj.in/finance/stock/page/hub?count=1
