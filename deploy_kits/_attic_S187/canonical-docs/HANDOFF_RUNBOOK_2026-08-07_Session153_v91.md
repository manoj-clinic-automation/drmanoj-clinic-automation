# HANDOFF RUNBOOK — 2026-08-07 — Session 153 — v91

## §0 — WHAT HAPPENED (S153, FULL EOS — build session)

The backlog TOP (attendance report build, deadline 01-09) was executed **end-to-end and beyond spec** in one long session:

1. **Notice v6 FINAL** (`b29dfa1317024d1d622d79d6de6f5c17`, PDF `ca8216b3…`) — owner iterated v5→v6: late bands stated per episode (10–29/30–59), ≥1 hr softened from half-day-absent to 2/3 marks (Option B), Option-B slab deductions (stick starts only after the incentive limit), OT expanded into point 7 (double rate, by minutes, approval+punch), Sunday swap needs register entry + both signatures + doctor countersign, leave register live 06-08-2026. Two-week-warning line ruled OFF the poster. One A4, signature merged to one line.
2. **Rate card v2** (`8e9cf646…`) — ÷30 basis, Arjun excluded; day-rate / half-day / per-minute / 2× OT columns, live formulas.
3. **`staff_master.csv` v2 INSTALLED** (`3b1ebcb1e339fdcdb8b47389ee206108`) — +`sunday_group` (A: Shivani, Awdhesh, Pravesh, Darpan · B: Alisha, Shavez, Ranjeet, Sukhveer · C: Sandip, Vikki, Surendra · ARJ) +`minutes_exempt` (Arjun). VPS backup `staff_master_BACKUP_preS153.csv`.
4. **`att_month_report.py` v2→v2.5** — six selftested versions (40+ checks each), additive on the frozen `att_core.py`. **v2.4 `608f2a90…` is INSTALLED and July-verified on the VPS; v2.5 `e64cad19…` is delivered but NOT yet installed.** Features: policy engine in the report (bands, grace cap, Option-B, roster incl. 5th-Sunday, fines, habitual tracker, Arjun exemption), two-pass informed-flag loop (`review_YYYY-MM.csv`), landscape **date-grid HTML** with per-cell punch times and L/E/OT markers, **three-tier early departure** (artefact ≤30-min pair · auto ≤120 · EARLY_BIG sheet-ruling with deductible ₹), collapsible per-staff money log (screen-only), bilingual policy legend, 2-sheet print; v2.5 adds owner legend wording, adjacent OT columns, **Incentive Rs (FULL = 1 day salary, HALF = half)** and a **signed colored Net Rs** (= incentive + OT − deductions; OT in by default).
5. **Findings:** **F-47** double-punch artefact (accidental second morning punch read as 540–722-min early departures across 6 staff; the three-tier fix). **F-48** shadow-write (a create_file race pre-applied a patch; resolved by full diff-audit vs last verified md5 — all in-scope). July analysis: cross-foots exact ×2 runs; Alisha's "midday exits" were late-arrival double punches; only two genuine EARLY_BIG items all month (Pravesh 28-07, Shavez 12-07); **staff essentially never punch out** (Sukhveer 31/31) — OT can never pay without out-punch; coaching line attached to notice posting.
6. **D256 minted** (Register index one-liner; full text Archive §S153). **Sept-strict correction** applied: notice (strict from Sep) overrides the S151 code's Aug+Sep ramp.
7. **July 2026 = diagnostic only.** First billing month: **August, run ~01-09.**

Fault codes: F-47, F-48 minted. No SOP/surveillance-scope changes (report layer is read-only, on-demand, monitored by nothing and touching no service). No incident.

**State corrections this session:** the "Notion connector present" note at Phase 0 was WRONG — no Notion tools existed in the session; catch-up now spans S151–S153. The wa_approve systemd verify-first task remains untouched.

## §1 — MENTAL MODELS (delta only)

- **The attendance stack is now three layers:** frozen engine (`att_core.py`, presence + punch pairs) → policy report (`att_month_report.py`, all money math, owner-tunable constants at top) → the human loop (review CSV vs the physical register + the EARLY_BIG ruling sheet). Judgment never left the owner: OT candidates and EARLY_BIG never auto-pay/auto-deduct.
- **Punch pairs must be classified before money math** (F-47). A punch count is not a departure record.
- **The posted notice is the staff-facing law** — where code and notice disagree, the notice wins and the code is corrected (Sept-strict).
- **staff_master.csv is now roster-bearing** — the report reads `sunday_group`/`minutes_exempt` itself; the frozen engine ignores the new columns (DictReader-additive).

## §2 — LIVE BACKLOG (ordered)

1. **Install v2.5** (`e64cad19d135618dec1413553e6bdc80`): WinSCP overwrite → md5 → `--selftest` → rerun `2026-07` → browser check. *(First action.)*
2. **Owner:** print/sign/post **notice v6**; announce punch-out coaching (OT needs out-punch); early departures now logged in the physical register.
3. **Workbook shift-time reality pass** before the Aug run: Sandip start (S151 open), **Shivani end** (OT300/318 pattern), **Alisha start** (near-daily L26–L81), confirm all 12; then **add `sunday_group` + `minutes_exempt` columns to the Staff Master sheet and `build_staff_master.py`** (else the next rebuild drops them), rebuild → WinSCP → md5.
4. **August run ~01-09** (first billing): run → edit `review_2026-08.csv` vs register → rerun → rule EARLY_BIG on the sheet → subtract Darpan outstation days → enter workbook. July's `review_2026-07.csv` needs no action (diagnostic).
5. **D255 maker-checker module** before the 01-10 processing (rate inputs now largely exist: OT + incentive defined; confirm any remaining rate-card rows + maker identity).
6. ~~Attendance dossier v1.2~~ **DONE at S153 close** (`Attendance_System_Dossier_v1_2_S153.md`, `bf19179181c553777e4cc8e3834bc754`). Still carried: folder-digest re-pins (attendance at repo commit; clinic_writer).
7. Phase-2 repo trim ruling (12 held docs) — carried.
8. `wa_approve` systemd — **verify `systemctl status` first** (records conflict) — carried.
9. Overdue key rotations — carried.
10. WABA sends blocked on Lokesh — carried.
11. **Notion catch-up S151–S153** (tools absent three sessions running).
12. clinic_writer Hindi spellings — carried.
13. **Cold kit due** (Register/Archive bumped; last kit ~S150) — build at next EOS or on request.
14. Parked/deferred: Insight Harvest D241 items, D223 gist tile, Docterz export migration (D243).

## §3 — REPO

Commit owed: `attendance/att_month_report.py` → v2.5 (`e64cad19…`) once installed. staff_master.csv NEVER goes to repo (F-31).

*Runbook v91 supersedes v90. Next session: 154. Next free: D257 · F-49.*
