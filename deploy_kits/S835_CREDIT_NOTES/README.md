# S835_CREDIT_NOTES — a dealer's credit note on the sorting desk (D986, F-1174)

Board `_numbers` v1503 → v1504 · built in the Scan App chat, session 464, 14-Nov-2026 · the owner's FINAL mock-up v2 ("Final", 18:39 IST
14-Nov-2026) https://claude.ai/artifact/D8jjGw4t8TjhvZSJWWwRnv · written spec `KB_canon_all/S461_CREDITNOTE_SPEC.md`.

## What it does
- **The reader** (`claude_reader.py`, appended block): the desk's bill reader also answers `doc_kind: "credit_note"`, its own no., the amount
  back, the lines, and `against_no` (the invoice it names). The pharmacy reader's prompt is untouched.
- **The desk** (`sorting_desk.py`): "The reader says this is a CREDIT NOTE … Its no. X, against invoice Y" with [Make it a Credit note]
  [No — leave it]; a sixth kind chip **Credit note**; the box — no., date, amount back; **Against which bill?** (this dealer's bills of the
  90 days before its date, newest first, the reader's pick pre-chosen; each opens its scan and, for a pharmacy bill, Marg's purchase entry
  lines (finance.db, read only, the bill Sanjeevni's register paired the scan with) beside the credit note's lines and whether Marg's
  purchase return is entered (the spine, read only)); or **Not against one bill — on the dealer's account**. One Save.
- **After Save:** pharmacy bill → the pharmacy lane, kind **`Pharmacy credit note`** (every Sanjeevni reader of the scan app reads
  `kind='Pharmacy'` only: it is never paired as a bill; it waits for Amir's purchase return). Clinic bill → filed with it in its group;
  The month shows *bought · Credit notes (−) · Spent* in the month the credit note is dated in (`_s566_total` counts a credit note
  negative: The month, the home card's month total and `xray_costs` read the one sum). On the dealer's account → kept where the person files
  it, lowers nothing, listed on that dealer's statement box. Never accepted (status `captured`), never spend (`clinic_papers` S835: never
  live), never into a stock or list, no payment. The bill's own view: *Bill · Credit note (−, its paper) · Still owed*; `paid_state`,
  `paid_map`, the receipt allocations and the implant ledger count it.
- **One live link** per credit note in the new table `credit_note` (fingerprints on both papers); a re-save that changes it voids the old
  row (kept); saved as another kind after all → the link voided, a pharmacy one back to kind `Pharmacy`.
- **The switch** `desk.cn` — "Credit notes on the desk" on the desk's switch card. **Absent = OFF for Shavez**; the owner sees it always.

## Files
| file | FROM | TO | how |
|---|---|---|---|
| /root/assetapp/sorting_desk.py | baa7c6aa | see PIN_TO | 44 counted edits + the S835 block (make_s835.py) |
| /root/assetapp/claude_reader.py | a7df99bb | see PIN_TO | one appended block (PROMPT, clean re-bound) |
| /root/assetapp/clinic_papers.py | b8f551c4 | see PIN_TO | 4 anchors / 5 places: credit_note never live, never accepted |
| /root/assetapp/xray_costs.py | 5823bae2 | see PIN_TO | 1 edit: the films month total less its credit notes |
Read only (pinned, refused if moved): asset_register, asset_machine, stationery, batteries, procroom, claude_reread, reader_watch.
Nothing of the Sanjeevni chat's or the parent's is touched; finance.db and the spine are only read.

## Proof
- `walk_s835_app.py` on the REAL app (all seven parts, the live shared folder), fresh made-up database, made-up Marg and spine:
  **30 green**; the control on the live files: **27 red, as it must be** (A0, D6, Z1 green both ways).
- `walk_s835_page.js` — the desk page as the app renders it, clicked in a headless DOM (jsdom): **11 green**; control **11 red**.
- `rehearse_s835.sh` on a made-up root: **7/7** (dry run, install, again, wrong bytes, lock, red health → byte-identical restore,
  moved read-only file).

## Install (his publish, then one server line)
    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S835_CREDIT_NOTES/install_s835.sh

## Undo
The installer prints the four `\cp …bak_S835_<from>` lines and `systemctl restart assetapp`. The table `credit_note` stays (unread by the
old code). A credit note already saved stays a paper (doc_kind `credit_note`, captured); the old code shows it with no kind chip.

## Cold review
A separate reviewer (who had not seen the build) found 8 defects in round 1 — the bill list not following a corrected supplier/date, credit
notes against expense-file / lab bills (counted as spend there), stock lines kept, clinic-equipment kind, the switch not gating a pharmacy
credit note, challan kind, wording, the reader wrapper (verified sound). All fixed with a walk check each; round 2: **SAFE TO INSTALL**, two
edge cases (a re-pointed pharmacy credit note on the Documents lane; a late reply of an older bill list) — both fixed too (C8; the page).
