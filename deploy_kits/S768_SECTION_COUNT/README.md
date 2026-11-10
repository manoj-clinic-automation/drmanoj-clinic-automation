# S768_SECTION_COUNT — the section count on Stock milaan (Orthotics first)

**Session 420 (the Sanjeevni chat), 10-Nov-2026. The owner, 05:13–05:35 IST:** the orthotic count table as its own page in Stock milaan — printable blank or with counts, enterable online; the 21 count-twice lines highlighted, #44 and #45 most; a feature to run whenever wanted; the list updating itself with new products; whatever is flagged into the section counted; a bill not yet in Marg never counted as stock.

| file | from → to | what |
|---|---|---|
| `/root/finance/stockmatch.py` | `623cb6f1` → `d80523b6` | `init()` mounts `section_count`; if it cannot, Stock milaan still works and the journal says `section_count NOT mounted` |
| `/root/finance/stockmatch.html` | `02826136` → `0ec2e32d` | one link under the title: *Orthotics ginti (shelf count)* |
| `/root/finance/section_count.py` | NEW | the count: `/finance/stockmatch/count` and its API; five tables of its own, created on first use |
| `/root/finance/section_count.html` | NEW | the page — PC and phone; print blank / with counts; CSV |
| `finance.db` | seed, insert-only | the display of the 75 orthotic names and the 21 marks of S420's paper (19 one star, #44 and #45 two stars) |

**How it works:** *Start* takes every item of the section in Marg's newest closing (the nightly seed files new names, so new products join). The marks are frozen at the start: the doctor's own, an open Marg hand change, and — from the second count on — the record since the last count (a gap: one star; 3 or more: two). **The guard:** a scanned bill of a dealer who supplies the section that is not in Marg yet blocks the start; only the doctor may start anyway (recorded). Boxes that came without a scanned bill go in *Came in, not yet in Marg* and are never counted. **The correction** (the doctor only): Marg at the count = the count day's closing + what was sold after the count (before the first sale: the whole day; during: after the last bill number; after the last sale: nothing); ready the next night. *Send to Amir's card* puts one tap job per changed line and one per rename (a name that loses its size in Marg's 20-letter sale report) on his card. Nothing writes to Marg; the 06-Sep count is untouched.

**Proofs:** `walk_s768.py` 44/44 green on made-up rows; the CONTROL on the live files red. Two cold reviews: the first NOT SAFE (four must-fixes, all built in), the second SAFE. `rehearse_s768.sh` 5/5. `proof_s768.py` on the device's copy of the 10-Nov database: 75 lines, 19 one-star, 2 two-star (#44, #45), 4 renames — exactly S420's paper.

**Install (the owner's paste; DRY first):**
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s768kit && cp -rp /root/deploy/repo/deploy_kits/S768_SECTION_COUNT /tmp/s768kit && DRY=1 bash /tmp/s768kit/install_S768_SECTION_COUNT.sh
```
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s768kit && cp -rp /root/deploy/repo/deploy_kits/S768_SECTION_COUNT /tmp/s768kit && bash /tmp/s768kit/install_S768_SECTION_COUNT.sh
```
**Undo:** the installer prints the one line (the two backups back, the two new files removed, finance restarted). The seeded rows stay; nothing reads them without the new files.
