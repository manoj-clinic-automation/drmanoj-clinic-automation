# S604_PAY_SHEET_FIXES — the NEFT payment sheet takes the reports, asks for them, and locks only on them

**Brief:** `claude_code_briefs/S604_PAY_SHEET_FIXES.md` (v2, Sanjeevni session 333, 20-Oct-2026) at the owner's word of 08:17 and 08:25 IST:
*"do all what is required for the NEFT payment sheet so that it accepts reports and other things are also corrected … The vendor payment kit
should specifically ask for the final uploads of the REQUIRED purchase reports as text files and should give confirmation when these files
are received by it."* The independent read R1 (`03_WORKING_PAPERS/S333/S604_R1_REVIEW.md`, four blockers, seventeen corrections) is folded in.
Repairs **F-956** (the reader's returns; the server counting returns as returns), **F-955** (the clipped-name twin), **F-954** (the two boxes);
the owner's ask is the card (3.4) and the lock gate (3.5). No D-number minted. One restart of `clinic-finance`.

## Pins (FROM → TO)

| file | FROM | TO |
|---|---|---|
| `/root/finance/purchase_app.py` | `60f2d846155659c4eddc33e4a0d42b39` | `447b745f16c81ef62d389900d1d8ae13` (25 anchored edits, `make_s604.py`) |
| Drive `ToMedical\_kit\marg_txt.py` (→ medical PC `D:\SendToClinic\marg_txt.py`) | `a59a222faf32a72ccc19c8635955cf8d` (S546) | `e8a60d9df79ed9fb763e2be4c4f23d4f` (S604, 5 anchored edits) |
| Drive `ToMedical\_kit\KIT_MANIFEST.txt` | `0bf248e43381bd27f6d011648b8405ee` | `ddd0eadb169f9f1a78c7befa5a550aaa` (the reader's md5 on its line; nothing else changed; CRLF) |
| `/root/finance/finance.db` | — | one audited data step (`data_s604.py`), no DDL, no new table, no new setting |

Read only, must not move (checked by the installer): `amir_day` 1169a3d6, `stock_app` 40f2c922, `stock_watch` f0d9092a, `amir_salts` fc5c1d16,
`marg_purchase_rows` 41d68148, `supplier_msg` 6366ed0f, `packs` e46264b8, `bank_sms` aa527840, `export_watch` f6845ec5, `reports_tile` 535b5790,
`marg_door` dc5c1e36; Drive `marg_watch.py` 39fa2773 (S556 — its re-offer on a reader change). Proved unmoved: `finance_app.py`, `portal.py`,
`tile_grants.json`, the crontab, `spine.db`'s and `finance.db`'s schemas.

## What it does

- **The medical PC's reader (`marg_txt.py`, F-956 A).** Marg's SUPPLIER/ITEM WISE PURCHASE STATEMENT prints a supplier's purchase returns as
  ordinary lines and subtracts them in its own TOTAL (L.K. DRUG HOUSE, 20-Oct 08:06, line 177: the lines exceed the TOTAL by exactly twice
  the three returns). A block is now taken as "returns inside" only when a set of at most 6 of its lines — in a block of at most 40 lines,
  every line positive in both money columns — adds to exactly half the excess in both columns at once (twice the set = the excess, to the
  paisa), found by a bounded pass over paise states (cap 200,000). The GRAND TOTAL is then held against the sum of the printed TOTALs. Every
  other mismatch refuses with the words of before. The sheet written is unchanged (no line marked). BILL/ITEM WISE is not changed.
  `VERSION = "S604"`, the docstring's S604 paragraph, ten selftest checks on made-up blocks shaped as L.K. and KEDAR.
- **Returns counted as returns (`_month_summary`, F-956 B).** A bill whose Marg amount carries the minus sign and whose line set is positive
  counts its lines negative, at read time; nothing stored changes. `_month_summary` returns `signed`; a signed bill that agrees is "agrees",
  one that still differs goes to `short` (offered a verdict), never to `returns`. The pay sheet's flag and the month page's chip say *"a purchase
  return — Marg prints its lines as a purchase; counted as a return"* (no "needs correcting"). April, May and July's item-wise figures become
  ₹3,82,174.00, ₹3,68,046.35, ₹4,76,392.96; September with this morning's lines ₹4,31,016.47 (Marg's GRAND TOTAL).
- **The clipped-name twin (`_store_bills` → `_s604_bill_lookup`, F-955).** A row retired as *"twin of bill N"* is read as bill N; when no live
  row has the incoming key, the one row of the same bill number and date whose other report carries the same amount, whose column for this
  report is empty or holds another export, and whose key is a word-boundary prefix of the incoming one (or the other way round) is joined,
  audited `twin_joined`; a stored shorter key is renamed to the longer only when nothing else names (short key, bill_no). The archived
  `…5307d3e5.XLS` shows the cause: row 11 holds `BASS PHARMA DISTRIBUTORS PVT` | `LTD29-09-2026` — the 32-letter name overflowed into the
  DATE cell and `marg_purchase_rows.iso_date` dropped "LTD" (named, not changed).
- **The data step (`data_s604.py`).** One transaction, guarded: audit `twin_merge` ref `542<-579` with both rows' full JSON; bill 542 takes
  `sw_md5 5307d3e5…, sw_amount_p 159700` (only where its `sw_md5` is NULL); bill 579 gets `sw_md5 NULL, sw_amount_p NULL, reason 'twin of bill
  542 (supplier-wise clipped the name; S604)'` (only where it holds 5307d3e5 and no bill-wise). Both UPDATEs must touch one row, else rollback.
  Skipped when the audit row exists. 579 is kept and stops being effective. September: 86 bills, ₹4,31,016; the cheque lane owes ₹1,597.
- **The month-end reports card (`_month_reports`, `_s604_reports_card`).** At the top of `/finance/purchase/page/pay/<M>`: the supplier-wise
  statement, the bill-wise statement and the item lines — *Received dd-Mon hh:mm · period · N bills* (and the supplier-wise total against the
  sheet), *Not yet — export from Marg as a TEXT file: <TITLE>, FROM 01-MM-YYYY TO <last>-MM-YYYY*, or *Received … — but N bills still have no
  item lines (dates): export …*; a purchase refusal from the medical PC after the month's end and after the newest covering export, in one
  line; the green *"All three reports are in and agree — the month can be locked."* when the gate is open.
- **The one lock gate (`_lock_gate`).** `_month_summary`'s reasons, plus one per report not received, plus — when the supplier-wise statement is
  received — the cross-check's first problem. `api_finalise`, the month page's FINALISE button and note, the hub's "ready to finalise" and the
  card's green line all read it. `_month_summary` is not changed by it (no recursion). `_verify_statement(con, month, s=None)` uses the month's
  last day, not the 28th.
- **The two boxes (F-954).** Carried in has no numeric keypad (a phone can type the minus); `api_pay_line` reads `−` (U+2212), `–` (U+2013), a
  leading `-` and a trailing `/-`, refuses an unreadable figure (`400 malformed`, the row unchanged), writes the note only when the request
  carries it, and replies with the new payable, `updated_at`, `updated_by`; under each typed vendor (editable sheet only, never the printed
  pack) *"Saved dd-Mon hh:mm by manoj — payable now ₹0"* and the note; the box shows *"Saved — payable now ₹…"* before the reload. Paid stays
  a record.

## The walks

- `walk_s604.py` (server; scratch copies by the backup API; the finance folder twice; the walk's own portal secret and user store; its own
  rows by key): §0 page dumps OLD vs NEW; §5b every money reader April–October (no recursion; only April/May/July's item-wise moves); §2 this
  morning's text converted by the kit's reader and pushed through `/api/push`; §3 the twin (join, re-export, retired twin, true pairs, the data
  step twice); §4/5 the card, the refusal line, the gate, `api/finalise`; §6 the boxes; §7 the greps. `--expect-red` on the OLD file: every
  `C:` control red. `--state` for the install-day state.
- `proof_s604_reader.py` (manojz, before the Drive delivery): the selftest; this morning's two texts (taken by S604, refused by S546 at 177);
  the real text altered (L.K. ±0.02 refused; KEDAR −100 refused by both; KEDAR +0.02 accepted by both); every kept text the same bytes.
- S603's walk is run on the NEW and the OLD file and must read identically (on 20-Oct it is red on the untouched live files too: the live
  copy carries real open visit days its scenarios did not expect — a finding for the chat, not this kit's).

## Install

Server: `S604_TEXT=/tmp/s604data/<the 20-Oct 08:06:12 text> bash install_S604_PAY_SHEET_FIXES.sh` from a copy of this folder (DRY=1 first).
Medical PC (by the build runner, S546's road): backups beside the Drive files (`marg_txt_S546.py.superseded`, `KIT_MANIFEST_S546.txt.superseded`),
read back; `marg_txt.py` placed first, then the manifest; both read back; then the heartbeat, the watcher log, the census and the server's
`purchase_export` read every 60 s for at most 60 minutes. Not seen by then: left placed, said in the report.

## Undo

- The server file: `\cp -p /root/finance/purchase_app.py.bak_S604_60f2d846 /root/finance/purchase_app.py && systemctl restart clinic-finance`.
- The data step (only if the twin's merge must be reversed): `python3 -B data_s604.py --db /root/finance/finance.db --undo` — it puts 542's and
  579's supplier-wise columns and 579's reason back from the `twin_merge 542<-579` audit row's JSON and writes `twin_merge_undone`.
  By hand: `UPDATE purchase_bill SET sw_md5=NULL, sw_amount_p=NULL WHERE id=542; UPDATE purchase_bill SET sw_md5='5307d3e5b82ec416cb70144a9efaeb6e',
  sw_amount_p=159700, reason=NULL WHERE id=579;`
- The medical PC: put `marg_txt_S546.py.superseded` back as `marg_txt.py` and `KIT_MANIFEST_S546.txt.superseded` as `KIT_MANIFEST.txt` on Drive.

## Seen, not touched (named)

BILL/ITEM WISE's own returns check; the bank file downloads before the lock with no DRAFT mark; negative payables summed on the page and in
`bank_sms.neft_portion_p` while the advice skips them; undated lines not blocking; the stale 09-01..10-01 bill-wise export still live; bill-number
case twins; the manojz reader's date-overflow rule (`marg_purchase_rows.iso_date`); phase 2 of the refusal note (naming the report); vendors with
no account on the cheque lane.
