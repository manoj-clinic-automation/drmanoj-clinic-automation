# Claude Code brief — S409_SCAN_LANES (whoever holds the paper scans it: five lanes, a duplicate guard, late bills, pharmacy scans from 01-Sep)

Written 26-Sep-2026 by the Sanjeevni chat (S283). Read `CLAUDE.md` first. **Kit S409 · decision D625 · fault F-633.** The owner approved
this WHAT (26-Sep). **Runs FOURTH, after S407 and BEFORE S408** (S408 reads the lanes). **Ownership: PARENT (the asset app) — the README
says so.** The asset app is a separate service (`assetapp`, `/root/assetapp/asset_register.py`, its own `assets.db`); S403 touched it
(intake pre-fill, 71bd3277 → 30b26d28) — read the live pin.

## 1 · The owner's words (26-Sep)
- "Medicine purchase, lab bill purchase, my expense files are all planned to be scanned; and any bill or document arriving at reception is
  scanned by reception and gets a number they write on it. X-ray films may go to the staff directly; lab ones to Sukhveer; some bills arrive
  late. Is depending only on reception right, or should Sukhveer, Shavez and I scan too — and what if a bill is scanned twice?"
- Agreed flow: **whoever holds the paper scans it at once and writes the number on it; a paper already carrying a B-number is never scanned
  again**; each person's drop-down opens on their own head; the server catches duplicates; late bills file by their own date.
- "Sanjeevni purchase bill scanning starts from **1st September**" — the bills-without-scan lists begin there, not 17-Aug.

## 2 · What exists (`/root/assetapp/asset_register.py`, read the live bytes)
- ONE intake `/scanapp/intake` (`intake()`, `_create_intake_bill()`, `intake_scan_submit`/`intake_submit`), ONE stamp series `next_stamp()`
  (B-0001…, never reused; a rejected bill keeps its stamp — the void-pair discipline), the select `intake_lane` with two values:
  `clinic` (→ `bills.kind='Consumable'`, `status='draft'`, the checker's approval queue → spend/assets/expiries) and `pharmacy`
  (→ `kind='Pharmacy'`, `status='captured'`, never in approval; matched to Marg by `purchase_app._scans()` — S403 pre-fills it).
  Sarvam OCR in the background fills vendor / bill_no / bill_date / total_amount (`ocr_status`). **No duplicate check of any kind exists.**
- Access: reception role reaches only RECEPTION_OK; owner/manager reach everything. The **Scan Purchase** tile is on the staff role, masked
  only from amir and bhati (`tile_grants.json` v28) — Sukhveer, Awdhesh, Shavez, Shivani, Alisha, Darpan and the owner already have it.
- `bills` table columns incl. `stamp_no`, `status` (draft/approved/rejected/captured), `submitted_by`, `source_stored` (the file).
- Finance side: `purchase_app.py` (as S407 left it) — `porders` "Bill scan karo" list and the owner's `/page/scans` red list count purchase
  bills since 17-Aug (S403).

## 3 · The build (D625)
1. **Five lanes**, one select, stored in a new column `bills.lane` (backfilled: Pharmacy→`pharmacy`, everything else→`clinic`):
   `clinic` (as today, approval) · `pharmacy` (as today, captured, Marg match) · `lab_purchase` "Lab purchase — NK Pathology" (captured, no
   approval) · `owner_expense` "Dr MK expense" (captured) · `other_doc` "Other document — not a bill" (captured, no OCR amount expected).
   Only `clinic` enters the approval queue, spend and expiries — assert every `/purchases` query still filters `status='approved'` (S219's
   reasoning holds). **Per-user default lane** in a small settings table (`user_lane_default`: sukhveer→lab_purchase, awdhesh→clinic,
   darpan→pharmacy, manoj→owner_expense, everyone else→clinic; owner-editable on a settings card) — the select opens on it.
2. **Duplicate guard, at capture, two layers.** (a) **Image fingerprint** of the flattened first page (a perceptual hash if Pillow is
   available in the asset app's python — check; else a robust text fingerprint of the OCR text) stored in `bills.fp`; (b) after OCR, the
   triple vendor + bill_no + total_amount against bills of the last 90 days. A hit on (a) at once, or on (b) when OCR finishes: the new bill
   → `status='rejected'`, `dup_of=<id>`, note "duplicate of B-nnnn"; the **stamp slip** (`intake_slip_last`, which the page polls for a few
   seconds after capture) says in Hindi: `Yeh bill pehle B-0123 par scan ho chuka hai — wahi number likho`. A near-miss (same vendor and
   amount, bill_no unreadable) → `dup_flag='maybe'`, amber on the checker's bills list with two taps **Duplicate** / **Not duplicate**.
   Approving (`bill_approve`) a bill whose triple matches an approved one is refused naming the stamp. Pharmacy/lab/expense duplicates never
   reach the Marg match or a pack (S408 and `purchase_app._scans()` read only non-rejected rows — add the condition where missing).
3. **Re-lane, one tap** (owner/manager, bills list and bill view): moves `lane` (and kind/status accordingly: into `clinic` = draft;
   out of it = captured), audited (who, when, from→to). A bill already approved cannot leave `clinic`.
4. **Late bills:** `bills.bill_date` from OCR (owner/checker may correct it); a bill scanned in a later month than its bill_date carries
   `late_for=<YYYY-MM>` — S408 files it under "Late — belongs to <month>"; the pharmacy match is unaffected.
5. **Pharmacy scans from 01-Sep-2026:** setting `porders.scan_from = 2026-09-01` in finance.db; `porders` "Bill scan karo" and the owner's
   `/page/scans` red list count purchase bills from that date (one anchored edit each in `purchase_app.py` / `porders.py`; Sanjeevni-owned,
   declared). Older bills are neither listed nor red.
6. **Monthly count per lane** on the owner's `/purchases` dashboard (one line) — S408's checklist reads the same numbers.

## 4 · FROM pins (read live first; mismatch = stop that file and report)
| file | FROM |
|---|---|
| /root/assetapp/asset_register.py | 30b26d280c6cdf373774a94aae59f339 (S403 TO — read live; clinic — declared) |
| /root/assetapp/scanner_widget.js | read live — only if the slip poll needs it; prefer the page/slip route |
| /root/finance/purchase_app.py · /root/finance/porders.py | as S407 left them — read live (the scan_from setting; Sanjeevni) |
Restart `assetapp` (+ `clinic-finance` for the scan_from edit). No portal/grants change (the tile is already everywhere it should be).
The intake stays on the same address: `https://followup.dr-manoj.in/scanapp/intake`.

## 5 · The walk (scratch copies of assets.db and finance.db; crafted images; own rows keyed W409*)
Five lanes store the right kind/status; only clinic enters the approval queue and `/purchases` totals (negative control: a lab_purchase
row never appears in spend) · per-user default lane renders for each crafted login · the same image twice → second rejected with dup_of,
slip text names the first stamp; a re-shot of the same paper (slight crop/rotation) still hits when the fingerprint is perceptual (say if
it is text-only) · the OCR triple hit rejects; a near-miss flags amber; Duplicate/Not duplicate store · approve of a triple-match refused ·
re-lane moves and audits; an approved bill refuses to leave clinic · late_for set on a crafted old bill_date · scan_from: a purchase bill of
25-Aug is not listed/red, one of 02-Sep is · S403's pre-filled intake still lands on `pharmacy` · reception still reaches only its routes ·
S400–S407 walks re-run green.

## 6 · Done means
Kit `deploy_kits\S409_SCAN_LANES\` (README: owner = parent; the scan_from edit named as Sanjeevni's) · installed, md5s read back · assetapp
login page 200, finance healthz 200 · published · `claude_code_briefs\REPORT_S409.md` (owner lines first: the five choices as the staff see
them, what happens on a double scan, who opens on which head; ending with `https://followup.dr-manoj.in/scanapp/intake`). Then S408.
