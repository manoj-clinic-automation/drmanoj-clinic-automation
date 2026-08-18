# HANDOFF RUNBOOK — 05 Aug 2026 — Session 151 close → Session 152 open — v89

## §0 WHAT HAPPENED (S151 — FULL EOS; one new live VPS file)

1. **July 2026 salary processed end-to-end.** Inputs computed twice independently (PDF coordinate-parse,
   24/24 self-check; then the new VPS script from raw punches — Present/Absent matched 12/12, grace deltas
   hand-reconciled: Sukhveer 93→74, Sandip 533→497). Shivani: 4 evening covers × Rs 200 (not raw minutes);
   punch-out rule born. July's Deduction/Incentive columns are PREVIEW ONLY (policy starts August).
2. **`staff_master.csv` rebuilt + live** (VPS md5 `f8f3a239…`): 12 staff, all salaried (Darpan, Arjun in),
   Sandip corrected to 09:00–21:00, Darpan split-shift parses to 09:30–21:00. Workbook home =
   `D:\clinic_salary\` (non-repo; F-31). Old OnTime salary folder archived-then-deleted after the workbook
   inside it was proven canonical by rebuild-and-compare.
3. **`att_month_report.py` LIVE on VPS** (md5 `c9251988…`; WinSCP → md5 → selftest PASSED → July dry-run
   cross-checked). Read-only; imports `att_core`; D249 policy layer; writes only dated
   `salary_inputs_YYYY-MM.csv/.html` (A4). Monthly routine: one command on the 1st.
4. **D249 punctuality/incentive policy LOCKED, effective 01-08-2026** (grace 10 → marks; >30=2 marks;
   3 marks = ½-day; >60 review; band incentive with Aug–Sep ramp ≤5/≤8 then ≤2/≤5; Rs 200 cover needs
   punch-out). Bilingual 10-point notice drafted in-chat — **owner still to print/sign/post**.
5. **D250 Darpan systematised**; `Darpan_Loan_System_v2_3.xlsx` delivered (md5 `dd6689e1…`), numerically
   verified (flat-interest amortisation, skip capitalisation, FY skip flags, partials). May/Jun-2026
   pre-entered; **Apr-2026 + Jul-2026 cells = owner's**. v1 (reducing-balance) analysed and discarded.
6. **D251 roadmap locked** (Phase 1 live · Phase 2 Sheet+gspread with key rotations · Phase 3 portal tile
   with D223, after Phase 2).
7. 🔴 **F-46 raised**: salary column printed in-chat twice (raw diff; header-keyed mask beaten by a title
   row). **Rule: whitelist-only printing from salary-bearing files.** Applied same session.
8. **Attendance dossier → v1.1** (att_month_report pinned; addendum). **Notion NOT updated** — connector
   absent this session; carry. Docs delivered by zip for drag-drop (Drive writes still fail).

## §1 MENTAL MODELS (carry unchanged + one new)

- Manifest wins on canonicity; Register wins on NOW; Archive holds history verbatim; no canonical doc is a
  delta (D202/D247). Expected values from artefacts (D172); a filename is not provenance (D188); presence
  by hashing, absence by exhaustion (D201). One writer per table. Live VPS is canonical (D160).
- **NEW (S151): the salary stack is three layers** — biometric truth (VPS: punches → engine → monthly
  report, read-only), money truth (workbook at `D:\clinic_salary`, owner-edited, never in git), judgment
  (owner: outstation conversion, disputes, perks). Automation may move computation between layers but never
  moves JUDGMENT off the owner, and never lets two writers share a table/tab.
- **NEW (F-46): from salary-bearing files, print whitelisted columns only** — never mask-by-exclusion,
  never raw diffs/dumps.

## §2 LIVE BACKLOG (ordered)

1. **TOP: Darpan module integration** — move the 5 sheets of `Darpan_Loan_System_v2_3.xlsx` into
   `Salary_System_2026.xlsx` (group Move/Copy; refs are internal-only), owner fills openings check +
   Apr-2026/Jul-2026 tracker cells; print + sign the Schedule Card.
2. Owner: post the D249 bilingual notice (August stands as ramp month 1 only if posted this week).
3. Commit `att_month_report.py` to repo `attendance/` (GitHub Desktop; message drafted S151); then
   **Attendance dossier folder-digest re-pin** against the 11-file folder.
4. S149-owed installs: project-knowledge doc-set confirmed installed at S151 Phase 0 (hashes matched) —
   remaining: run `Repo_Trim_Phase2_S149.ps1`; rule on the 12 held `docs/` files.
5. `clinic_writer/` folder digest recompute + re-pin (owed since S150 install).
6. `wa_approve` nohup → systemd (overdue). 7. Key rotations (overdue — bundle with Phase 2 per D251).
8. WABA sends blocked on Lokesh (D120). 9. Insight Harvest items 1/2/3/10 (D241). 10. D223 portal gist
   tile (+ Phase 3 salary tile rides with it). 11. Notion S151 catch-up when connector present.

**Next free: D252 · F-47 · Session 152.**
