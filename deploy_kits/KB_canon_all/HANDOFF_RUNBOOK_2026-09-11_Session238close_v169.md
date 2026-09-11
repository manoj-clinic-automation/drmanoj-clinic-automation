# HANDOFF RUNBOOK — v169 — at the S238 close, 11-Sep-2026

**Supersedes v168 (S237 close).**

## 0 · WHAT HAPPENED

Two calendar days, one compaction, twelve kits in the repository — every one that went live installed by the owner from one
line and read back GREEN (`S238_SHEET1_PRINT` a tombstone). **The S237 staff-ledger worklist is done in code:** the reconciler, the close guard
(close only after the month ends and only by hand — D447), the six August corrections written. The
month-end sheets were rebuilt five times from the owner's own prints and now carry his rulings on the
hold (D448), overtime (D449), Shivani's cover duty (D450), Step 0 on one A4 page (D451) and advances off
the month they were taken (D452). **Docterz Day Revenue was dark from 03-Sep because a cron redirect
pointed into a missing directory (F-415)** — live again to 10-Sep, now on his timetable (D453).
**Six findings, F-414 … F-419; two are the assistant's. Eight decisions, D447 … D454.**

## 1 · WHERE THINGS STAND

**Canon:** Archive **v1.85** · Register **v5.88** · Fault Register **v2.70** (F-0 … F-419) ·
**START_HERE_SESSION_239** · `S238_BUILD_BRIEF` · `CANONICAL_MANIFEST.md` · `MD5SUMS_ALL.txt`.
Next free **D455 · F-420**.

**Live pins (read back):** `/root/staff_ledger.py` v3.7 `49b13f42…` · `/root/staff_register/salary_policy.py`
v1.12 `bc7b7ffc…` · `/root/staff_register/staff_register.py` v0.18 `b9a72d1a…` ·
`/root/staff_ledger_reconcile/ledger_reconcile.py` v1.1 `d797f2b4…` · `/root/finance/docterz_ingest.py`
`80bf760d…` (unchanged, now scheduled).

**August:** ready to lock. **The lock is the owner's, later on 11-Sep**, after staff fill Step 0 and he
fixes punches (Darpan −4,443.82 until then). First month ever locked (F-407).

## 2 · WHAT TO START ON

**`START_HERE_SESSION_239` — it carries the full context.** In order: §2a has August been locked · §2b
Amir's Marg exports (**none on 8, 9, 10-Sep**, measured at the close) · §2c the Docterz 09:30 proof and
F-419 · then **§3 Docterz** (Ask 1 the auto-pickup watcher, Ask 2 the clinical data report — the new
chat is for this) · **§4 Sanjeevni** (Rung 1 backfill → install T1 → Rung 2) · **§5 the Marg vendor**
(the Excel export still 9 columns, names still cut at 20/29 — ask whether the message to Ram Singh went).

## 3 · THE TRAPS THIS SESSION EARNED

- **A probe copy of a `BASE`-relative module reads no settings (F-414).** Re-point every BASE path, or
  the probe reports changes that are not there.
- **A cron redirect into a missing directory kills the command silently (F-415).** An installer that
  writes a redirect makes the directory and proves one run landed.
- **"Nothing to read" is not "failed" (F-416).** Name the benign reason and accept only it.
- **A reconciler states intent, not row ids (F-417).** The ledger moves under it.
- **Escape once, at the boundary (F-418).**
- **The device shell mounted nothing all session** (a Windows update of 8-Sep). Stage → container →
  commit → verify md5 from inside the kit folder. Worked every time.
- **One line per copy block, machine named above it.** The owner ran a `.bat` path in the VPS shell and
  once glued two commands; both were the hand-over's fault.

## 4 · THE BOUNDARY

**Clinic screens that changed behaviour this session:** the staff-register month-end flow and sheets
(`https://attendance.dr-manoj.in/register/salary/flow?ym=2026-08`), the ledger's close step (now
refuses before the 1st of the next month), and the Day Revenue screen (moving again). **Nothing on
manojz, the medical PC or the tracker PC was changed.** Marg is never written to.

*HANDOFF_RUNBOOK v169 · S238 close · 11-Sep-2026.*
