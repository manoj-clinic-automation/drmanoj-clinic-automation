# S976_WHOLE_UNIT_PACK — CCM counted whole (F-1742)

**28-Nov-2026 · Sanjeevni session 543 · by Opus · his "Ok" 14:02 IST on the mock-up** (Darpan's CCM line: one Botal box, like a gel's Tube):
https://claude.ai/artifact/TLhhxcwJ2MDXuEf6QzsDkJ

**The fault.** CCM is on the desk's whole-unit list (`stock.whole_unit_items` = `["CCM = bottle"]`): the shop sells, counts and stocks it
by the bottle, and Marg prints every CCM figure in bottles. Its packing is `1*40` (tablets in the bottle). `stock_figure.pack_of` read that
packing as a pack of 40, so the stock record read Marg's bottles as tablets, Darpan's count screen asked for Patte + Goli with "ek patte
mein 40" and stored his one bottle of 28-11 as 40, and the voucher reading from the medical PC took Marg's issue of 3 bottles (L000009) as
3 packs = 120.

**The fix (five files, each change an appended block re-binding one function, plus one anchored line).**

| file | FROM → TO | what |
|---|---|---|
| `/root/finance/stock_figure.py` | 0d8cab56 → 428effea | `pack_of` = 1 for an item on the whole-unit list (the record, shelf_figure, Stock check); `_s976_whole` reads the list from the database and hands it to qty_words |
| `/root/finance/stock_watch.py` | fe0a89cd → 02894900 | `item_info` pack 1 for such an item (his asks, Abhi ginti, Stock batao, Kuchh gadbad hai); `build_roster` puts the day's unanswered list rows to pack 1; `roster_view` loads the word list first (Botal) |
| `/root/finance/stockmatch.py` | 1f5a15ba → 91b5193f | one line: the item search's pack through `_s976_pack` |
| `/root/finance/voucher_judge.py` | 59a68bb1 → 1fb41376 | Marg's voucher line of such an item read in the bottles printed (3, not 120, told "3"); `_pack_of` 1; S975's "cannot be judged yet" stands only while the record's pack is above 1 |
| `/root/finance/stock_check.py` | 6b8d077c → 03a2f557 | band 2 tells such a count in its bottles at pack 1 ("counted 1 bottle · Marg 2 bottles · −1 bottle", D1107) |

Every item NOT on the whole-unit list reads exactly as before: on two copies of the 28-Nov database (the real 390-item record built by the
old files and by the new) every non-whole row is identical; only CCM's pack moves 40 → 1.

**The data.** `fix_s976.py` divides a count-screen count of a whole-unit item stored as whole packs by the pack it was stored with (CCM 28-11:
40 → 1 bottle), with its morning-list row (qty, pack 1) and any loss line beside it; every row's before-image in table `s976_fix`; never
more than 3 points (refused otherwise); never twice. The 06-Sep full count (stored in bottles) is not touched. The installer then rebuilds
the stock record (under the record cron's own lock) and judges that count again (`record_judges.rejudge_all`, its own undo rows).

**Assessed, not changed.** `expiry_watch.py` reads Marg's batch figures as printed (CCM 2 bottles = 2): words only. `marg_vouchers.py` and the
medical PC's reader keep the 120 as stored; the judge reads it right. `item_ledger.py`: S975's whole-pack wording falls silent at pack 1
(its `pack <= 1` return) and the ledger tells bottles in its own word. `stock_watch._candidates` (the morning list's ranking) still ranks
CCM by its packing; the list row is put right after it is written.

**Proof.** Walk `walk_s976.py` 40/40 (twice on one layout), the control red on the live files at A1; S975's, S973's, S971's, S969's, S967's and
S965's walks give the SAME results on old and new files (the installer compares them); the S952 / S956 / S957 / S958 walks on the 28-Nov copy
the same on old and new (VM only, no spine). Rehearsal on a made-up root with the real-shaped 28-Nov database and a spine made from its
closing prints: dry · red@4 · red@5 (data put back, record rebuilt at 40) · install · again · undo · install again · wrong FROM · a read pin
moved · the lock · a corrupt kit = 11/11. NO_PHONE_NUMBERS clean.

**Install (one server line, after his publish):**

    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s976kit && \cp -rp /root/deploy/repo/deploy_kits/S976_WHOLE_UNIT_PACK /tmp/s976kit && bash /tmp/s976kit/install_S976_WHOLE_UNIT_PACK.sh

**Undo:** `bash /root/deploy/repo/deploy_kits/S976_WHOLE_UNIT_PACK/undo_s976.sh` — the five files back, every `s976_fix` row put back, the
record rebuilt by the old files.

**On the real 28-Nov data (VM copy, item names only):** of Marg's 254 voucher lines only CCM L000009 changes (120 → 3); CCM's 06-Sep
correction of 3 bottles then reads "in Marg". **Cold review** NOT SAFE → 1 MUST (the voucher line's `per` left at 40: "0:3") + 3 SHOULD
(the installer to require the fix's own FIXED line; the rows chosen inside the write lock; today's unanswered list rows put right at install)
+ 1 note (a count whose list row already asked in whole pieces is never divided) — all built in.
**Second look** SAFE, 3 SHOULD — all built in: a copy or a live database with nothing to fix (n=0) no longer stops the install; the morning-list
rows the install re-packs are recorded in `s976_fix` (the undo puts them back) and a failed install's record rebuild takes the record's own
lock; the undo puts back only the columns the fix (and its re-judging) set, and only where the fix's mark still stands — a row changed since
is left as it stands and named.
**Re-look** NOT SAFE → 1 MUST (a re-judged resize sets a loss line's `mrp_p`; the undo now puts it back) + 1 SHOULD (a list row re-packed at
install and answered since is never put back to 40) — both built in. Known and accepted: an undo after a later re-judging of the same count
(quantity unchanged) puts back the judgment from before the fix.
