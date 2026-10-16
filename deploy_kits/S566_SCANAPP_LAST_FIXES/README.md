# S566_SCANAPP_LAST_FIXES — the scan app's last fixes after S563 (D646 PLANNED line, board v442)

**Why.** Two notes of S563's independent kit review (`S563_KIT_REVIEW_K1.md` N5, N6) and six things a read-only live check as
the owner found at 05:2x IST 16-Oct-2026. The brief: `claude_code_briefs/S566_SCANAPP_LAST_FIXES.md` (v2, with the independent
read `S566_BRIEF_R1.md` taken in — its replacement wording governs). The owner, 05:20 IST 16-Oct: *"check the scanner and then
find whatever needs to be done, then include these two small follow-ups ... use the Claude API credits"*. **No new feature, no
new page, no new switch, no new column, no data step. Reception's screens unchanged; `scanner_widget.js` unchanged.**

**What changes (owner / manager pages only).**
1. **N5 — a restored paper never counts twice blind.** The one restore (`_s563_restore`: F-902's Restore and the blank fix)
   keeps its status rule (clinic → draft; the other lanes → captured — never *draft* off the clinic lane) and, on EVERY lane,
   first looks for the live paper it would be a second count of: (a) `AR._dup_by_triple` (exact) on the row; (b) when the row
   has no supplier or no amount, the same exact triple from Claude's reading; (c) the same capture again (`AR._dup_by_fp`, fine
   distance ≤ `AR.DUP_EXACT`). A match refuses — *"This looks like B-xxxx — open it instead."* — nothing written. Otherwise the
   restore runs as before and the paper waits on the desk with the reason `restored` (*"restored — sort it"*) until its next
   desk Save (`_marks` now reads `desk_restored` / `desk_blank_restored`). The blank fix's route now returns that refusal as a
   plain 400 line, not as a failure.
2. **N6 — the old challan doors check on the server.** `clinic_papers._s566_door`, called first in `challan_close`,
   `challan_delete`, the join page's POST (the head, every page, the typed paper) and `unjoin` (the head): a challan with
   `subgroup='patient_paper'` is refused for anyone; a paper with `subgroup='personal'` for anyone but the owner — one plain line,
   nothing written. The old pages' warranty and Dr MK / Dr Bhawna POSTs (`set_warranty`, `set_pe_who`) call the same helper
   (R1 note 18 as the brief binds it; `set_pe_who`'s own 403 for a Personal paper stays in front of it).
3. **No paper waits where nobody sees it (B-0009).** `sorting_desk.waiting` gains the reason `waiting` (*"not accepted yet —
   check"*; a challan with no supplier read: *"challan — supplier not read"*) for a draft that no other list shows — not a double
   scan, not a page, not pharmacy, not a patient's paper, Personal only for the owner — whatever its scan day and earlier desk
   saves; except an awaiting challan whose supplier is read (Bills awaited lists it) and a Clinic-equipment draft for anyone but
   the owner (it waits on his Save). The menu's and the home card's desk counts are `len(waiting())` and follow. Nothing written.
4. **Bills awaited: the count = the rows.** `sorting_desk.awaited_open(db, owner)` is the page's own list of open challans; the
   page no longer drops a challan whose supplier is not read (its own card *"Supplier not read"*, each row to the desk, no
   how-they-bill buttons); the menu's count is `len(awaited_open(...))`. Paid-on-challan (final) rows show as before, not counted.
5. **A date is never stored half-read.** At the four `bill_date` writers only: the reading's fill (`_bg_extract`) leaves a date
   it cannot read in full empty (the pharmacy lane's fill unchanged byte for byte); the old edit and new-bill pages refuse it
   with one line, nothing saved; the intake's prefill leaves it empty (pharmacy as before). `_norm_date`, item expiry and
   `normalise_dates` unchanged. `CP.MONTH_OF` takes the bill date's month only when it is shaped yyyy-mm-dd (else the scan month,
   as for an empty date). A stored non-ISO date shows as written with *"date looks misread — check"* on the old bill page (the
   desk's own flag as before). The old bill page prints *"approved by …"* only for an approved paper; *"rejected by …"* as before.
6. **Home's Spend this month = The month.** `sorting_desk.month_total(db, ym, owner)` = the sum of The month's section totals
   (`month_data`'s two money queries factored into `_s566_paid_rows`, one sum `_s566_total`, no items loop). The home card reads
   it for the desk's today; the old query only when the desk is not mounted.
7. **"None" is never shown as a contract.** The Machines list's Contract cell and the machine page's *Contract:* line show a
   blank for the stored word "None" or an empty value (`|s566_contract`, the test of `asset_machine._old_record`). Stored values
   and the edit form unchanged.
8. **`/desk?open=` takes the stamp in any common form** — B-0162, b-0162, B-162, B162, b162. A bare number stays the record id
   (every link the app makes carries it). An unknown value: *"No paper <typed>"*; a refused one: `_visible`'s reason.

**Fix round 1 (16-Oct-2026, brief `S566_FIX1.md`, after the independent kit review `S566_KIT_REVIEW_K1.md`).**
- **A held double is never money twice (K1 BLOCKER 1).** `_s566_paid_rows` — the one selection The month and the home card both
  read — leaves out a D710-held double (`_S566_NOT_HELD`, the SQL twin of `held()`) in both its money and its finals query. The
  copy drops out of The month and home until it is answered on the desk; the accepted original counts once.
- **A closed challan does not wait for ever (K1 CORRECTION 2).** A desk Save of a challan already closed on the old page writes a
  `desk_closed_kept` audit row and says *"B-xxxx is a closed challan — kept as a record; no bill will come."* (never "Bills
  awaited"); `_marks` reads that row and `_s566_waits` then leaves the challan out of Waiting.
- **The old edit page does not refuse an untouched stored date (K1 CORRECTION 3).** `bill_edit` refuses a date that is not a full
  yyyy-mm-dd only when the submitted value differs from the stored one (as the desk's `typed_date`); `_norm_date` writes an
  untouched value back unchanged. B-0163 and a pharmacy scan with an old partial date can be edited again.

**Files and pins (FROM → TO).** `/root/assetapp/sorting_desk.py` `062ac43c` → `a053a222` (20 counted edits) ·
`clinic_papers.py` `9a59f977` → `024464cc` (9; unchanged by fix round 1) · `asset_register.py` `0828fbc3` → `8b3c4551` (11).
(Round 0, superseded, never installed: `255a27ed` / `024464cc` / `19ebade7`.) Read only, pinned:
`asset_machine.py` `7d4fdffc`, `scanner_widget.js` `10a8bb29`, `claude_reader.py` `3894dc23`, `claude_reread.py` `d9b75e78`,
the parent's `/root/finance/packs.py` `048d2ad8`. Every edit is an anchor found exactly once in the live bytes (`make_s566.py`).
Restarts **assetapp** only (`clinic-finance` is not touched).

**Kit.** `make_s566.py` (the patcher; `--cp-on` rebuilds S563's tidy comparison) · `walk_s566.py` (I1–I8, I6b, W1, W2, Z1; the
control with `--expect-red` on the FROM files; `--expect-red-r0` on round 0's TO files: I3, I5, I6b must be red) · `lines_s566.py` (the earlier walks' lines S566 changes, written to /tmp copies only: S563 F4, S559 O3 / O4)
· `install_s566.sh` · `rehearse_s566.sh` · `walk/` (the PC's headless-Chrome S560 desk-layout walk results) · `PIN_*.txt` ·
`KIT_ID.txt` · `SUMS.md5`.

**Proof, fix round 1 (16-Oct-2026, 06:25–06:28 IST by the box's clock, on the box in /tmp only).** S566's walk **12/12** green on
the FIX1 TO files; the control on the FROM files **10 of 10 MUST_RED red**; the control on round 0's TO files (`--expect-red-r0`)
**I3, I5, I6b red** (I6b: The month rose by ₹1,000 there, by ₹500 now). Inside the rehearsal: S563 17/17 with its tidy fetch
(102 answers, none differing), S560 37/37, pack 9/9, S548 8/8, S559 43/43, S557 41/41, S555 19/19, S551 87/87; all seven outcomes
as before. **Round 0 (below)** is kept for the record.

**Proof, round 0 (16-Oct-2026, on the box in /tmp only, and in headless Chrome on the PC).** S566's walk 11/11 green on the TO files; the
control 9 of 9 MUST_RED red on the live files. S563 17/17 with its tidy fetch (102 answers, none differing), S560 37/37, S560
pack 9/9, S548 8/8, S559 43/43, S557 41/41, S555 19/19, S551 87/87. The rehearsal on a made-up root: green, ALREADY INSTALLED,
forced red restored, /desk 404 restored, /desk 200 restored, a moved file and a moved read-only file refused before placing.
Browser: S560's desk layout 7/7 on the new desk.

**Install (the owner, after publishing):** `bash /root/deploy/repo/deploy_kits/S566_SCANAPP_LAST_FIXES/install_s566.sh`
(`DRY=1` in front stops before placing.)

**UNDO (one line):** `\cp -p /root/assetapp/sorting_desk.py.bak_S566_062ac43c /root/assetapp/sorting_desk.py && \cp -p /root/assetapp/clinic_papers.py.bak_S566_9a59f977 /root/assetapp/clinic_papers.py && \cp -p /root/assetapp/asset_register.py.bak_S566_0828fbc3 /root/assetapp/asset_register.py && systemctl restart assetapp`
— then `/healthz` 200 and the three md5s back at the FROM pins. No data step ran, so the database backup
`assets.db.bak_S566_<stamp>` is never needed for an undo.
