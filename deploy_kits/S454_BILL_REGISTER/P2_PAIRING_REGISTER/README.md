# S454_BILL_REGISTER · part 2 — P2_PAIRING_REGISTER

Session 283 (Sanjeevni), 03-Oct-2026 · the brief's sections 5, 6, 7, 8 and 12 · D662 D663 D665 · F-690 F-691.

## What and why

- **§5 One set of rules, in one place (`scan_register.py`)**, used by the matcher, the questions, the register and the Sarvam counter.
  - Supplier: `_vendor_match` / `supplier_key` as they are, plus punctuation and brackets dropped, "&" = AND, standalone PVT / LTD / P / CO / M/S
    dropped, a trailing BAREILLY dropped; then the learnt spellings. The shop's own name or a heading = not read.
  - Bill number: Marg's number (zeros dropped) equals one whole digit run of the reading. The financial year, and a licence-shaped
    reading, never count.
  - Date: day and month. Total: within Rs 1 equal; up to `purchase.total_noise_rs` (10) agrees; more differs.
  - **Verified** = the total agrees, the number agrees, and the supplier or the date agrees. This is the only pair the matcher makes by itself.
    **Has its scan** = paired, total agrees or not read, not Verified. **Amount differs** = paired, total beyond the noise.
  - **Auto-link:** the supplier agrees and the amount is within Rs 1 of exactly one unscanned bill of that supplier (dated from
    `porders.scan_from`, within 60 days of the scan, never refused for it) → paired, grade `AUTO`, audit `auto_link`.
  - A link that exists is never undone. A scan whose bill number agrees with a bill names it as its likely bill ("is this the bill?"), so it
    never reaches Amir as a bill Marg lacks.
  - "The amount differs" asks only beyond the noise (it was 2%). The intake link of a Marg bill's line carries that line's supplier only,
    so a scan started from a line settles nothing by itself (the asset app keeps a carried number/amount and never lets the OCR overwrite it).
- **§6 Amir** (`purchase.entry_mode` = paper): step 2 reads "Scan ho chuke bill (N)" with its words and the downloads, and has no grey line.
  On `both`, S452's words return. `digital` is refused with its line.
- **§7.1 The month's register** at `/finance/purchase/page/scans?month=`. Every Marg bill sits in exactly one state: Verified · Has its scan ·
  Amount differs · No scan · Entered twice in Marg · Accepted without paper.
  - The month's scans with no Marg bill sit in their states too.
  - The head counts each state. "Last 7 days" shows readiness. The Sarvam figures are at the foot. A parked month is headed as parked.
  - The owner's "Accept without paper" / Undo, audited (counted months only).
  - `?legacy=1` keeps the old tables.
- **§7.3** The bill-scan Needs-you line only after `purchase.scan_wait_days`. Also new: "Paper not found by reception", and "Scanned and not yet
  in Marg" (owner only, after `purchase.entry_wait_days`). Shavez's page gets one line: "Bill scan baaki: N · sabse purana X din".
- **§7.4 The Sarvam counter** reads by the rules. A wrong year is a miss there only. Batch and expiry are not judged.
- **§8 Vendor payments** (the page, its months, the letter, the annexure, the advice, the pack, and their POSTs) open for the owner and
  `supplier_msg.senders` only. The link is drawn for them only. The phone book shows anyone else the account's last 4 digits and no
  IFSC, and refuses them a bank edit.
- **§12** `manoj.returns_ok` reads the owner's own returns rule. `amir_day` keeps that rule's count in `returns.pending_ok` when
  Needs-you is built. DUTY_MAP v5 also adds `amir.scan_files` (never due) and the new wording of the bill-scan owner line.
- **Found by this kit's staff-eye walk (03-Oct 16:40 IST, on live data):** `amir.arrival_bill_entry` counted an arrival as due the minute it was
  tapped, while its door (Amir's card, stock_watch's "bill entry baaki" list) shows it only after `arrival.bill_grace_days` (3). Its `due_sql` in
  v5 waits the same grace. The owner's line still comes at 3 days, as before.

## Pins (FROM → TO), `/root/finance/`

See `PINS.sh` (TO) and `install_S454_P2.sh` (FROM). New: `scan_register.py`.

## Files

`make_s454p2.py` (patcher; also writes DUTY_MAP v5), `scan_register.py`, `rules_report_s454p2.py` (S454 §5's September report, run before
anything is placed; red on a suspect pair), `walk_s454p2.py`, `plan_old_s454p2.py` + `walks_old_s454p2.py` (the earlier walks),
`data_s454p2.py` (the data step), `install_S454_P2.sh`, `PINS.sh`, `DUTY_MAP.json` / `.md` (v5).
