# S490_ORDER_SHEET_PACKING — the order sheet's reader takes a packing of any shape (F-756)

**Project:** Sanjeevni. **Built by:** the Sanjeevni chat itself (session 296, 06-Oct-2026), on manojz, from the medical PC's live bytes — an urgent mend, not a Claude Code brief. **Touches:** the medical PC's `D:\SendToClinic\marg_txt.py` and Drive `ToMedical\_kit\KIT_MANIFEST.txt`. Nothing on the server, nothing on manojz, not `marg_watch.py`.

## What happened

06-Oct-2026, 13:48:51 IST: Darpan's PENDING ORDERS (PURCHASE) text reached the medical PC and `marg_txt.py` S480 refused it whole — *"line 21: a line of a kind this reader does not know"*. Line 21 was a gel, packing `30GM`; the sheet also carried a `200ML` bottle. `RE_ORDER_ITEM` (S454) knew a packing only as `N*M`. No order reached the server, so reception saw none (the owner, about 14:05).

The shop's item master holds 36 packings of 379 that are not `N*M` (200ML, VAIL, 2ML, 1, 30GM, 75GM, 2.3ML, `200ML.`, 1810 …) — none with a space, none empty. The server's own order reader (`order_sheet._pack`) already takes them as a pack of 1.

## The change — `make_s490.py`, five anchored edits, each anchor exactly once

| | |
|---|---|
| `VERSION` | `S480` → `S490` |
| `RE_ORDER_ITEM` | the packing group `(\d+\*\d+)\.?` → `(\S+?)\.?` — whatever stands in the packing's place |
| `order_rows` | the packing must start in the **same column on every item line of the sheet**; a line that does not is refused by its line number, never guessed |
| comments | two |

Nothing else in the reader moves. FROM `14b750120233e349d713d9de1d1edb7a` → TO `7fa5136d3bc134a55ffd1392d9f06675`.

## Proof — `walk_s490.py`, run on manojz (the texts never leave it): 10 of 10

1. **Every text the medical PC kept** (`_captured_txt`, taken and refused; 72 files: sale 16, stock 11, purchase 19, the lists, valuation, expiry, returns, register, order): OLD and NEW give the same bytes or the same refusal for 71; the one that changes is the refused order sheet of 06-Oct — OLD refuses, NEW reads 16 item lines of 11 suppliers.
2. **Invented sheets (W490):** every packing shape of the item master is read (OLD refuses — the control); a strips-only sheet gives the same bytes OLD and NEW; a packing out of its column is refused; a subtotal that does not tie is still refused.
3. **The server's side, on the 06-Oct 01:35 bundle's code:** the converted sheet is identified `ORDER_PENDING` and VERIFIED by `marg_router`, and `order_sheet._lines_of` takes one line per item with the packing as printed and a pack of 1 for the non-strip lines.

The reader's own `--selftest`: OK on both, line for line the same.

## Delivery

`deliver_S490.ps1` (made from S480's): pins FROM → TO, `.superseded` backups on Drive, md5 read-back, both put back on red. `marg_watch.py` (58b54f37) and `marg_push.py` (566e189e) must be at their pins and are not written. The watcher re-reads `marg_txt.py` when the file changes (S390) — no restart.

```
powershell -ExecutionPolicy Bypass -File "D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\S490_ORDER_SHEET_PACKING\deliver_S490.ps1"
```

**The refused sheet of 06-Oct** is offered to the new reader at the watcher's next start (S397: texts refused in the last three days), or at once if the report is exported again with any change in it (the same bytes are remembered as seen until a restart).

## For S488 (built the same day by Claude Code)

`deliver_S488.ps1` pins Drive's `marg_txt.py` 14b75012 and the manifest ea2b437a as unchanged. After this kit both differ (7fa5136d, 95a1dc5f), so S488's medical-PC delivery needs its script made again on the new pins.
