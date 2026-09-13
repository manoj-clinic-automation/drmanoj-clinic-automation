# S243_CA_AND_NUMBERS -- two owner rulings of 13-Sep-2026

**Ruling A (the chartered accountant):** no UPI ↔ cash correction is to be made in Marg any more --
correcting a bill's payment mode re-opens a closed sale bill to unauthorised edits. The system keeps
the record and it becomes part of the **monthly accountant pack**.
**Ruling B:** "full phone numbers everywhere, including the returns desk."

Built 13-Sep-2026 (S243), offline, on the 13-Sep live capture; walked live-shape (61/61 stacked on
SCREEN_FIXES + DARPAN_KAL, 59/59 on the live bytes alone, 59/59 on an installed mock tree); installer
mock-tested 5/5.

## Install (the owner's double-click publishes; then ONE line on the VPS)

```
bash /root/deploy/repo/deploy_kits/S243_CA_AND_NUMBERS/install_S243_CA_AND_NUMBERS.sh
```

**Order:** after `S243_SCREEN_FIXES` and `S243_DARPAN_KAL` (their gates accept only the older pins;
this kit's gate accepts the pin **or** their marks -- the patcher's count==1 anchors are the guard, and
the ACTUAL from-pin is recorded in each `.bak_S243_<pin8>` name and the printout).

| file on the box | from-pin | to-pin (predicted) |
|---|---|---|
| `/root/finance/finance_app.py` (patched) | `f002defb…` or SCREEN_FIXES/DARPAN_KAL-marked (`f93f7430…` after both) | `d20a44e1…` from f002defb alone · `ece2a82b…` after both siblings |
| `/root/finance/finance_ui/finance_approvals.html` (patched) | `cc349dd0…` or DARPAN_KAL-marked (`7dbb5e56…`) | `e1e40ae7…` alone · `520ff235…` after DARPAN_KAL |
| `/root/finance/returns_desk.py` (patched) | `dface15b…` | `dffbe8fb…` |
| `/root/finance/returns_desk.html` (patched) | `77e754e9…` | `4d6f2161…` |
| `/root/finance/darpan_corrections.html` (REPLACED, full file) | `26b1defe…` | the kit's bytes (SUMS.md5) |
| `/root/finance/accountant_upi_cash.py` (NEW) | -- | the kit's bytes (SUMS.md5) |

Gates: SUMS + KIT_ID → pins/lineage → patcher `--selftest` on the live bytes → all four patches to
`.new` before anything is placed → `py_compile` → place with backups → import smoke under the unit's
environment (`accountant_upi_cash` must be a registered blueprint) → restart → healthz within 20 s.
Any RED → every file restored, the new file removed, service restarted. Re-run → ALREADY INSTALLED.
`padwriter.py` (already at `/root/finance`, `e7546afe…`) writes the .xlsx; if ever absent the download
answers 503 and the page/JSON still work.

Rollback by hand (one line; `<pin8>` = the from-pins the installer printed):
```
\cp -f /root/finance/finance_app.py.bak_S243_<pin8> /root/finance/finance_app.py && \cp -f /root/finance/finance_ui/finance_approvals.html.bak_S243_<pin8> /root/finance/finance_ui/finance_approvals.html && \cp -f /root/finance/returns_desk.py.bak_S243_dface15b /root/finance/returns_desk.py && \cp -f /root/finance/returns_desk.html.bak_S243_77e754e9 /root/finance/returns_desk.html && \cp -f /root/finance/darpan_corrections.html.bak_S243_26b1defe /root/finance/darpan_corrections.html && systemctl restart clinic-finance.service
```

Prove on the box after install (builds its own db; touches nothing live):
```
FIN_APP=/root/finance/finance_app.py FIN_MODS=/root/finance /root/wa/venv/bin/python3 -B /root/deploy/repo/deploy_kits/S243_CA_AND_NUMBERS/walk_ca_and_numbers_s243.py
```

## RULING A -- what changes

**1 · The monthly accountant report (NEW, English, checker only) -- `accountant_upi_cash.py`**

| URL | what |
|---|---|
| `/finance/accountant/upi-cash` | → this month |
| `/finance/accountant/upi-cash/<yyyy-mm>` | the page: month picker · **Section A** per bill -- date, bill, amount, bank ref (RRN), bank time, matched-on, Darpan's answer, "corrected in Marg before the ruling" (the historic ticks) · monthly total · **Section B** bills whose payment mode changed on a re-import (`mode_change_log`, the hub card's data) · **Section C** the day-level books-vs-bank difference (`marg_correction`, the S195 checklist rows, now history) |
| `…/<yyyy-mm>?print=1` | the print view (prints itself) |
| `…/<yyyy-mm>.xlsx` | three-sheet workbook via `padwriter` (stdlib) -- `UPI_booked_as_cash_<yyyy-mm>.xlsx` |
| `/finance/accountant/api/upi-cash/<yyyy-mm>` | the same as JSON |

Read-only. Sources: `upi_match status='cash'` (bank_match.py's per-bill verdict), `darpan_correction`,
`mode_change_log`, `marg_correction`. Any table absent → that section is empty, never an error. No
patient name or number appears on the report (walked).

**2 · `/finance/darpan/corrections` stays, as a read-only RECORD.** Full-file replacement of
`darpan_corrections.html`: the header reads **"Ab Marg me sudhaar nahi karna hai — yeh record
accountant ke liye rakha jata hai"** (Devanagari beneath), the "done in Marg ✓" button is gone, the
historic ticks show as "pehle sudhaara", the counters read "is mahine ke bill (record)" / "ruling se
pehle Marg mein sudhaare gaye". The route, `api_corrections` and `api_tick` are untouched and still
answer (walked: 200 / 409 / 404). The owner block (ledger check, transfer) is untouched and gains the
report link.

**3 · Health.** The red/amber **"Correction checklist"** work item is gone. In its place an ⓘ line
under *Worth knowing*: **"Cash → UPI reclassifications — N bill(s) this month, ₹X — the bank proves UPI,
Marg rang cash"**, hint "Kept for the accountant report (no Marg correction — the CA's ruling)", the row
opening the report. **"Cash / UPI split"** is likewise `info` (recorded, not corrected). `HEALTH_LINKS`
for both rows point at the report; the app's own selftest expectations (`_hmap`, the "Open the
checklist" wording) follow. `_correction_rows()` is no longer called from the health page, so the
S195 checklist table is no longer re-synced on every render; `/finance/marg-worklist` and the
`/finance/api/marg-corrections*` routes are kept as they were.

**4 · Hub.** The **Cash ⇄ UPI · Reclassified bills** card carries the report link; the tab strip gains
**Accountant ↗** beside Corrections ↗.

**5 · Freshness.** No leg watches corrections (S230 `legs.json` and the S240 add-list read at build) --
nothing to turn informational.

**Not touched, by design -- for the close:** `tile_grants.json`. The owner said Darpan's *Corrections*
tile can go; `S243_REPORTS_TILE` (built in parallel, producing v13) owns that file, so **remove
"Corrections" from Darpan's grants there**, not here. The tile, if left, opens a harmless read-only page.

## RULING B -- where full numbers live today, and what this kit does

**On the VPS today (from the 13-Sep capture, read not assumed):**

| store | what it holds |
|---|---|
| `patient_ref.mobile` | **the full number** -- lazy column added by `finance_patient_sync.py` (owner's ruling of 31-Aug, "reverses F-86"), filled nightly from the clinic PC's `Patient_Master_Join.xlsx` in `/root/wa/followup-inbox/` (freshness leg "patient sync"). Present for every patient the tracker master knows; `mobile_fp` (salted fingerprint) and `phone_last4` beside it. |
| `marg_push_staging.parsed_json` (`lines_csv`) | the full `mobile` column **while a push is pending** -- `/root/finance/marg_report.py` (f9370dde, S220 F-282b) writes `phone_last4` AND `mobile`; `finance_ingest.adapter_csv` reads it into memory for the D355 ladder and **strips it from the stored raw**; `parsed_json` is nulled at apply. With S243_AUTOAPPLY that window is seconds. |
| `sale_item`, `sale_line_item`, `mi_sale_line`, `sale_bill` | **no phone at all** (never had one) |
| `sale_item_review.raw_text` | last-4 only (mobile stripped at parse) |

Note the parent brief's pointer -- "`marg_report.write_lines_csv` masks to last4 ~L472-497" -- describes
the **other** copy, `/root/marg_ingest/marg_report.py` (the S240 PHI-free lane feeding `sale_bill`);
the copy the finance app imports carries the full number since S220.

**Upstream:** the raw `SALE_BILLWISE_DETAIL` exports on manojz / the Drive mirror ("`<phone> <NAME>
<clinic id>`" in the description column; the server deletes them after read) and the tracker master
workbook itself.

**Built here (2 files, both on-box patches, anchors count==1):** the returns desk's `/api/search` now
returns `mobile` -- the full number from `patient_ref.mobile` where the column exists and is filled,
`""` otherwise -- and five or more typed digits search the full number (`mobile LIKE '%digits%'`); two
to four digits still search the last four; name/clinic-id unchanged. `returns_desk.html` shows the full
number in the picker and on the chosen patient's line, `***last4` where there is none. Walked with a
placeholder number (all zeros -- the only ten digits the F-185 gate admits) and with the `mobile` column
absent altogether (an older db): the desk keeps answering. The jaankari lists already showed the full
number through `_rd_mobile()` (D363); they are unchanged.

**Phase 2 -- needs the ingest change (designed, NOT built):** bills whose clinic id is **not** in the
tracker master get a `patient_ref` row from `finance_ingest.resolve_patient()` (line ~371, name only),
and a walk-in bill has no row at all -- so their numbers are never kept, though `ln["mobile"]` is in
memory at exactly that point (`ingest_day`, the accept path ~L774-790). The smallest change is one line
in `resolve_patient()`/`resolve_patient_checked()`: on INSERT (and on UPDATE when `mobile` is NULL) write
`ln["mobile"]` (ten digits, `marg_report.full_mobile()` already normalises it). That is the money path of
`finance_ingest.py` -- a change with its own kit, walk and owner OK. Historical rows: a separate backfill
job over the archive, not built. F-185 stays absolute: nothing here puts a number in the repository.

**Check on the box (count only, no numbers printed):**
```
/root/wa/venv/bin/python3 -c "import sqlite3;c=sqlite3.connect('/root/finance/finance.db');print(c.execute(\"SELECT COUNT(*), SUM(mobile IS NOT NULL AND mobile<>'') FROM patient_ref\").fetchone())"
```

## Files

| file | role |
|---|---|
| `accountant_upi_cash.py` | the monthly report module (page, print view, .xlsx, JSON); `python3 accountant_upi_cash.py` runs its offline selftest |
| `darpan_corrections.html` | the read-only record page (full-file replacement) |
| `patch_ca_and_numbers_s243.py` | on-box patcher for the four live files, `--selftest <files>` |
| `install_S243_CA_AND_NUMBERS.sh` | the installer |
| `walk_ca_and_numbers_s243.py` | live-shape walk (real Flask on the patched app, real sqlite, seeded month) |
| `mock_install_ca_and_numbers_s243.sh` | the installer's five ROOT proofs |

## Doubts / open

* The app's own `finance_app.py --selftest` cannot run on an empty db (IndexError at its "days" check --
  unpatched file, same result), so the walk asserts its two moved expectations by text instead.
* "Cash / UPI split" turned `info` as part of "the Marg — corrections pressure must go"; if the owner wants
  that row to stay a warning, it is one word in the patcher (`U_NEW`).
* Whether `patient_ref.mobile` is actually filled on the live box depends on the PC-side master export
  carrying the `mobile` column; the one-line count above answers it. The desk degrades to last-4 either way.
