# REPORT S560_RECEIPTS_STATEMENTS — receipts, statements, one payment record, the desk on one screen (built, walked, rehearsed; NOT installed, NOT published)

## Fix round 2 (15-Oct-2026, brief `S560_FIX2.md`) — rebuilt, re-walked, re-rehearsed; NOT installed, NOT published

**For Dr Manoj (plain English):**
- **A paper saved as a Receipt by mistake can now be changed back to a Bill safely.** When you do, the payment it recorded is cancelled
  (kept on record), and the bill it had marked paid shows unpaid again.
- The paper is then accepted as a normal bill, so it counts in the clinic's money once. Before this fix it counted nowhere.
- The same applies to a Statement changed to any other kind. Every earlier check still passes on a copy of your data.
  The new check fails on the kit as it was, so it really tests the fix. **Nothing is installed yet.**

### For the chat — the proof

**Run (IST, box clock).**
- FROM pins read on the box at **12:01:44**: `sorting_desk a59fa38d`, `asset_register 20ef7bc6`, `clinic_papers 80e3cd8d`, `asset_machine 0caec41e`,
  `scanner_widget 1128ac97`, `claude_reader 3894dc23`, `claude_reread d9b75e78`, `packs d86d351a`, pre-S559 widget `1143c77b`. All equal the kit.
  Lock absent, 0 `bak_S560` files, both services active, the live database has no `paper_payment` table and no `to_accountant` column.
- Walks and controls ran **12:02:51 → 12:03:01**. The rehearsal ran **12:03:09 → 12:06:02** (exit 0; "made-up root removed" confirmed).
- **After (12:06:20):** all nine live files at the same FROM bytes, lock absent, 0 `bak_S560` files, the live database unchanged in shape,
  `/finance/healthz` 200. No service was restarted and no live file was written.

**Pins — FROM → TO (built on the PC and rebuilt on the box: equal).**

| file | FROM | TO after fix round 1 (superseded) | **TO now** |
|---|---|---|---|
| `/root/assetapp/sorting_desk.py` | `a59fa38d7c7f145c8fefa52bad5676d1` | `b5993236…` | **`a4623438f068d8e691b797482bd942ab`** |
| `/root/assetapp/clinic_papers.py` | `80e3cd8d2ef8e8953b2ae3fec3f85203` | — | `88963eacee217e051ae07091648a46d7` (unchanged) |
| `/root/assetapp/asset_register.py` | `20ef7bc6b44079f3181d9c52519e8b94` | — | `9daed9ea4f2a87e40b43711e472e701f` (unchanged) |
| `/root/finance/packs.py` (THE PARENT'S) | `d86d351a46a1ba4da7d0e615da0deb1a` | — | `048d2ad81abb0271a1cddd31134544bb` (unchanged) |

Counted edits are unchanged (52 / 6 / 4 / 5). Every anchor was found exactly once, on the PC and on the box. The new code is in
`s560_sd_block.txt`, which goes in whole, so the edit count does not move. The built files compile on `/usr/bin/python3` and
`/root/wa/venv/bin/python3`. The round-1 kit (kept in `_scratch\S560_FIX2\kit_before\`) still builds `b5993236` from the same live bytes.
The second control ran on that build.

**What changed (C4, `s560_sd_block.txt` only).**
- **`_s560_pre`:** if the paper's stored kind is receipt / statement and the Save's kind is bill / estimate / challan, its own live
  payment is noted (`s["unproof"]`). If it is Filed (`captured`) on the clinic lane, it goes back to `draft`, audited
  `desk_not_spend_undone` (kind_from, kind, status_from, status). `save()` re-reads the row before its accept step, so the normal accept
  runs, with its duplicate check. A later refusal rolls the whole Save back.
- **`_s560_post`, first thing:** that payment is voided by the existing `_s560_void_own` (audited `payment_voided` on the paper and the
  bill it paid, plus `paper_payment_void` in the desk's book). Its live allocation rows are then voided by the new `_s560_void_allocs`
  (`voided_at` / `voided_by`, the same `#n` rule as round 1). The message adds *"Its payment as a receipt is voided (kept on record) —
  the bill it paid is unpaid again."*
- The block header has one FIX2 line. Nothing else in the kit's code changed: `s560_js.txt`, `s560_ar_block.txt`, `make_s560.py`,
  `install_s560.sh` and `rehearse_s560.sh` are byte-identical to round 1.

**The walk** (`walk_s560.py`, on the box, isolated as before; 1 new check, R6, also added to MUST_RED):
- **Walk on the new files: `37 checks: 37 GREEN, 0 RED`.**
- `LIVE-STAMPS … B-0140 receipt . B-0139 receipt . B-0137 blank . B-0104 statement`; `SIZES desk 36521 B (50 ms) . list 1313 B (28 ms)`.
- **Control on the live (S559) files: `37 checks: 3 GREEN, 34 RED`**. `CONTROL must-be-red: … N2, R6 -- all RED`.
- **Control on the S560 kit after fix round 1** (`--must-red R6`): `37 checks: 36 GREEN, 1 RED (R6)` — `all RED`. What the old build did
  (made-up rows): the re-save as Bill answered `'Z-2031-RRX2 → Others.'` with status `captured`. The old bill still read `paid`, and the
  payment stayed live. This is the review's gap, exactly.

| New check | What it proves (made-up rows) |
|---|---|
| **R6** | A clinic-lane receipt pays made-up bill RX1 (₹600): RX1 *Paid*, the receipt *captured*. Re-saved as a Bill into Others: 200. The paper is `doc_kind='bill'`, **approved**, and in the month's Others `money_ids` (the clinic total), beside RX1. RX1 reads **unpaid**. The one payment row is kept with `voided_at` set, and its one allocation row is kept with `voided_at` set (nothing deleted; RX1 has no live allocation). `desk_not_spend_undone` and `payment_voided` are audited on the paper, and `payment_voided` on RX1. The message says "voided (kept on record)". |

**The pack walk** (packs.py unchanged): `9 pack checks: 9 GREEN, 0 RED` (venv python: the same). Before / after is identical to round 1
(`2031-09 owner_expense before C2,E1,E2 after E1`; `C2-LANES {'owner_expense': ['construction_accountant'], 'lab_purchase': ['construction_accountant']}`).
**Pack control, live packs.py:** `9 pack checks: 2 GREEN, 7 RED`, `CONTROL must-be-red: P2, P3, P5, P6, P7, P8, C2 -- all RED`.
S548 on the new packs.py: `8 checks, 8 green, 0 red`.

**The earlier walks on the new files** (inside the rehearsal's installer): S559 `43 checks: 43 GREEN, 0 RED` · S557 `41 checks: 41 GREEN,
0 RED` · S555 `19 checks: 19 GREEN, 0 RED` · S551 (S559's three agreed lines) `87 checks: 87 GREEN, 0 RED` · S548 `8 checks, 8 green, 0 red`.

**The rehearsal** (`rehearse_s560.sh`, made-up root, both services faked) — **`REHEARSAL GREEN`**, six outcomes:

| Outcome | Result |
|---|---|
| 1 | DONE. Rebuilt = `a4623438 88963eac 9daed9ea 048d2ad8`; every walk and control above inside it; the database backed up before the data step; the lock released; "packs.py loaded (no 'packs NOT mounted' …)". |
| 2 | ALREADY INSTALLED. |
| 3 | Forced red → restored to `a59fa38d 80e3cd8d 20ef7bc6 d86d351a`, both health answers 200. |
| 4 | `/desk` 404 → restored. |
| 5 | `/desk` 200 → restored (302 only). |
| 6 | `/finance/healthz` 200 but the made-up journal says `packs NOT mounted` → restored. |

**The kit.**
- 26 files + `SUMS.md5`, all LF, no BOM, no `__pycache__`.
- **Byte-identical to what ran:** the box's md5 of its 26 kit files equals the repository copy for 24. The 2 that differ are `README.md`
  and `KIT_ID.txt`, re-written after the run; neither is executed.
- Changed this round: `s560_sd_block.txt`, `walk_s560.py`, `PIN_TO_sorting_desk.txt`, `README.md`, `KIT_ID.txt`, `SUMS.md5`.
  `walk/walk_results_s560.txt` (the browser walk) is unchanged.

**Calls I made (the brief left room), each with its reason.**
1. **The trigger is `kind in ('bill','estimate','challan')`, not the review's `k not in NOT_SPEND`.** A Save that sends no kind leaves
   the stored kind as it is (`_doc_kind` ignores it). With the review's line, such a Save would have voided the payment of a paper that
   is still a receipt.
2. **The allocation rows are voided too.** The brief says "(and that payment's allocations)". The review's code voided only the
   payment row. Every read already ignores a voided payment's allocations, so the totals are the same either way. The rows now also say
   so themselves.
3. **The message's "the bill it paid is unpaid again"** is added only when the payment paid a bill. A "No bill — paid directly"
   receipt just says its payment is voided.
4. **Only the clinic lane goes back to draft**, as the brief says. On another lane, `captured` is that lane's own normal status. There
   the payment is still voided, and nothing else changes.
5. **Not re-run, because nothing they test changed:** the browser walk (no layout or script change) and the pack control on the
   round-1 kit (packs.py is byte-identical, `048d2ad8`).

**Review notes — seen, not changed:**
- **N13:** `record_payment`'s docstring still says "append-only".
- **N14:** the journal check is fail-open if `journalctl` errors.
- **N15:** the round-1 scratch `/tmp/s560fix1a`, `/tmp/s560fix1b` and `/tmp/s560fix1probe` is still on the box.
- **N16:** two *Paid?* rules. A part-paid bill takes a further direct *Paid?* as an instalment, capped at what it still owes. A fully
  paid bill offers "Paid on … — change?", which edits its one direct payment.
- The round-1 notes N2–N12 stand as listed below.

**Not done, and seen outside the brief.**
- **Not installed, not published, no build lock taken** (nothing was placed; the lock is taken only inside `install_s560.sh`).
  `asset_machine.py`, `scanner_widget.js` and the DUTY_MAP were not touched; no staff duty changes.
- **Scratch left behind:**
  - On the box: `/tmp/s560fix2a` (kit copies and logs) and `/tmp/s560fix2_pins.sh`. No copy of live data is left: the walk's `snap.db`
    was removed by its script, 0 `.db` files and 0 new `.json` files remain, and the rehearsal removed its own root. Remove them with
    N15's folders at the install session.
  - On the PC: the permission list refused my recursive delete of `_scratch\S560_FIX2\built2\__pycache__` (from a local compile check).
    I did not respell it. It sits in the git-ignored scratch, outside the kit.

**Cost of fix round 2:** about **US$2** of API credit, read from this session's budget meter when this section was written.

**Gates (fix round 2)** — see the lines directly below. They were run after this section's words were written, over the 26 kit files +
`SUMS.md5`, this report and both fix briefs.

- `SUMS.md5`: 26 lines, 0 mismatches.
- `.gitignore` (last match wins): `git check-ignore -v --non-matching --stdin` over the 30 files gives 30 lines, **0 ignored** (GitHub
  Desktop's git, read only).
- Contact-number gate, as PUBLISH_ALL runs it: `NO_PHONE_NUMBERS: clean -- 30 staged file(s) checked (numbers and credentials).`
  It was run again on this report's final bytes, with the same result.
- No `__pycache__` in the kit or the briefs folder.

**Nothing installed, nothing published.**

---

## Fix round 1 (15-Oct-2026, brief `S560_FIX1.md`) — rebuilt, re-walked, re-rehearsed; NOT installed, NOT published

**For Dr Manoj (plain English):**
- **A payment is now recorded only once.** Saving a receipt or a statement a second time (for example, to correct its date) now
  corrects the payment already there. It never adds a second one. On a bill that is already paid, *Paid?* now reads *"Paid on
  dd-mm-yyyy — change?"* and corrects that payment.
- **No bill gets more money marked against it than it owes.** If a receipt is for more than the bill still owes, only what is owed is
  marked on the bill, and the message says how much was left over.
- **A construction bill you tick for the accountant goes into the pack once**, in its own line (8.4). It no longer also appears in
  the lab or expense line.
- **A receipt or a statement can no longer be approved as spend** from the old bill page.
- On a real laptop screen (1366 × 620), every place a paper can go, the five paper kinds and Save show without scrolling.
  Every check passes on a copy of your data, and the new checks fail on the kit as it was. **Nothing is installed yet.**

### For the chat — the proof

**Run (IST; box clock unless marked).**
- FROM pins read on the box at **10:39:42**. All eight equal the brief and the nightly bundle's pins the review confirmed:
  `sorting_desk a59fa38d`, `asset_register 20ef7bc6`, `clinic_papers 80e3cd8d`, `asset_machine 0caec41e`, `scanner_widget
  1128ac97`, `claude_reader 3894dc23`, `claude_reread d9b75e78`, `packs d86d351a`. The pre-S559 widget backup is `1143c77b`.
- The build lock was absent at 10:39. **No lock was taken**, because nothing was placed; the lock is taken only inside
  `install_s560.sh`. There were 0 `bak_S560` files on the box.
- The walks and controls ran **10:48:47 → 10:48:56**. Rehearsal (kept root, for inspection) ran 10:50:56 → 10:53:28. **The final
  rehearsal ran 10:53:53 → 10:56:25**: it removes its made-up root, and "made-up root removed" was confirmed.
- The browser walk ended **10:56:59** (PC clock).
- Both live services were active at the start. The live files were only read; no service was restarted.
- **After (10:59:53):** all ten live files read back at their FROM bytes, the lock is absent, and there are 0 `bak_S560` files.

**Pins — FROM (live = brief) → TO (built on the PC and rebuilt on the box: equal).**

| file | FROM | TO before fix round 1 (superseded) | **TO now** |
|---|---|---|---|
| `/root/assetapp/sorting_desk.py` | `a59fa38d7c7f145c8fefa52bad5676d1` | `5017fe92…` | **`b5993236927baa6872ad719116b0a86d`** |
| `/root/assetapp/clinic_papers.py` | `80e3cd8d2ef8e8953b2ae3fec3f85203` | `88963eac…` | **`88963eacee217e051ae07091648a46d7`** (unchanged) |
| `/root/assetapp/asset_register.py` | `20ef7bc6b44079f3181d9c52519e8b94` | `5c8b3097…` | **`9daed9ea4f2a87e40b43711e472e701f`** |
| `/root/finance/packs.py` (THE PARENT'S) | `d86d351a46a1ba4da7d0e615da0deb1a` | `f8d9a8f4…` | **`048d2ad81abb0271a1cddd31134544bb`** |

The built files compile on `/usr/bin/python3` and on `/root/wa/venv/bin/python3`. Counted edits: sorting_desk 52 (the same anchors;
the DDL edit carries the new table), clinic_papers 6, asset_register **4** (AR4 new), packs 5 (PK1 carries C1). Every anchor was found
exactly once, on the PC and on the box. The old kit's `make_s560.py`, run on the same live bytes, still reproduces the superseded pins
(`5017fe92 88963eac 5c8b3097 f8d9a8f4`). That build is what the second control ran on.

**What changed, each item of the brief.**

**B1 — a payment is recorded once** (`s560_sd_block.txt`, `s560_js.txt`, the DDL in SD4).
- `_s560_pre` finds the paper's own live payment (`proof_bill_id` + `proof_created_at`). `_s560_post` then **updates** that payment
  (`_s560_update_payment`) instead of calling `record_payment`:
  - date / amount / mode / ref are updated in place;
  - the old and new values go into `payment_changed` on every paper touched, and into `desk_audit`;
  - when the bills or their amounts change, the old `paper_payment_bill` rows get `voided_at` / `voided_by` (kept), and the new
    rows are written;
  - an identical re-save writes nothing.
- A receipt re-saved as *the receipt of a statement* voids its own payment. Its link audit is written only when the link changes.
- `_s560_payable` keeps offering the bills the paper's own payment already pays, owing what they owed before it. So the re-opened
  receipt shows its bill ticked (`cur`), and the statement shows its invoices ticked.
- The payment boxes are pre-filled from the recorded payment, and the period and total from the last `desk_statement`. The box
  shows *"Recorded: … — saving again changes this payment, never adds a second."*
- ***Paid?* on a fully paid bill:**
  - The fold reads *"Paid on dd-mm-yyyy — change?"* and is pre-filled when the bill is paid by ONE direct payment. Save edits that
    payment. The desk sends the boxes only if the person touched them.
  - A bill paid by a receipt or statement is refused with *"… is already paid. It is paid by Z-… — to change the payment, open that
    receipt. Nothing was saved."* A bill noted as paid on the paper, or paid by several payments, gets the same kind of one-line refusal.
- **Caps:** a receipt's and a *Paid?* allocation is `min(amount, what the bill still owes leaving out this payment)`; the rest is named
  in the message. The statement's per-invoice cap now also leaves out its own payment.
- **The table:** `paper_payment_bill` gains `voided_at TEXT NOT NULL DEFAULT ''` and `voided_by`. Its key becomes `PRIMARY
  KEY(payment_id, bill_id, voided_at)`: one live row per bill per payment, and voided rows kept. Every read of the allocations
  (`_s560_live_allocs`, `paid_state`, `paid_map`, `pay_void`) now takes live rows only.

**C1 — a construction bill goes into the pack once** (packs.py, inside `build_bundle`, PK1).
- Every bundle except `construction_accountant` adds `AND NOT (subgroup='construction' AND kind bill AND to_accountant=1)`. That is
  exactly 8.4's own selection, guarded on the three columns existing.
- An unticked construction paper stays where it is today. **packs.py's TO pin is now `048d2ad8…`.**

**C2 — a real check that the pack loaded** (`install_s560.sh`).
- The wording was read in the live `finance_app.py` (md5 `87cc4266…`; read only): line 13557 prints `packs NOT mounted: …` to stderr,
  which goes to the journal. Under gunicorn's 2 workers each worker would print it.
- The installer notes `FT0` (one second before the finance restart). After `/finance/healthz` answers 200 it runs
  `journalctl -u clinic-finance --since "$FT0" --no-pager -q | grep -q "packs NOT mounted"`. Nothing is printed. On a match it says so
  in one line and runs `restore` (both services).
- `S560_JOURNAL_CMD` lets the rehearsal use a made-up stub.

**C3 — never approved as spend** (`asset_register.py`, AR4).
- The one counted edit is anchored on `flash("Only draft bills can be approved.")` and its `return redirect(...)`. It adds a refusal
  for `doc_kind IN ('receipt','statement')`, with the line *"A receipt or a statement is never approved as a bill — the bill it pays
  is."*

**N1 — fit a real laptop.**
- Measured in the PC's headless Chrome at a viewport of exactly **1366 × 620** (window 1390 × 719): every destination (15), the
  five kinds, Save and the join / blank row are on screen, with **0 px overflow** and no cue needed.
- **No spacing change was made**, because none was needed. At 1366 px wide the panel is 615 px, so the buttons fit in fewer rows than
  at 1280 × 720.

**The walk** (`walk_s560.py`, on the box, isolated as before; 5 new checks):
- **Walk on the new files: `36 checks: 36 GREEN, 0 RED`.**
- `LIVE-STAMPS … B-0140 receipt . B-0139 receipt . B-0137 blank . B-0104 statement` (unchanged).
- `SIZES desk 36523 B (47 ms) . list 1738 B (20 ms)`.
- **Control on the live (S559) files: `36 checks: 3 GREEN, 33 RED`**, and
  `CONTROL must-be-red: W2 … N1, R4, S3, D2, R5, N2 -- all RED`.
- **Control on the S560 kit as it was before fix round 1** (`--must-red R4,S3,D2,R5,N2`): `36 checks: 31 GREEN, 5 RED (R4, S3, D2,
  R5, N2)` — `all RED`. What the old build did:
  - **R4:** the paid bill's receipt, re-opened, offered no bill (`'none'`).
  - **S3:** the re-opened statement had nothing ticked (`[]`), and the narrowed re-save was refused.
  - **D2:** `Marked: Paid 12-06-2031 · ₹640` gave a second payment, and the receipt-paid bill took a payment too.
  - **R5:** the allocation was not capped.
  - **N2:** `approved`.

| New check | What it proves (made-up rows) |
|---|---|
| **R4** | The paid bill's receipt, re-opened with its bill still ticked and saved: 1 payment, and the bill still reads *Paid*. A part-paying receipt re-saved as it was: 1 payment, *Part-paid ₹400 of ₹1,000* unchanged. Re-saved with a new date and ₹450: the same payment changed (1 row), 1 voided allocation kept, *Part-paid ₹450 of ₹1,000*, audited. |
| **S3** | A statement re-opened with its two invoices ticked and saved: 1 payment, each invoice paid once. Re-saved for ₹300 covering only the first: the same payment changed, and the second invoice is unpaid again. |
| **D2** | The paper's `pay.edit` is pre-filled `11-06-2031`, and the desk shows *"Paid on … — change?"*. Save changes that payment: the total number of payments is unchanged, and the date and mode are updated. *Paid?* on a bill paid by a receipt answers 400 *"already paid"*, and no payment is written. |
| **R5** | ₹800 against a ₹500 bill: ₹500 on it, the payment kept at ₹800, and the message names the rest. ₹500 against a bill owing ₹200 after a ₹300 *Paid?*: allocations ₹300 + ₹200, *Paid*. |
| **N2** | Old-page Approve: a draft receipt and a draft statement on the clinic lane stay draft (302 back to the page). A draft bill is still approved. |

**The pack walk** (`walk_s560_pack.py`; both pythons) — **`9 pack checks: 9 GREEN, 0 RED`** (the venv python gives the same):
```
2031-09 construction_accountant  before -              after C1,C2,C6
2031-09 lab_purchase (8.1)       before LB,LC,LF,LR    after LB,LF
2031-09 owner_expense (8.2)      before C2,E1,E2       after E1        (statement E2 out; ticked construction bill C2 now 8.4 only)
2031-09 owner_expense_bhawna     before E3             after E3
2031-10 construction_accountant  before -              after C7
2031-10 lab_purchase             before L2             after L2
C2-LANES (the bundles holding made-up C2): {'owner_expense': ['construction_accountant'], 'lab_purchase': ['construction_accountant']}
```
- The new check **C2**: made-up C2 is on the owner-expense lane, then moved to the lab lane. Each time it is only in 8.4.
- **P3** now expects 8.2 = E1.
- **Pack control, live packs.py:** `9 pack checks: 2 GREEN, 7 RED`, and `CONTROL must-be-red: P2, P3, P5, P6, P7, P8, C2 -- all RED`.
- **Pack control, the kit before fix round 1:** `7 GREEN, 2 RED`, `C2, P3 -- all RED`. The old build had C2 in
  `['construction_accountant', 'owner_expense']`, then `['construction_accountant', 'lab_purchase']`.
- S548's pack walk on the new packs.py: `8 checks, 8 green, 0 red`.

**The earlier walks on the new files** (inside the rehearsal's installer):

| Walk | Result |
|---|---|
| S559 | `43 checks: 43 GREEN, 0 RED` |
| S557 | `41 checks: 41 GREEN, 0 RED` |
| S555 | `19 checks: 19 GREEN, 0 RED` |
| S551 (S559's three agreed lines) | `87 checks: 87 GREEN, 0 RED` |
| S548 | `8 checks, 8 green, 0 red` |

**The browser walk** (headless Chrome on the PC; made-up rows) — **`7 browser checks: 7 GREEN, 0 RED`**:

| Window → viewport | Result |
|---|---|
| 1366 × 768 → 1342 × 669 | All on screen, 0 px. |
| 1280 × 720 → 1256 × 621 | Only *Not here* below, with the cue (76 px). |
| 1920 × 1080 → 1896 × 981 | All on screen, 0 px. |
| **1390 × 719 → 1366 × 620** | **All on screen, 0 px.** |
| For the record: 1342 × 641 | All on screen. |
| For the record: 1342 × 526 | Four groups under the cue. |

R, S and C are green as before. **Negative control** on the live S559 desk: `12 of 14 destination buttons hidden` at 1342 × 669,
and **`14 of 14 hidden` at 1366 × 620**. The full output is in `walk/walk_results_s560.txt`.

**The rehearsal** (`rehearse_s560.sh`, made-up root, both services faked) — **`REHEARSAL GREEN`** (exit 0), six outcomes:

| Outcome | Result |
|---|---|
| 1 | DONE. Rebuilt = the new pins `b5993236 88963eac 9daed9ea 048d2ad8`. Every walk and control above passed. The database backup was taken before the data step. The undo line starts `\cp -p`. The lock was released. The installer printed *"/finance/healthz 200; packs.py loaded (no 'packs NOT mounted' in the finance journal since the restart)"*. |
| 2 | ALREADY INSTALLED. |
| 3 | Forced red → restored to `a59fa38d 80e3cd8d 20ef7bc6 d86d351a`, both health answers 200. |
| 4 | `/desk` 404 → restored. |
| 5 | `/desk` 200 → restored (302 only). |
| **6 (new)** | `/finance/healthz` 200, but the made-up journal says `packs NOT mounted` → *"/finance/healthz 200, but packs.py did not load"* → restored to the FROM pins. |

**The kit and the gates.**
- `deploy_kits\S560_RECEIPTS_STATEMENTS\` holds 26 files + `SUMS.md5`, all LF, no BOM, no `__pycache__`, no database and no copy
  of a live file.
- **Byte-identical to what ran:** the box's md5 of the 21 executed or pinned kit files (installer, rehearsal, builder, the three
  blocks, both walks, the 13 pins) equals the repository copy (0 differ).
- The browser walk's two scripts ran on the PC from the final bytes (`run_browser_walk_s560.py 8904a89a`, `layout.js 58285124`).
- `README.md`, `KIT_ID.txt`, `walk/walk_results_s560.txt` and `SUMS.md5` were written after the runs; none of them is executed.

**Calls I made (the brief left room), each with its reason.**
1. **"Updates that payment"** is done literally. The payment row's date / amount / mode / ref are updated in place, with the old values
   in `payment_changed`, rather than voiding the payment and writing a new one. The brief says "updates" and "never a second
   payment". So `paper_payment` is no longer strictly append-only; every change stays in the audit.
2. **"The old allocation rows voided"** needed a voided state on `paper_payment_bill`. I added `voided_at` / `voided_by` and put
   `voided_at` into the key (`PRIMARY KEY(payment_id, bill_id, voided_at)`). The S560 brief's §4.5 key was `(payment_id, bill_id)`.
   The tables are not live yet, so nothing on the box changes shape.
3. **D2 "as the review names it"** is kept under its name with the brief's meaning. *Paid?* on a Paid bill now **changes** the one direct
   payment instead of being refused. It is still refused, with nothing written, when the bill is paid by a receipt, a statement, a
   note on the paper, or several payments.
4. **C1's exclusion** matches 8.4's own selection exactly (kind Bill, ticked, construction). A ticked estimate, which the desk can never
   make, therefore stays in its lane rather than vanishing from both.
5. **The C3 walk check** is a new check, **N2**, so N1 keeps its meaning and the control names it separately.
6. **A receipt re-saved as the receipt of a statement** voids its own earlier payment, because the money is the statement's (counted
   once).
7. **N1 needed no tightening.** The words and order are unchanged.

**The other review notes — seen, not changed.**

| Note | What it says |
|---|---|
| **N2** | The word rules can over-fire (a "Receipt book" line). |
| **N3** | Restore of a blank set-aside goes straight back to `approved`, past `_dup_by_triple`. |
| **N4** | A statement invoice with no total takes the whole remaining payment. |
| **N5** | Duplicate `id=s560mark` / `id=s560paid`. |
| **N6** | The implant ledger: a "no bill" payment is not shown, and there is no cross-check against *Note payment*. |
| **N7** | The receipt → statement link lives in `bill_audit` only. With B1 an unchanged re-save no longer adds a row. |
| **N8** | 8.4 shows "missing" in months with no ticked bill. |
| **N9** | The NULL `created_at` fingerprint. |
| **N10** | `desk_fix_answered` is written on every Save. |
| **N11** | The `.gitignore` check — re-run below. |
| **N12** | A failure at the finance restart was never rehearsed. The new outcome 6 now runs that path, as a by-product of C2. |

**Not done, and seen outside the brief.**
- **Not installed, not published, no build lock taken,** as the brief says. `asset_machine.py`, `scanner_widget.js` and the DUTY_MAP
  were not touched.
- **Seen, outside the brief:** a receipt that recorded a payment and is later re-saved as a **Bill** keeps that payment live, with
  itself as the proof. The brief names only receipt / statement re-saves. The payment can be voided on the desk; a later kit could
  void it automatically.
- **The permission list refused** my `rm -rf` of my own box scratch folder. I did not respell it.
  - I used fresh folders: `/tmp/s560fix1a`, `/tmp/s560fix1b` and `/tmp/s560fix1probe` remain on the box, holding kit copies and logs
    only.
  - The three scratch files holding live data (`work_104847/snap.db` and two `list.json`) were deleted one by one with a plain `rm`
    (10:56:40; 0 left).
  - The PC's two `list.json` copies in `_scratch\S560_FIX1\` were deleted too.
  - The rehearsal's made-up root was removed by its own final run.

**FOR THE PARENT:** once this kit is installed, `/root/finance/packs.py` becomes **`048d2ad81abb0271a1cddd31134544bb`** (not the
`f8d9a8f4…` named in the first round). Build on that byte only. The new item is still **8.4 · Scanned bills: Construction bills
marked for the accountant**. A ticked construction bill now appears there only.

**Cost of fix round 1:** about **US$5.5** of API credit, read from this session's budget meter when this section was written.

**Gates (fix round 1).** These were run on the 26 kit files + `SUMS.md5`, this report and the brief, after this section's words
were written:
- `SUMS.md5`: 26 lines, 0 mismatches.
- `.gitignore` (last match wins): `git check-ignore -v --non-matching` over the 29 files gives 29 lines, **0 ignored** (GitHub
  Desktop's git, read only).
- Contact-number gate, as PUBLISH_ALL runs it: `NO_PHONE_NUMBERS: clean -- 29 staged file(s) checked (numbers and credentials).`
- No `__pycache__` in the kit or the briefs folder.

**Nothing installed, nothing published.**

---

## Round 1 (14-Oct-2026) — kept as written; its TO pins are superseded by fix round 1 above

**For Dr Manoj (plain English):**
- **The sorting desk now fits one laptop screen.** *What was read* folds into one line. Every place a paper can go shows at once,
  in a tight grid: *Clinic consumables · Clinic expense · My expense — Dr MK / Dr Bhawna · Handed over · Documents · Not here*.
  Your Clinic and Personal buttons are no longer hidden under the Save bar.
- **Receipt and Statement are new paper kinds.** A receipt asks *"Pays which bill?"* (the likely bill is already ticked) and is
  filed with that bill. The bill then shows *"Paid 08-10-2026 · ₹850 · Cheque · no. …"*, and the receipt's scan is one tap away.
  A statement ticks the invoices it pays and shows any difference. **Neither is ever counted as spend** — only the bill is.
- **Construction bills** get a tick, *Send to accountant* (off unless you tick it). Ticked bills go into a new line, **8.4**, in
  the accountants' pack. The pack no longer carries receipts, statements, or challans still waiting for their bill.
- **Four papers wait at the top of your desk list, one tap each, with the reason:** B-0137 (*set aside as blank, but it reads as a
  bill — restore?*), B-0139 and B-0140 (*this looks like a receipt*), and B-0104 (*this looks like a statement*). Nothing is
  changed until you tap. Bills awaited now lists each challan's items.
- Every check passes on a copy of your data, and the same checks fail on today's files. **Nothing is installed yet.**

---

## For the chat — the proof

**Run.** All times are IST, read from the box clock unless marked.
- FROM pins read on the box at **20:34:59**. All eight equal the brief.
- The final rehearsal (which runs the installer, with every walk inside it) ran **21:07:31 → 21:09:25**.
- The live state was re-read at **21:09:56**. The box's `/tmp/s560*` was removed at **21:11:39** / **21:11:44**.
- The browser walk ran on the PC; the time is in `walk/walk_results_s560.txt` (PC clock).
- **No build lock was taken**, because nothing was placed. The lock was absent at 20:34, 21:03 and 21:09. The lock is taken only
  inside `install_s560.sh`.

**Read first:** S551 v4 (+ FIX1), S555, S557 (+ FIX1), S559 + S559_FIX1 and their reports; S559's whole kit, whose shape is copied;
S548's kit (the pack walk); `BUILD_NORM_v1.md`; the live `claude_reader.py` (its `doc_kind` values: tax_invoice, bill, estimate,
challan, quotation, other — there is **no receipt or statement kind**). I also took a read-only look at the six named papers on
the box (stamps, kinds and amounts only).

### 1 · Pins (read on the box; all equal to the brief)

| file | FROM (live = brief) | TO (rebuilt on the box = Windows build) |
|---|---|---|
| `/root/assetapp/sorting_desk.py` | `a59fa38d7c7f145c8fefa52bad5676d1` | **`5017fe926b185e88bfd5c84eb40e6481`** |
| `/root/assetapp/clinic_papers.py` | `80e3cd8d2ef8e8953b2ae3fec3f85203` | **`88963eacee217e051ae07091648a46d7`** |
| `/root/assetapp/asset_register.py` | `20ef7bc6b44079f3181d9c52519e8b94` | **`5c8b309725d0a36dd4da4f63e9c3ec38`** |
| `/root/finance/packs.py` (THE PARENT'S) | `d86d351a46a1ba4da7d0e615da0deb1a` | **`f8d9a8f45938da408f94992e0880a8c2`** |
| `asset_machine.py` (read; **not edited**) | `0caec41e655cfd51c2eaf9176ee33365` | — |
| `scanner_widget.js` (**not touched**) | `1128ac975ba2543e1fe9edf7c721d4f8` | — |
| `claude_reader.py` / `claude_reread.py` (read) | `3894dc23…` / `d9b75e78…` | — |

- All four built files compile on `/usr/bin/python3` and on `/root/wa/venv/bin/python3`.
- `packs.py` was at its pin, so it was built (no STOP).
- `asset_machine.py` is not edited: no machine's Spends needed a Paid line for this brief's surfaces.

### 2 · The counted edits (`make_s560.py`; each anchor found exactly once, on Windows and on the box) — 66 in all

**`sorting_desk.py` (52 edits, plus `s560_sd_block.txt` before the mount and `s560_js.txt` in the desk's script)**

| Area | What changed |
|---|---|
| Marks and kinds | `RECEIPTS = "S560"`; `KINDS` + Receipt, Statement; group titles *Clinic expense* and *My expense — Dr MK / Dr Bhawna*. |
| Database | `BILL_COLS` + `to_accountant INTEGER NOT NULL DEFAULT 0`; `DDL` + `paper_payment` (mode CHECK cash/cheque/bank, `proof_created_at`) and `paper_payment_bill` (PRIMARY KEY(payment_id, bill_id), `bill_created_at`). Created by the existing `ensure()`, which tolerates two workers. |
| Waiting | A receipt or statement is never flagged *"a bill — this supplier has open challans"*. `waiting()` returns `_s560_with_fixes(...)`, which puts the papers to put right on top. `_hint` gives their reason. |
| paper_json | The Claude pre-choice goes through `_s560_claude_kind` (a block means nothing is pre-chosen). New fields: `pay`, `rc` (cands, stmts, prefill), `st`, `fix`, `to_acc`. |
| Save | `_s560_pre` runs before the destination check: it validates the receipt / statement / *Paid?* and forces the receipt's place to the bill's place. `accept` is turned off for a receipt or statement. `_s560_post` runs after: Filed (captured), the payment, the construction tick, the fix answered. `desk_saved` now carries `"s560": 1`. `_doc_kind` takes receipt / statement. |
| Bills awaited | `{{r.items}}` → `{{r['items']}}`. |
| Ledger | A receipt or statement row is never owed. `_s560_ledger` adds each S560 allocation of an implant bill once. |
| The month | *paid N / unpaid M* per section; Construction gets *M marked for the accountant*. One `paid_map` read per page. |
| Desk layout | The right panel is `clamp(440px,45vw,640px)` and the left list 220 px. *What was read* is a `<details>` with a one-line summary. Groups flow inline. Buttons are ≥ 36 px and the kinds sit inline with their title. The header row is compact, and a *more ▾* cue sits in the footer. The receipt, statement and *Paid?* boxes are added, plus *Send to accountant*. Personal expense is drawn as *Dr MK* / *Dr Bhawna* (same `pe` + `who`). The ids S555's I1 reads (`save`, `savednote`, `pagebox`, `blank`, `f_vendor`, `groups`, `flags`, `#fields`/`#foot` rules) are kept. |
| Routes | `POST /desk/api/fix` (restore / keep) and `POST /desk/api/payment/void`, both behind the desk's gate and `checker_required`. |

**`clinic_papers.py` (6):** `RECEIPTS` mark. `_live` and `_live_sections` now leave out `('challan','receipt','statement')`.
`_accept` refuses a receipt or statement. `heal()` never accepts one. `challan_for_bill` offers no challan to one.

**`asset_register.py` (3 + `s560_ar_block.txt` after S559's block):** the old bill page gets `{{s560_paid(b)}}` under Total. All
papers gets `{{s560_mark(b)}}` beside the total (one `paid_map` read per request, kept on `g`). Both helpers return `''` on any
error.

**`packs.py` (5, inside `build_bundle` and the item-8 list only):**
- New `lane_sql, xk_sql`. Every bundle gets `COALESCE(doc_kind,'bill') NOT IN ('receipt','statement')` and leaves out an awaiting
  challan. Both are guarded on the columns existing, so an older database works as today.
- The new lane `construction_accountant` selects `subgroup=?` ('construction') AND kind Bill AND `to_accountant=1`, on any lane,
  `status<>'rejected'`, by the pack's own month rule.
- The new lane has its words in the "no … scans" line and the index title.
- The item-8 list gets **`("construction_accountant", "Construction bills marked for the accountant")` → item 8.4** (the list is
  numbered by `enumerate(..., 1)`, so it follows 8.3).

### 3 · The walk (`walk_s560.py`, on the box, isolated as S559's)

**Isolation:**
- A backup-API snapshot of the database.
- The scratch import, with `__file__` asserted.
- The environment set before import (`ASSETS_DB`, uploads, a made-up key and URL, `CLINIC_PORTAL_DIR`, `FINANCE_LOCAL_URL`,
  `SHARED_LIB_DIR`), with no reader keys.
- Made-up logins `walk_own_2031` / `walk_mgr_2031`.
- Made-up papers `Z-2031-R…`, from suppliers whose first two words differ, found by key.
- Today is made up as 15-Jun-2031.
- The walk and the control run in separate processes.

**Log (inside the rehearsal's installer, 21:07–21:09):**
- **Walk on the built files: `31 checks: 31 GREEN, 0 RED`.**
- `LIVE-STAMPS the fix rules list on the copy (stamps and reasons only): B-0140 receipt . B-0139 receipt . B-0137 blank . B-0104 statement`
- `SIZES desk 35703 B (47 ms) . list 1313 B (23 ms)`
- **Control on the live (S559) files: `31 checks: 3 GREEN, 28 RED`.**
  - `CONTROL must-be-red: W2, W3, K1, K2, R1, R2, R3, S1, S2, P1, V1, F1, L1, D1, C1, C2, X1, X2, X3, G1, A1, I1, M1, U1, U2, B1, B2, N1 -- all RED`.
  - The 3 that stay green are W1, T1 and T2 (the import, the speed, the scratch copy).
  - A1's red reproduces the live fault exactly: `built-in method items of dict object`.

| Checks | What they prove (made-up rows) |
|---|---|
| W1–W3 | Isolation; the S560 marks with the older ones kept; the code's own DDL holds the two tables and the column (fingerprinted, mode CHECK), and they exist after mount. |
| K1, K2 | All five kinds are saved and read back. Claude pre-choice: receipt text + kind `other` → Receipt; receipt text + `tax_invoice` → nothing; a plain invoice → Bill. Nothing is saved without Save. |
| R1–R3 | **Receipt → bill:** the list is newest first, the same-amount bill is pre-ticked, ONE payment (cheque, no., fingerprint, proof), the bill is Paid, and the receipt is Filed in the bill's place (clinic · Others), never accepted, with the Others total unchanged. **The Paid line** reads `Paid 08-06-2031 · ₹850 · Cheque · no. 123456`, with the receipt's stamp, on the desk and on the old bill page. **"No bill — paid directly":** refused without a place; then one payment with no bill under it, filed on NK Pathology. |
| S1, S2 | **Statement** covering 3 made-up invoices (₹300 + ₹400 + ₹500), with the 4th (outside the period) untouched. The difference line and grey line are in the desk. **Receipt → statement:** linked as proof; the payment count is unchanged (counted once). |
| P1, V1, F1 | **Part-paid** `Part-paid ₹400 of ₹1,000` on the desk, the bill page and All papers. **Void:** the bill is unpaid again, the row is kept with voided_at/by, and a second void is refused. **Fingerprint:** the paid bill's id is re-issued to a new paper, which reads unpaid. |
| L1, D1 | A lab bill's receipt is filed on the NK Pathology lane. **Paid?** on a bill is refused without a mode; then it reads `Paid 11-06-2031 · ₹640 · Bank / UPI · no. UTR9` with the *Paid* mark. |
| C1, C2 | *Send to accountant*: saved when ticked on a construction Bill; off by default; forced off for an estimate, a challan, and a ticked bill turned into an estimate. The month shows `2 bills … · 1 marked for the accountant`. |
| X1–X3 | **The five fix hints** for their made-up look-alikes, at the top of Waiting with their texts: blank-but-reads-as-a-bill, receipt, statement and Resumes. A plain bill is not listed. *Restore* puts the paper back to draft with the reason cleared, audited; *No — leave it* takes it off the list; Restore is refused on a non-blank. A Save as Statement answers it. |
| G1 | **The manager's own eyes** (signed in as him, desk on): the five kinds, no Personal button, and the papers to put right on his list. |
| A1 | Bills awaited prints `WALK ENVELOPE 8.5 X 10.5 × 2 · WALK TAPE × 1`. |
| I1 | The implant ledger: its own *Note payment* ₹1,000 + the desk's ₹2,000 = Paid ₹3,000, two Payment rows, each once. The receipt filed there is never owed. |
| M1, U1, U2, B1, B2, N1 | *paid / unpaid* per section, with receipts and statements in no total. The six group titles are in order; *Dr MK* / *Dr Bhawna* sit beside *Personal (you only)*; buttons are ≥ 36 px. The folded summary, the cue, and Save / join / blank are in the footer. The bill page's Paid line sits under Total. All papers marks only the paid bill. A receipt or statement is never spend (`_live`, `_live_sections`, `_accept`, `heal`). |

### 4 · The earlier walks on the new files (inside the rehearsal's installer)

| Walk | Result |
|---|---|
| **S559** | `43 checks: 43 GREEN, 0 RED`. The baseline was dumped on the live S559 files. `--from-widget` is the box's pinned pre-S559 backup `scanner_widget.js.bak_S559_1143c77b`. |
| **S557** | `41 checks: 41 GREEN, 0 RED`. The baseline was taken from the S560 build without `asset_machine.py`, as S559 did. |
| **S555** | `19 checks: 19 GREEN, 0 RED`. |
| **S551** | `87 checks: 87 GREEN, 0 RED`. It runs through S559's frozen `s551_lines_s559.py`, unchanged. |
| **S548 (the old packs.py walk)** | `8 checks, 8 green, 0 red` on the new packs.py: fully green, so no "intended row" exception was needed. |

My first run showed **S551 S6 RED**. The manager's desk page carried the words *Personal (you only)* inside the page's name list
for the "Filed with …" line (it was not a button). The list is now filtered for a non-owner, and S6 is green.

### 5 · The browser walk (headless Chrome on the PC; made-up rows only) — `6 browser checks: 6 GREEN, 0 RED`

| Window → viewport | Every destination (15), the 5 kinds, Save, join / blank | Panel overflow |
|---|---|---|
| **1366 × 768 → 1342 × 669** | **all on screen** | 0 px |
| **1280 × 720 → 1256 × 621** | all but **Not here** (its one button), with the **more ▾** cue visible; kinds, Save, join / blank on screen | 76 px |
| **1920 × 1080 → 1896 × 981** | all on screen | 0 px |
| *for the record* 1366 × 740 → 1342 × 641 (a 1366 × 768 laptop with the taskbar and Chrome's bars) | all on screen | 0 |
| *for the record* 1366 × 625 → 1342 × 526 | My expense, Handed over, Documents and Not here below the fold, with the cue | — |

At every size the buttons are at least 36 px, the page itself never scrolls, *What was read* is folded, and there is no script error.

| Check | Result |
|---|---|
| **R** | Receipt: 3 choices, the likely bill pre-ticked; *"Filed with Z-2031-RA2, on its place: Others. Never counted as spend — the bill is."*; Save reads *Save — next paper*. |
| **S** | Statement: period 01-05 → 31-05 ticks 3 of 3. It shows **`Ticked ₹1,200 of statement ₹1,300 — difference ₹100`** and the grey line, with Save on screen. |
| **C** | *Send to accountant* is shown on Construction + Bill, off by default, and hidden for an estimate. |
| **Negative control** (the live S559 desk, the same measure) | `12 of 14 destination buttons hidden below the fold` at 1366 × 768. This is the owner's finding. |

### 6 · The pack, before / after (`walk_s560_pack.py`; made-up assets rows; both pythons) — `8 pack checks: 8 GREEN, 0 RED`

```
2031-09 construction_accountant  before -              after C1,C2,C6
2031-09 lab_purchase (8.1)       before LB,LC,LF,LR    after LB,LF        (receipt LR and awaiting challan LC out; final challan LF stays)
2031-09 owner_expense (8.2)      before C2,E1,E2       after C2,E1        (statement E2 out)
2031-09 owner_expense_bhawna     before E3             after E3
2031-10 construction_accountant  before -              after C7
2031-10 lab_purchase             before L2             after L2
```

- 8.4 carries only the ticked construction **bills**, whatever their lane (clinic, Personal expense, Other document). It never
  carries the unticked bill (C3), the ticked estimate (C4) or the rejected bill (C5).
- P8: only those rows change.
- Pack control on the live packs.py: `8 pack checks: 2 GREEN, 6 RED`, `CONTROL must-be-red: P2, P3, P5, P6, P7, P8 -- all RED`.

### 7 · The rehearsal (`rehearse_s560.sh`, made-up root `/tmp/s560dev/root`, both services faked) — **`REHEARSAL GREEN`**

| Outcome | Result |
|---|---|
| 1 | DONE. Rebuilt = pins (`5017fe92 88963eac 5c8b3097 f8d9a8f4`). Every walk above passed. The database was backed up *before* the data step (proven: the backup has no `paper_payment`, the made-up live copy has it). Backups beside all four files. The undo line starts `\cp -p`. The lock was released. |
| 2 | ALREADY INSTALLED. |
| 3 | Forced red after placing, run on the database outcome 1 left (its tables kept, as after a real restore): restored to `a59fa38d 80e3cd8d 20ef7bc6 d86d351a`, both health answers 200. |
| 4 | `/desk` 404 → restored. |
| 5 | `/desk` 200 → restored (302 only). |

**The rehearsal caught one fault, now fixed.** My first outcome 3 refused at the control. Its database check (W3) went green
because the made-up database already held the new tables from outcome 1. A real re-run after a restore would have done the same.
W3 now tests the code's own table list, and the rehearsal resets its database between outcomes (except outcome 3, on purpose).

**After (21:09:56):**
- The live pins read `a59fa38d 80e3cd8d 20ef7bc6 0caec41e 1128ac97 3894dc23 d9b75e78 d86d351a` (all FROM), with 0 `bak_S560` files.
- `assetapp` and `clinic-finance` are active. `/healthz` 200, `/desk` 302, `/finance/healthz` 200.
- The live database has no `paper_payment` table and no `to_accountant` column.

### 8 · The kit and the gates

- `deploy_kits\S560_RECEIPTS_STATEMENTS\` holds 26 files + `SUMS.md5`, all LF. There is no `.json`, no database, no copy of a
  live file and no `__pycache__`.
- **Byte-identical to what ran:** the box's md5 of the 23 executed or pinned kit files equals the repository copy (0 differ).
  `README.md`, `KIT_ID.txt` and `walk/walk_results_s560.txt` were written after the run; they are not executed. The browser walk's
  two scripts ran on the PC from the same bytes.
- **SUMS / .gitignore / contact-number gate:** see the gate lines at the end of this report.

### 9 · Calls I made (the brief left room), each with its reason

1. **"Only if the reader's own kind supports it."** The reader has no receipt or statement kind. I read `other` as the kind
   that allows a Receipt / Statement pre-choice. Any other kind, with receipt words, means nothing is pre-chosen.
2. **"Read text."** Claude's stored reading has no free text, only vendor, no., date, amount and items. So *"says receipt"* is read
   in those fields, and the fix rules use what the reading does carry:
   - **Receipt:** an `other` paper with an amount, no goods line, and a same-supplier bill of that amount within 60 days.
   - **Statement:** an `other` paper with ≥ 3 priced lines and no single bill number and no single date. That stands in for "a
     period", which no reading carries.
   - On the copy these rules pick exactly B-0139, B-0140 and B-0104.
   - B-0103 is not listed, because `suggest()` does not say resume for it, as the brief allows.
3. **A receipt or statement is *Filed* (captured), never accepted.** That keeps it out of every approved-only total (the dashboard,
   /purchases) without touching those pages. If one was already accepted, saving it as a receipt sets it back to Filed (audited).
4. **A receipt that pays a statement records no second payment.** It is linked as the statement's proof, so the money is counted
   once.
5. **A statement's payment** is spread over the ticked invoices, oldest first, each up to what it still owes. Anything left over
   shows only as the difference.
6. **Personal expense** is shown as its two choices *Dr MK* / *Dr Bhawna* under the group title. The owner sees 15 destination
   buttons (the brief's "16" counts Personal expense plus its two choices).
7. **The fingerprint columns** (`proof_created_at`, `bill_created_at`) are added to the brief's DDL, as its "S557's fingerprint
   rule" asks.
8. **The data step** runs sorting_desk's own `ensure()` from the built file once, after the backup-API copy and before placing. It
   does not wait for the workers to start, so a locked database at mount can never leave the tables missing.
9. **The installer is all-or-nothing across both services.** If the parent has moved `packs.py`, it refuses and places nothing.
   Placing the desk without the pack fix would let a receipt on the lab lane count in 8.1.
10. **The papers to put right are counted in *Sorting desk (N)*.** The bar's N stays `len(waiting())` (S559's rule), so N rises by
    those papers until each is tapped.

### 10 · Not done, and seen outside the brief

**Not done:**
- **Not installed and not published,** as the brief says.
- `asset_machine.py` and `scanner_widget.js` were not edited, and neither was the DUTY_MAP (the brief forbids it). No staff duty is
  added: the list of papers to put right sits on the desk's existing Waiting list.

**Seen outside the brief (not touched):**
- **B-0137's stored total is ₹1.00** (Claude read ₹850). B-0139's stored date reads 16-08-2024 and its amount ₹650 (Claude:
  08-10-2026, ₹850). B-0140's stored no. is 13625 (Claude: 13825). The desk's *Claude read … — use it* lines offer each
  correction at the person's Save.
- **On a cramped viewport (1342 × 526)** the lower groups need the *more ▾* cue.
- **The permission list refused** a local `Remove-Item -Recurse -Force` of my own scratch folder. I did not respell it: I used new
  scratch folders under `_scratch\S560_RECEIPTS_STATEMENTS\` (git-ignored) and left them there.

**FOR THE PARENT:** `/root/finance/packs.py` becomes **`f8d9a8f45938da408f94992e0880a8c2`** once this kit is installed. Build on that
byte only. The new pack item is **8.4 · Scanned bills: Construction bills marked for the accountant**.

**Cost:** about **US$12** of API credit for this run, read from this session's budget meter when this report was written.


**Gates (run after this report's final words; the files gated: the 26 kit files + SUMS.md5, this report and the brief):**
- `SUMS.md5`: 26 lines, 0 mismatches.
- `.gitignore` (last match wins): `git check-ignore -v --non-matching` over the 29 files gives 29 lines, **0 ignored** (GitHub Desktop's git, read only).
- Contact-number gate, as PUBLISH_ALL runs it: `NO_PHONE_NUMBERS: clean -- 29 staged file(s) checked (numbers and credentials).`
- No `__pycache__` in the kit or the briefs folder.

**Nothing installed, nothing published.**
