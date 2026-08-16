# S183_M2a — turn ON the Marg pharmacy feed (code + config)

**Session 183 · 16 Aug 2026 · installs code + a config migration · NO patient data in this kit**

---

## What this installs

| # | Artefact | Change |
|---|---|---|
| B1 | `/root/finance/marg_report.py` | **replaced** — now reads `.xlsx` as well as `.xls`. The `.xls` path is **byte-for-byte unchanged** (proven). |
| B2 | `finance.db` migration `S183_marg_map` | **7-field column map** for `(medical, marg_export)` + source set **active=1**. Additive, atomic, reversible. Moves no money. |
| B3 | `/root/finance/marg_backfill.py` | **v1 → v2** — writes BOTH `sale_item` (bills) AND `sale_line_item` (drug lines) per day. |

**No service is restarted** — nothing on the box imports `marg_report` (only the
standalone backfill driver), so the running finance app is untouched. **`openpyxl`
is already present** (`finance_upi.py` uses it); the installer checks anyway.

## Why B1 was needed

Six of your eight April→August exports are genuine Excel-2007 `.xlsx` (someone
opened a Marg `.xls` in Excel and saved it). `xlrd 2.x` reads legacy `.xls` only,
so those six were refused. The new reader identifies the format by content, not
by name (D188), and reads an Excel-saved file **byte-identically to the original
`.xls`** — proven by converting a known-good `.xls` to `.xlsx` and parsing both to
identical day-totals, bill lines and item lines.

## How it was proven offline (nothing assumed)

- `.xls` path **byte-for-byte unchanged** — old vs new parser, identical output (Regression 1).
- `.xlsx` reader **faithful** — a `.xls` round-tripped to `.xlsx` parses identically (Regression 2).
- Parser selftest **38/38**; all **8 real files** parse clean.
- Migration applies, verified (marker + active=1 + 7 map rows), idempotent.
- v2 driver on real files: **money (`day_line`) untouched**, **idempotent** (re-run
  never duplicates), both identity regimes handled (July 87%: 277 attributed to 183
  patients + 77 review + 12 returns; April 0%: all to review) — and it **caught and
  we fixed** a false-abort where the row-count guard didn't allow for Marg's own
  zero-net procedure write-offs (F-87 lesson: the offline test found it).
- Installer rehearsed against a throwaway box: installs clean, the **F-97 currency
  gate refuses** a live `marg_report.py` that isn't the expected `28b47d44…`
  (touching nothing), honest red restores from `.bak`.

## Install

```
bash /root/deploy/vps_deploy.sh S183_M2a
```

Then confirm it green with the pin verifier from earlier this session:

```
python3 /root/deploy/verify_live_pins.py
```

(It will show `marg_report.py` DRIFT — expected, because the Register still pins
the old md5. Its new md5 is `829f4344df6e086510bb0fb6112ecb77`; I'll correct the
Register at close-out, same as the nine rows earlier.)

## After install — running the backfill (owner-driven, PHI never touches git)

The eight export files carry patient names and phone-last-4 (F-31/D320), so they
travel **PC → VPS directly**, never through the repo.

1. Put the eight files on the box, e.g. via WinSCP into `/root/finance/backfill_in/`.
2. For each file, **dry run first**, read the survey, then apply:

   ```
   /usr/bin/python3 /root/finance/marg_backfill.py /root/finance/backfill_in/<file>
   /usr/bin/python3 /root/finance/marg_backfill.py /root/finance/backfill_in/<file> --apply
   ```

3. The driver backs up `finance.db` before the first write, refuses an inactive
   source or a mismatched column map, and aborts on any row-count anomaly.
4. When all eight are done, **delete the files from the box** and confirm.

**What the backfill will and will not do (measured on your data):**
- It fills `sale_line_item` (drug lines) and `sale_item` (patient attribution).
- It **cannot** change any day total or any cash/UPI figure — those are `day_line`
  (Darpan's declaration), a separate table the attribution can never move.
- **April → mid-June has no patient identity**, so those bills land in the review
  queue as "no patient identified" — correct, but it means a large legacy review
  backlog. That is a decision to note (filter review by date, or leave as-is); it
  affects no money.

## Still owed after this (the daily live flow, not the backfill)

The watcher that pushes the morning export PC→VPS (B5), the home-medicine cash
deduction (B4), expenses/advances/deposits (B6), the cash-position view (B7), the
bank-visit trigger (B8) and the returns display (B9) — all in the design doc
`S183_Sanjeevni_Daily_Cash_Design_and_Marg_Findings`. This kit is the data
foundation they build on.

---
*S183_M2a · built + proven offline · Session 183*
