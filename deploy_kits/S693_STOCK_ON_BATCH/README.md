# S693_STOCK_ON_BATCH — new stock placed on its batch from the purchase report

*Sanjeevni session 375 · 01-Nov-2026 · the plan's section 9, step 0 (the S690 plan's step 3); the owner's word 09:28 IST "club these and build now".*

## For the owner
The expiry watch takes every batch of the newest whole-shop Batch Stock and lowers it by the sales since — but a purchase since the
report reached no batch, so a medicine bought again (93 of 159 sold in October) was judged only by Marg's own printed minus, and a counter
sale into a minus batch on such a medicine waited for the next monthly report. Now the purchase item report's lines since the report are
placed on their batch (the report prints the last 8 characters of a batch; 83 % tie to one batch, a batch the Batch Stock does not print is
a new one), and a re-bought medicine is judged like any other. A line that fits two batches, or carries no batch, leaves its medicine judged
as before. Nothing on any screen changes; Amir's vouchers (S690) come from the same figures.

## What changes — one file
`/root/finance/expiry_watch.py` **b68cda86 → 15417df5** (`make_s693.py`, six anchored edits): the kit's name on each run · `_s693_place`
(the effective purchase exports only — the purchase page's own rule; medicines; bill date after the report's day; units = the report's
loose figure, Marg's own unit, else qty + free × pack) · the placement before the sales are taken off · a sale whose batch is printed
differently from the Batch Stock's ties by the same letters-and-digits rule · the wrong-batch rule for a placed re-supply · the run's note
(`S693: N purchase line(s) since <day> placed on M batch(es), K new; untied …`).

From the cold review (built in): the same bill line in two overlapping live exports is placed once (S227's rule); a medicine is judged
as placed only when the report's placed units cover the spine's own purchases since the day (a report that lags the spine leaves it
untied); the tie is symmetric, so a sale printing a batch in full ties to a new batch made from the report's 8-letter clip. **Units are
Marg's own loose figure** — the Batch Stock's unit (THIO Q AP 1*10: bought 10 + 2 free, loose 12, the Batch Stock prints 12; CCM 1*40:
loose 5, printed 5) — not the count's tablet rule, which would place 132 and 205 against prints of 12 and 5; the review's objection was
read against the real prints and the loose figure stands.
Untouched: the readers, the voucher pair's judging (printed figures), the owner's page, Amir's words, every other section, every table.

## The proof
- **In the device VM, on the 1-Nov database copy, the spine rebuilt from the archive, and the archive:** on the live archive (newest report
  30-Oct, no sales after it yet) old = new, 102 of 102 lines identical; on the archive with only the 22-Oct report (sales after it to 27-Oct):
  21 purchase lines placed on 21 batches (12 new), 117 of 122 lines identical, **3 minus batches newly named** — each read against its sales
  since the report or Marg's own printed minus (BIO D3 MAX: two printed minuses beside the re-supplied batch; ONKET DT: 18 sale lines into
  SPT613; TRAMAVIN GEL: 9 into JH-A108) — and 5 wrong lines whose stock-holding batches gained the purchase. Nothing else differs.
- `walk_s693.py`: 22 checks on made-up rows (medicines WALK…, year 2099): the tie by the last 8 characters, a new batch with its expiry on
  the near list and in the voucher pair, two fits → untied, no batch → untied, a sale batch printed without its prefix, a purchase dated the
  report's own day not added, a superseded export ignored, an orthotic ignored, no loose figure → (qty + free) × pack — **22 of 22 green**;
  control on the live file **13 S693 check(s) red · 7 green**; 12 mutants (any fit, the old bought rule, the day's own purchases, superseded
  exports, orthotics, no sale tie, free left out, no dedupe, the spine's purchases ignored, a one-way tie, the count's tablet rule) caught.
- **The installer's gate on the box:** the walk, the control, then the OLD and NEW watch on copies of the database and the spine, twice —
  on the live archive and on the archive without its newest report (so purchases since a report exist) — every difference must be one the
  kit explains, or nothing is placed. After placing: finance restarted, the walk on the placed file, then the watch run once (last, so a red before it writes nothing). The
  second proof drops the very report the first proof read and must place at least one line, or it proves nothing and nothing is placed;
  a set OFF switch refuses the install at [1/8].
- Rehearsed on a made-up root (the VM): DRY · install · ALREADY INSTALLED · a forced red at [8/8] restores · a changed live file refused.

## Install (the server)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s693kit && cp -rp /root/deploy/repo/deploy_kits/S693_STOCK_ON_BATCH /tmp/s693kit && bash /tmp/s693kit/install_S693_STOCK_ON_BATCH.sh
```
**Undo:** `\cp -p /root/finance/expiry_watch.py.bak_S693_b68cda86 /root/finance/expiry_watch.py && systemctl restart clinic-finance`

## Named, not done
- A purchase keyed into Marg with a bill date on or before the report's day but entered after the print is not placed (the Batch Stock is
  taken to hold it) — the same cut the spine's purchase moves already use.
- The 5 % of lines that fit two batches and the lines with no batch stay as before (their medicine judged by the printed minus only).
