# S771_ORTHOTIC_BILLS — the Orthotic bills card on the Stock check page

**Session 423 (the Sanjeevni chat), 10-Nov-2026. The owner's mock approved 11:27 IST ("go"); D886.** Each orthotics dealer's bill (Yuvika today: `section_count.section_dealers`): what the dealer's bill says (the scan) beside what Amir entered in Marg. A differing line stays highlighted — and its bill stays on the card past its month — until the next Marg export shows it fixed, or the doctor clears it. The scanned bill opens folded under each bill, loaded only on a tap.

| file | from → to | what |
|---|---|---|
| `/root/finance/section_count.py` | `d69e1681` → TO | v1.2: `GET /api/bills` (the doctor's), `POST /api/bills/mark` {bill, key, action: amir / clear / undo}, table `section_bill_mark`, the star at the next count (`start()` → `bill_flags`) |
| `/root/finance/stock_hub.html` | `90da7707` → TO | the card under *Counts in progress*: this month, still open from earlier months, settled earlier; the scan fold; *Amir fixes Marg* / *Marg is right — clear* / *Undo* |

**How a line is judged:** paired one to one (product words, size, side, brand, rate), then size, side (left / right), brand and quantity must agree. A scan word the reader got wrong (no size, two sizes, *V*, *St*, *MN*) takes the Marg line's size and shows as a grey note. A quantity read differently while the line's amount is the same on both sides is a note. A Marg line missing from the scan is a difference only when the totals differ.

**The overflow read (F-1233):** Marg's item-wise export prints a long bill number into the item column (`06202627CAST SHOE M TYNOR`, bill number empty). The card reads those lines for the bill whose number ends in that prefix (the newest export), the prefix cut off. A read only; the reader's own repair is its own kit.

**Writes:** `section_bill_mark` (its own table) and `amir_job` rows of kind `tap` (one per *Amir fixes Marg*, key `S771:b<bill>:<hash>`, as S768 does). Never Marg, `purchase_line` or `assets.db` (read only, `ASSETS_DB` or `/root/assetapp/assets.db`). The scan opens through the Scan App's own route `/scanapp/bills/<id>/file` and its own access rule.

**Proofs:** `walk_s771.py` 33/33 green on made-up rows (pairing, a name read too badly paired by its amount, size / side / brand / quantity, the notes, the overflow read and the newest export by its stamp, the marks with the figures in their key, Amir's job and its undo, the star at the next count, the access, assets.db unreadable); cold-reviewed (code: SAFE, its eight findings fixed; screens: ten findings fixed); the CONTROL on the live files red. `rehearse_s771.sh` 5/5. `proof_s771.py` on the device's copy of the 10-Nov database with the nine scans' lines: this month 2 (803 differs — quantities swapped; 800 agrees) · earlier still open 5 (YS/0706 size XXXL→XXL and Tynor→Bamboo; 672 Tynor→Bamboo; 634 Unison→Tynor; 585 XL→M; 571 Right→Left) · settled 2 (774, 738).

**Install (the owner's paste):**
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s771kit && cp -rp /root/deploy/repo/deploy_kits/S771_ORTHOTIC_BILLS /tmp/s771kit && bash /tmp/s771kit/install_S771_ORTHOTIC_BILLS.sh
```
**Undo:** the installer prints the one line (two backups back, finance restarted). `section_bill_mark` may stay; nothing reads it without the card.
