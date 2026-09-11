# S238 BUILD BRIEF — what was built, what is live, what is next (S238 close, 11-Sep-2026)
**The one document to read instead of the fourteen S238 papers.** `START_HERE_SESSION_239` carries the
full context for Docterz, Sanjeevni, the Marg vendor and Amir; this brief is the as-built record.

## 1 · The staff-money chapter — built and installed (all from one owner line each, all read back GREEN)
| kit | what it did | live pin after |
|---|---|---|
| `S238_LEDGER_RECONCILE` | the reconciler (dry-run default, `--apply` separate, backup first, rows via `append_ledger()`) | `/root/staff_ledger_reconcile/ledger_reconcile.py` v1.0 |
| `S238_CLOSE_GUARD` | close only from the 1st of the next month · refuses while PENDING rows · `close_report_<m>.txt` names what was not collected (F-396) · duplicate refused at entry (F-400) · SPECIAL needs narration | `/root/staff_ledger.py` v3.7 **`49b13f42d3a923c5bb2e34230c80e6e8`** |
| `S238_MONEY_SHEETS` · `S238_SHEET1_PRINT` (tombstone) | the month-end money sheets | superseded by V3–V5 |
| `S238_SHEET2_REVIEW` | Sheet 2 review; **improve_pct 30 → 20** via audited `save_settings` | salary_policy v1.9 `e848c81f…` |
| `S238_RECONCILE_AUG2` | reconciler **v1.1** — `month_advances` kind finds a person's month advances at run time (survived Sukhveer's reversed/re-entered `…ca19`); `--apply` wrote **6 rows**; `august_nets.py` read-only | reconciler v1.1 (kit `d797f2b4…`) |
| `S238_SHEETS_V3` | Sheet 1 month summary with no-punch dates + Sundays + late-fine total + OT payable; holds write-off/deduction column; "recovered from AUG salary" | — |
| `S238_SHEETS_V4` | OT paid (2× own minute-rate on the report's `ot_min`); OT threshold **setting, default OFF** (15 min); Sheet 3 landscape, Sheet 4 portrait; `&amp;` double-escape fixed | — |
| `S238_SHEETS_V5` | Shivani's cover rule verified by the OUT punch (D450) | salary_policy **v1.12 `bc7b7ffc1d336459ec41c5f6e527bad0`** |
| `S238_STEP0_V2` | Step 0 verify sheet condensed to **one A4 page** (3 date slots per row, both paragraphs removed) | staff_register **v0.18 `b9a72d1a35f3a71f2cbb518b4fb7698c`** |

**Settings now (audited):** improve_pct 20 · ot_pay 1 · ot_threshold_on 0 · ot_daily_min 15 · cover_end
21:00 · cover_auto_from 17:00 · dates_only_staff "Amir Sohail" · collect_now_pct 25.

**Backups on the VPS:** `*.bak_S238_SHEET2_REVIEW_20260910_220730` · `*.bak_S238_SHEETS_V3_20260910_232028`
· `*.bak_S238_SHEETS_V4_20260911_054145` · `*.bak_S238_SHEETS_V5_20260911_062050` ·
`staff_register.py.bak_S238_STEP0_V2_20260911_063813` · `staff_ledger.py.bak_S238_CLOSE_GUARD_20260910_183746`
· ledger `/root/staff_ledger/ledger.jsonl.bak_reconcile_20260910-232003`.

**Validated:** `project_recovery` (the overlapping-advance projection) simulated against the real
`close_month` Sep–Jan — **19/19 match**.

## 2 · Docterz Day Revenue — made live again
`S238_DOCTERZ_LIVE` rev 2 (`ea3e3ef9…`): made `/root/finance/logs/`, ran the catch-up (73 days, to
10-Sep), backups `/root/finance/finance.db.bak_S238_DOCTERZ_LIVE_20260911_065202` / `_065430`.
`S238_DOCTERZ_SCHEDULE` (`77fbaf36…`): four flock-guarded lines (`30-50/10 9` · `*/10 10-11` · `0 12` ·
`40 13,19`), 49 other crontab lines unchanged by count; backup
`/root/finance/logs/crontab.bak_S238_DOCTERZ_SCHEDULE_20260911_070504`.

## 3 · The owner's rulings this session (full text: Archive §S238)
D447 close only after the month ends, only by hand · D448 the hold model · D449 OT paid, threshold
setting default OFF, no closing cap · D450 Shivani's cover rule · D451 the Step 0 sheet and Amir
dates-only · D452 a month's advances come off that month's salary · D453 the Docterz schedule ·
D454 Docterz auto-pickup, tracker stays on the PC.

## 4 · Next, in order
1. **August lock** — his, later on 11-Sep (Step 0 → Fix-absents → Sheets 1+2 → 3+4 → Lock). First lock ever (F-407).
2. **Docterz Ask 1 (watcher) then Ask 2 (clinical report)** — `START_HERE_SESSION_239` §3.
3. **Sanjeevni Rung 1 backfill → T1 → Rung 2** — §4. **Marg vendor + Amir exports** — §2b, §5.
4. Staff-money remainder: statement page rewrite · loan-restatement row · actual-paid on the lock ·
   the register's advance deduction reading only the ledger's month rows (D349).

## 5 · Traps this session paid for
- **F-414** probe copies read no settings (BASE-relative). **F-415** a cron redirect into a missing
  directory kills the command silently. **F-416** "no sheet" is not "failed". **F-417** a static record
  cannot survive a reversed-and-re-entered row — find at run time. **F-418** double HTML escaping in a
  shared header. **F-419** Docterz 07-Sep ₹0 / 08-Sep missing, open.
- The device shell mounted nothing all session (Windows update of 8-Sep); stage → container → commit →
  verify md5 worked every time.

*S238_BUILD_BRIEF · 11-Sep-2026.*
