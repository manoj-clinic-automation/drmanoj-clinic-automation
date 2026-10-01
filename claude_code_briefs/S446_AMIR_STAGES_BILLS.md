# Claude Code brief — S446_AMIR_STAGES_BILLS (what S444 did not carry: Amir's count work in the decided order — orthotic vouchers, verified, renames, verified, then medicine vouchers a few per visit; his monthly packs; the scanned medicine bills as files for Marg's own digital entry, Marg overruling Sarvam; the text reader learns Marg's `***`; and the doors the duty map found missing)

Written 02-Oct-2026 by the Sanjeevni chat (S283 close). Read `CLAUDE.md` first. **Kit S446 · decisions D649, D650 (claimed for S444, not built there) · faults F-673, F-674, F-679, F-680** (System Board `_numbers` v144). Runs AFTER S444_STAFF_SAFE (live 01-Oct 22:08 IST) and builds ON its files — read every FROM pin live. S438_COUNT_BOOK stays HELD. Staff pages Hindi (Roman), owner pages English.

**Why this brief exists (F-679).** The S444 brief on the PC was an earlier text than the one the owner approved in chat: the chat's last save did not carry the final sections. S444 built everything in the text it was given, correctly. This brief is the remainder, nothing else. `REPORT_S444.md` is the starting state — read it first.

**Touches (declared):** `/root/finance/amir_day.py`, `stock_app.py`, `sanjeevni_approvals.py`, `purchase_app.py`, `darpan_kal.py` (+ its page) — Sanjeevni's; the medical PC's `marg_txt.py` and `marg_watch.py` (Sanjeevni's, delivered by the Drive kit channel); `claude_code_briefs/DUTY_MAP.md` + `.json`. **READ ONLY:** `packs.py` (the parent's — `amir_pack()` per month), `supplier_msg.py`, the asset app's store (through `purchase_app`'s existing read-only door). Restarts `clinic-finance` only.

## 1 · The owner's words (01-Oct, evening)

"The decided flow was that Amir first does the orthotic stock issue and receive vouchers; you cross-check and verify the uploaded report; after that you give him the orthotic renaming list; then he renames. That completes the orthotics neatly. When that is complete and verified, we move on to the remaining stock vouchers. All should come in the same Amir ka kaam app — that boy is in a tearing hurry."

"He should be able to see his monthly pack of August — I could not find it for him."

"The scanned medicine bills are simply made available to him at one place so he can upload them in the digital entry part of Marg, which processes them with its own engine. That will be the final entry of the bill, and our system verifies Sarvam's transcription against what Amir entered in Marg; for the coming two months Marg overrules Sarvam."

## 2 · The state S444 left (REPORT_S444 — re-read live and REPORT the same facts first)

- **The card.** Every step of Amir's day shows "Stock voucher baaki: 7 orthotic, 30 dawa — kholiye"; one tap opens his stock board with ALL 37 vouchers (28 ISSUE + 9 RECEIVE; orthotic 4 ISSUE + 3 RECEIVE, 30 lines). "Naam badlo: 22 naam" appears only after EVERY voucher is entered and the whole proof is green. So today nothing stops him starting on medicine vouchers, and the orthotic renames wait on all 37.
- **F-673 — the August pack.** `packs.amir_card()` shows only the previous calendar month and only when ready, at the foot of every step. On 01-Oct "previous month" became September (not ready), so August's pack (ready 28-Sep) disappeared. S444 did not touch it.
- **F-674 — the refused sale text.** 30-Sep 22:10 the bill-wise sale text was refused by `marg_txt` at line 52 — `4 *** FINGER EXTENSION SPL 1*1  1  180.00`, bill A003920: Marg prints `***` in the item's number column. The file is whole (24 bills, GRAND TOTAL Rs 23,598) and kept in `FromMedical\refused_text\`. S444's "Report refused today" line reads only what the SERVER refused (`mi_file`); a refusal on the medical PC still reaches nobody.
- **The scans are read by Sarvam Document AI** (the shared helper under `/root/shared`, A-D16); our code only matches its reading to Marg. Amir has no place to get the scan files.
- **F-680 — lists chosen by the current month hide older open work.** `sanjeevni_approvals._returns_pending` counts the current month only: 7 counter returns of 03–19 Aug wait for the owner and never show. Shavez's Vendor payments tile opens the current month's page; 18 supplier messages queued since 26-Sep sit only on August's.
- **The duty map's Sanjeevni no-door duties** (REPORT_S444, findings 1–5, 8, 9).

## 3 · The build

### 3.1 The count as gated stages (D649) — `amir_day.py`, `stock_app.py`

Nothing of a later stage is shown to Amir before the earlier one is verified. The owner and the checkers see everything, as today.

- **Stage A — orthotic vouchers.**
  - The card reads "Orthotic voucher baaki: N — kholiye" and nothing about medicine.
  - For the amir login the board lists only the orthotic vouchers (ISSUE first, then RECEIVE, numbered 1 … 7).
  - When all are marked entered, the card says **"Ab closing stock export kijiye"**.
  - A closing-stock export received AFTER the last mark runs the existing proof (`proof_state`, S231/S404) over the orthotic lines only.
  - The card then shows **"Orthotic: sab sahi ✓"**, or names each item still wrong: item, Marg, shelf expected, and the voucher number to correct.
- **Stage B — the 22 orthotic renames** (S437's list, D620's memory).
  - Shown only when Stage A is verified. S444's "Naam badlo" block moves here: it no longer waits on the medicine vouchers.
  - He renames in Marg and ticks each. The next closing-stock or item-list export is checked: every new name seen, every old name gone. Those still old are named.
  - When B is verified: one Needs-you line, once — **"Orthotics verified and renamed — live orthotic ordering can start"**. The card shows "Orthotic poora ✓" for that visit.
- **Stage C — medicine and consumable vouchers** (30).
  - Released only after B is verified.
  - **5 per visit** (setting `amir.vouchers_per_visit`, default 5), oldest round first. The card reads "Dawa voucher: aaj ke 5 (baaki 25) — kholiye".
  - Each batch is verified on the next closing-stock export, the same way as Stage A, over that batch's lines.
  - The next 5 are released when the batch is verified, or after 2 of his visits. An unverified batch stays listed with its wrong items named.
- **It never blocks "Din band".** S444's line (d) — vouchers not touched in 2 visits — now names the stage.
- **A stage is verified by the server's own proof, never by a tap.** The owner's approvals page gets one small line of where the count stands: "Count #1: Stage A 3/7 entered" and so on.

### 3.2 Monthly packs chosen by state (F-673) — `amir_day.py`; `packs.py` READ ONLY

- Inside the same card: every month of the last 3 whose pack is ready and not yet "dekh liya", oldest first — **August now**. Read through `packs.amir_pack(con, month)`; the pack's own page and its "dekh liya" stay as they are.
- The foot-of-page card (`packs.amir_card()` call in `amir_day`) is removed.

### 3.3 Scanned medicine bills as files; Marg overrules Sarvam (D650) — `amir_day.py`, `purchase_app.py`

- **Step 2 (Bill entry) gets one list: "Marg mein daalne ke bill (N)".**
  - Every captured pharmacy scan not yet linked to a Marg bill, oldest first: the stamp, supplier as scanned, date.
  - **Download** gives the stored scan file, read-only from the asset app's store through `purchase_app`'s existing door, named `<SUPPLIER>_<billno>_<dd-mm-yyyy>.pdf`.
  - **"Aaj ke sab"** gives one zip of today's.
  - Amir and the owner only (server-enforced).
  - A bill leaves the list by itself when his export links it (S439's re-match).
- **No Sarvam reading is shown to Amir.** Marg's entry is the bill's final record.
- **The trial** (setting `purchase.sarvam_trial_until` = install date + 2 months).
  - For every scan linked to a Marg bill, store field-by-field agreement: supplier (alias-aware), bill number (digit tail), date, total (within Rs 1), and item lines where Sarvam read items (name similarity, qty, rate, batch, expiry) against Marg's item-wise purchase lines.
  - **Wherever they differ, Marg's figure is used.** Nothing downstream reads a Sarvam value for a bill Marg has. S444's "Kaagaz (scan)" amount on Amir's bill line stays, as a prompt to him only.
  - Owner: one line on the Scan links page, and a monthly Needs-you summary with a drill-down: "September: N bills · Sarvam agreed fully on N · supplier wrong N · total wrong N · items wrong N".

### 3.4 The text reader learns `***`; a PC refusal reaches the owner (F-674) — medical `marg_txt.py`, `marg_watch.py`

- An item line whose number column prints `***` is read with that column empty. Every other check (bill sums, GRAND TOTAL) stays.
- **Proof before delivery:** the refused 30-Sep file converts — 24 bills, GRAND TOTAL Rs 23,598 — and the earlier parity files still pass.
- Delivered as S397 was (`ToMedical\_kit`, md5-gated, the agent confirms). The watcher then re-examines the refused file, so 30-Sep's sale arrives without a re-export. If the owner's Excel re-export is already in, the server keeps one copy.
- **The refusal note travels.** `marg_watch` sends its refused-text note to the server by the route its exports already use (no new door, no new secret). S444's "Report refused today" line then names it: report, time, line, reason. If the existing route cannot carry a note without a new door, REPORT that and deliver the reader fix alone.

### 3.5 The doors the duty map found missing, and lists by state (D648, F-680)

- **Amir's card also carries**, each only while due, each opening the place on his board: pick the Sunday for the full count · key the bill for goods tapped as arrived · fix lines from the stock traces (28 open).
- **Darpan sees Amir's supplier claims** on Kal ka hisaab: supplier, bill, amount, raised when, and his existing answer taps. Nothing new for him to type.
- **Shavez's Vendor payments** shows "Pichhle mahine ka baaki: N" above the month whenever an earlier month holds unsent messages or unpaid lines; one tap opens that month.
- **`_returns_pending` counts every open month**, oldest named: "Counter returns waiting for your OK: 7 (oldest 03-Aug)".
- **The 18 supplier messages not leaving the reception phone since 26-Sep: REPORT only.** Read the queue door's own log: is the phone fetching at all, and what does it get? Fix only if the fault is on the server. Otherwise say in one owner line what must be done on the phone.
- **Spine tasks (48, no page, no person):** not in this kit — REPORT their kinds and ages only.
- `DUTY_MAP.md` / `.json` updated for every duty this kit adds or moves.

## 4 · Pins — S444's TO, read live

| file | pin |
|---|---|
| `amir_day.py` | `2b497142` |
| `stock_app.py` | `c0120fb6` |
| `sanjeevni_approvals.py` | `d2c55040` |
| `purchase_app.py` | `a51fe90e` |
| `darpan_kal.py` | `803970bd` (+ its page `a4eecb21`) |
| `packs.py` (READ ONLY) | `6a1cf6ce` |
| medical `marg_txt.py` | `38d85298` |
| medical `marg_watch.py` | `81145aa7` |

Not touched: `porders.py` `3620b374`, `portal.py`, `clinic_sso.py`, `tile_grants.json`, the crontab.

## 5 · Walk (scratch copies; rows keyed W446*; dates from today)

- **Stages.**
  - With the live count's 37 vouchers open, every step shows ONLY Stage A; the amir board lists 7; no rename and no medicine voucher is visible anywhere for amir; the owner's board still lists 37.
  - All 7 marked: "Ab closing stock export kijiye".
  - A crafted export with one orthotic item wrong: that item named with its figures; Stage B not shown.
  - A crafted clean export: "Orthotic: sab sahi ✓" and the 22 renames; still no medicine voucher.
  - A crafted export with the new names: the Needs-you line once, and Stage C's first 5.
  - A verified batch releases the next 5; an unverified one releases them after 2 crafted visits.
  - Din band offered throughout.
- **Packs.** August shows in the card until "dekh liya"; September appears when crafted ready; the foot card is gone.
- **Bills as files.** The list equals the unlinked captured scans; a download carries the new name and the stored bytes (md5 equal); the zip holds today's; another staff login gets 403; a crafted linked scan writes its comparison row; Marg's total is the one every page uses; the owner's summary counts add up.
- **`***`.** The 30-Sep file converts to 24 bills and Rs 23,598; a crafted line with `***` in another column still refuses; the refusal note reaches the Needs-you line.
- **Doors.** Each new card line shows only while due; Darpan's page lists a crafted claim; Shavez's page shows the earlier month's count; the returns line counts August.
- **Staff-eye walk** (CLAUDE.md, "Every duty has a door") for amir, darpan, shavez and the owner.
- **Earlier walks re-run green:** S444 60/60 with each adjustment named (the card's text; the renames' gate); S437's and S436's on the board.
- **Negative control** on the box as it is.

## 6 · Done means

Kit `deploy_kits\S446_AMIR_STAGES_BILLS\` · installed · published · `claude_code_briefs\REPORT_S446.md`, owner lines first:

- Amir's card as he will see it tomorrow: Stage A only, the August pack, the bills to put in Marg.
- Where the 30-Sep sale stands.
- The Sarvam comparison as it stands today.
- The 18 supplier messages: why, and whose step.

Ending with:

```
https://followup.dr-manoj.in/finance/amir/day
```

```
https://followup.dr-manoj.in/finance/approvals
```
