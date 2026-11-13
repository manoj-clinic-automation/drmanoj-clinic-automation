# S811_MARG_WATCH_SMALL — the Marg watch's five small things, its console line, the 05-Oct part lists retired (13-Nov-2026, Sanjeevni session 441)

**The owner's "ok" (06:42 IST 13-Nov)** to the build list; on F-1280 his word: *"the latest export should settle it"*.

**The kit.**
1. `/root/finance/marg_billwatch.py` (616490b4 → TO), the five small things S438 noted: on an agreeing or settled row the scanned paper sits full width above the lines (it was a narrow side column) · *For the record — 24 entries* (it said "bills"; three bills appear twice) · a day on which two lists of one kind were taken shows their times · the month grid's *Added late* names a sale bill counted in it · a list that held none of its period's bills says so (*held none of the 25*), not "held 0 of 25".
2. `/root/finance/owner_console.py` (ba977832 → TO) — **the parent's file, PLANNED on board/_numbers v1332**: ONE line in the Sanjeevni section, *Marg watch · N changed bills to look at · M new*, the page's own reader (`marg_billwatch.build`), linked to `/finance/sanjeevni/marg-watch`; a reader that fails is one grey line. Nothing else in the file changes.
3. `repair_s811.py` (F-1280): the three 05-Oct purchase lists of 1 Sep–3 Oct (item list 5 rows, item list 208 rows, bill-item list 0 rows — all live) marked as replaced by September's complete item list of 20-Oct (15b9d64a). Proved inside the same transaction first, or nothing is written: every one of their 213 lines is in a later live list (15 under the orthotic names Marg carries since); September's 86 and October's 82 bills' line sets are the same export and money; the effective bills the same (September ₹4,31,016, October ₹3,72,609). The before-state is saved beside the database.

Both files are rebuilt on the box from the live bytes by `make_s811.py` (exact anchors and whole functions whose md5 is checked).

**Proof before it left the bench.** `walk_s811.py` 13/13 GREEN, its control on the live files 11 red · the Marg watch's own walk `walk_s803.py` (74 checks) GREEN on the rebuilt page · the page rendered on a copy of the 13-Nov database by the live and the built file: only the intended words changed · the console's Sanjeevni lines on that copy: *Marg watch · 19 changed bills to look at* (the copy has no scanned papers; on the box the settled ones drop out) · `repair_s811.py` on that copy: dry, apply, again (ALREADY) · `rehearse_s811.sh` 7/7.

**Install (the VPS, one line):**

    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s811kit && cp -rp /root/deploy/repo/deploy_kits/S811_MARG_WATCH_SMALL /tmp/s811kit && bash /tmp/s811kit/install_S811_MARG_WATCH_SMALL.sh

**Undo:** the installer prints the line for the files; the database step: `UPDATE purchase_export SET superseded_by=NULL WHERE md5 IN (the three)` (printed by the repair).
