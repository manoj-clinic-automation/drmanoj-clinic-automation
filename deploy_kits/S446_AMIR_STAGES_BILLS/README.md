# S446_AMIR_STAGES_BILLS — what S444 did not carry (D649 · D650 · F-673 F-674 F-679 F-680)

**Sanjeevni project · session 283 · 02-Oct-2026 · brief `claude_code_briefs/S446_AMIR_STAGES_BILLS.md` · runs after S444_STAFF_SAFE
(installed 01-Oct 22:08 IST).** Staff pages in Hindi (Roman script), the owner's in English.

## What was built

**3.1 The count in gated stages (D649) — `stock_app.py` (`amir_stage`, `_s446_proof`, `_s446_board_filter`) + `amir_day.py`.**
Count #1's corrections reach Amir one stage at a time; the owner and the checker keep the whole board.

- **Stage A — the orthotic vouchers.** These are the 7 batches whose items are all orthotics: ISSUE first, then by round, numbered 1..7
  on his board. The card reads "Orthotic voucher baaki: N — kholiye".
  - When all 7 are entered, it reads "Ab closing stock export kijiye".
  - The next closing-stock export is proved over the orthotic lines only, using S304's drift (Marg's feed minus the expected feed, day R
    before the first entry → day L after the last).
  - The result is "Orthotic: sab sahi ✓", or each wrong item named with Marg's figure, the shelf figure expected and its voucher number.
  - Proved once → `stock_stage_event` (count, A, verified).
- **Stage B — the renames.** Shown only once A is verified (until then the board reads "नाम बदलना — orthotic voucher Marg में सही
  होने के बाद").
  - When every `item_alias` row is verified, the owner gets one Needs-you line for two days: "Orthotics verified and renamed -- live
    orthotic ordering can start".
  - The card shows "Orthotic poora ✓".
- **Stage C — the medicine and consumable vouchers.** These come `amir.vouchers_per_visit` (5) at a time, oldest round first: "Dawa
  voucher: aaj ke 5 (baaki 25) — kholiye".
  - Each lot is proved on the next export.
  - The next lot is released when a lot is proved, or after 2 of his visits.
- The stages never block Din band.
- The owner's line (d) names the stage: "Count vouchers waiting (Stage A, orthotic): N".
- The owner also gets an info line: "Count #1: Stage A 3/7 entered".
- Count #1 has **37** batches, not the brief's 39: 7 orthotic, and 30 medicine and consumables (rounds 1, 2, 5).

**3.2 Packs by state — `amir_day.py`.** Every month of the last three that `packs.amir_pack` (read only) calls ready and not yet
"dekh liya" stands in the card. The S408 foot card is gone.

**3.3 The scanned bills as files (D650, F-679) — `purchase_app.py` + `amir_day.py`.**
- **Step 2:** "Marg mein daalne ke bill (N)". This lists every captured pharmacy scan with no Marg bill linked, each a download named
  `<SUPPLIER>_<billno>_<dd-mm-yyyy>.pdf` (`/finance/purchase/api/scan-file/<id>`). "Aaj ke sab" downloads today's as one zip.
- **Who may download:** Amir and the owner/checker only (setting `purchase.scan_file_users`, default `amir`); anyone else gets 403.
- **The Sarvam trial** runs until `purchase.sarvam_trial_until`, which is the install date + 2 months.
  - Each linked scan is compared field by field with its Marg bill (`purchase_sarvam_check`):
    - the supplier, allowing for its known aliases;
    - the bill-number digits;
    - the date;
    - the total, within ₹1;
    - the items, matched by name, then quantity, rate, batch and expiry.
  - Marg overrules.
  - The comparison appears as one line on the Scan links page, plus `/finance/purchase/page/sarvam` (owner/checker).
  - Each month there is one Needs-you info line with the month's summary.

**3.4 The medical PC (F-674) — `medical/`.**
- **The reader fix.** `marg_txt.py` reads an item line whose second number column Marg prints as `***` (the 30-Sep sale, line 52).
  It goes through Drive `ToMedical\_kit` with its `KIT_MANIFEST.txt` line (md5-gated; proved GREEN 59/59, `medical/PROVE_S446_RESULT.txt`).
  `marg_watch.py` is unchanged and not delivered.
  - **The manifest exists in two copies.** The repository stores `.txt` with LF (`.gitattributes`), so `medical/KIT_MANIFEST.txt`
    here is `60992cf0…`. The copy delivered to Drive keeps the agent's CRLF lines, `bdd277686cb76f944d4569e666a9d89f`. The two
    differ only in line ends.
- **The refusal note cannot travel unchanged.** The push door (`marg_take`) refuses anything not `.xls/.xlsx/.pdf` before it opens the
  database. A note would need a new door, which is not built here (see `medical/README.md`).

**3.5 The doors.**

| Who | Where | What they see |
|---|---|---|
| Amir | Card | The full-count Sunday ("Poori ginti ka Sunday"), the arrived-goods bills ("Marg mein bill baaki") and the trace fixes, each only while due. |
| Darpan | Kal ka hisaab (`darpan_kal`) | "Amir ke claim". Each open claim has two taps: *Baat hui* (contacted) and *Mil gaya* (settled, `darpan_received`). |
| Shavez | Vendor payments | "Pichhle mahine ka baaki: N" — last month's supplier messages still unsent. |
| Owner | Counter-returns line (`sanjeevni_approvals.py`) | Counts every open month (last six) from `returns.act_from`, naming the oldest. |

`DUTY_MAP.md/.json` v2 carries every changed door.

## Pins (FROM → TO, md5)
| live file | FROM | TO |
|---|---|---|
| /root/finance/amir_day.py | 2b497142efdb1a3d1b84e9f05cbf59ac | cd8f4659cb828c09e9455d1b7543cfbd |
| /root/finance/stock_app.py | c0120fb67c78105fe797982fcb6ab644 | ec6b1ce80d46b808d034b23cab032dc9 |
| /root/finance/sanjeevni_approvals.py | d2c550401ebfb7716126d24a09fae78f | 792f4a9af1728c76e8d5a656f5662421 |
| /root/finance/purchase_app.py | a51fe90eaa2922ba4e2b4db6388f797a | 176fc6eac35c7a3e7d052cba96ca873e |
| /root/finance/darpan_kal.py | 803970bd04c7203632b98d9659923b3b | 377ffd63786261cef4a6113482d43bb5 |
| /root/finance/darpan_kal.html | a4eecb21a88f793ab5c81b75dab20a51 | 9269afb04a454b626895a27666032752 |
| /root/finance/packs.py (READ ONLY) | 6a1cf6ceec4a58260df7352e48cdefe5 | unchanged |
| medical PC D:\SendToClinic\marg_txt.py | 38d85298f1627ab22b59c9f3459d8764 | 70f920c445ec82fc8c1e069f1f758efb |
| medical PC marg_watch.py | 81145aa7d7c8e9f7e23072cfab1ee620 | unchanged |

**What it touches:**
- **Data** (finance.db, backed up first):
  - three settings rows (INSERT OR IGNORE): `amir.vouchers_per_visit` 5, `purchase.sarvam_trial_until`, `purchase.scan_file_users` amir;
  - two additive tables made on first use: `stock_stage_event`, `purchase_sarvam_check`.
- **Restarts:** `clinic-finance` only.
- **Not touched:** porders.py, portal.py, clinic_sso.py, tile_grants.json, finance_app.py, crontab. The installer reads their md5s before and after.

## The files
- `make_s446.py` — the anchored patcher, plus the blocks it appends: `amir_block_s446.py`, `stock_block_s446.py`, `purchase_block_s446.py`, `darpan_block_s446.py`, `approvals_block_s446.py`.
- `walk_s446.py` — the walk (on scratch copies; the negative control on the box as it is). It covers:
  - the stages, the packs, the files and the 403;
  - Sarvam on crafted bills;
  - the doors;
  - the staff-eye walk for amir, darpan, shavez and manoj (a walk-only secret and user store).
- `walks_old_s446.py` + `plan_old_s446.py` — S437's and S436's walks on the board and S444's walk, re-run.
  - Each runs twice: unadjusted on the box as it is (the baseline), and adjusted on the box + S446.
  - Each adjustment is named in the script (D1, D2, B1–B3).
  - A red is accepted only if it is in the walk's ACCEPT list and is red on the baseline too.
- `apply_s446.py` — the data step and the figures.
- `install_S446_AMIR_STAGES_BILLS.sh` — gates → pins → build → compile both pythons → walk → earlier walks → (DRY stops here) → lock
  check → backups → place → md5 read-back → restart clinic-finance → health → data step; restores on red.
- `DUTY_MAP.md`, `DUTY_MAP.json` — the copies placed in `claude_code_briefs/`.
- `medical/` — the reader fix, its patcher, its proof and the manifest for Drive `ToMedical\_kit`.

## Run
```
cd /root/deploy/repo && git pull --ff-only && bash deploy_kits/S446_AMIR_STAGES_BILLS/install_S446_AMIR_STAGES_BILLS.sh
```
(holding `/root/deploy/.claude_code_build.lock` with owner `S446_AMIR_STAGES_BILLS`; `DRY=1` places nothing).

## Undo
Put back `/root/finance/<file>.bak_S446_<from8>` for the six files, restart `clinic-finance`, check healthz 200 and read the md5s back.
The three settings rows and the two tables are harmless to the old files. `finance.db.bak_S446_<stamp>` is used only if the data step
must be reversed.

On the medical PC: deliver the S397 `marg_txt.py` (38d85298) with the old manifest line.
