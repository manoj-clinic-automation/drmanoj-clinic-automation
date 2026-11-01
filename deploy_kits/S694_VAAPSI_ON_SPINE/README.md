# S694_VAAPSI_ON_SPINE — Darpan's returns desk reads the spine

*Sanjeevni session 375 · 01-Nov-2026 · the plan's section 9, step 1; the owner's word 09:28 IST "club these and build now".*

## For the owner
The Vaapsi desk (Darpan's returns screen) was the one returns screen still reading the old sale store for a patient's bill lines; the
returns engine reads the spine since S677. Now the desk reads the same spine: the patient is still found on sale_item, and every line of
his bills — what he bought, how many, at what rate, which expiry, and what Marg's credit notes already took back — comes from the spine.
Where the old store had a bill the spine has more fully (an unread line, a renamed medicine, Marg's own unit for an item like CCM), the
desk now shows the spine's truth. The screen, its words and its flow do not change. If the spine ever cannot be opened, the old store
answers and the counter carries on.

## What changes — one file
`/root/finance/returns_desk.py` **dffbe8fb → 93fd7556** (`make_s694.py`, fourteen anchored edits): the spine adapter (`_spine`, `_k20`,
`_ym_of`, `_units_of`, `_lines_of`, `_patient_refs`, `_catalog_rows`) · `api_history`, `api_items`, `api_catalog` and `_allocate` read
through it · every answer carries `source: spine | old`. **A whole-unit line** (Marg sells CCM by the unit though the packing says 1*40 — the
spine's units say so) is priced at its printed rate per unit, not the rate over the pack: the cold review caught the old strip rule
refunding ₹14 for a ₹560 pack once the units were the spine's; the slip, the picker and the catalog all carry it. The slip's `item_key` is the spine's key from now on; the installer's data step
re-keys any older desk line (0 rows today). Untouched: `judge_line`, the slip, settle, void, the jaankari list, `returns_desk.html`.

## The proof
- **In the device VM, on the 1-Nov database copy and the spine rebuilt from the archive:** the OLD and the NEW desk answered items and
  history for all **533 patients** with a ref in the last 61 days and the catalog for 20 letter pairs — items identical 502, history
  identical 532; every other difference one the kit explains and names: 2 lines the spine holds and the old store had not (an unread
  `***` line), 13 names the spine's alias folds into one medicine (PARI 12.5 → PARI CR 12.5), 18 same-day bill pairs now ordered by bill
  number (the newest bill's discount applies), 14 items where the old desk read a printed "1.0" of a 1*40 pack as a strip (CCM) and the
  spine holds Marg's own unit — their per-unit price is now the pack's price (old price × pack); the catalog's 20-name cut. **Unexplained 0.**
- `walk_s694.py`: 25 checks on made-up rows (patient WALK-9001, medicines WALK…, year 2099; a Flask test client with a made-up login):
  items, history, catalog and a slip from the spine; a line the old store missed; the credit note reducing what is returnable; the spine's
  unit; a credit-note-only item kept out; allocation to the newest bill and the over-bought flag from the item's own lines; the fallback
  to the old store with the spine's key — **25 of 25 green**; control on the live file **14 S694 check(s) red · 11 green**; 6 mutants
  (returns flag, the item filter, the old key, credit notes in the catalog, printed units, the expiry form) all caught.
- **The installer's gate on the box:** the walk, the control, the proof on copies of the live database and spine (every patient of the
  last 61 days) — unexplained 0 or nothing placed; after placing: finance restarted, the desk's login gate answered, the data step, the walk
  on the placed file. Rehearsed on a made-up root: DRY · install · ALREADY INSTALLED · a forced red at [8/8] restores.

## Install (the server)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s694kit && cp -rp /root/deploy/repo/deploy_kits/S694_VAAPSI_ON_SPINE /tmp/s694kit && bash /tmp/s694kit/install_S694_VAAPSI_ON_SPINE.sh
```
**Undo:** `\cp -p /root/finance/returns_desk.py.bak_S694_dffbe8fb /root/finance/returns_desk.py && systemctl restart clinic-finance`

## Named, not done
- Seven old item names longer than 20 letters (`4 *** FINGER EXTENSION SPL 1*1` and its kind — the old store's unread shapes) show as the
  spine's 20-letter name; nothing else is clipped.
- The old sale store (`sale_line_item`) is still written by the ingest and still read by other screens; its retirement is the plan's step 5.
