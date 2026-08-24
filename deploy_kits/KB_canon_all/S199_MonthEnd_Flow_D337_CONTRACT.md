# D337 — THE MONTH-END FLOW & LOCK DESK (S199 · owner-specified · SIGNED via session rulings)

**The owner's flow, verbatim spirit: sheets generated for staff viewing first → his modifications
through the system → both sheets approved → final salary computed and processed. Five-minute close.**

## The pack (machine data)
- **Sheet 1 · Attendance** (`/register/salary/flow/sheet1`): the month grid in two half-month
  blocks, arrival time visible in every cell (amber 11–59 late, red ≥60; out-punch on hover),
  L approved leave · A absent · * approved present-request; the RUNNING DAY EXCLUDED (F-176);
  summary splits Absent (excl. sanctioned) from Leave; print version carries the staff-remark
  column. Caption: month in words + "MACHINE DATA — for review".
- **Sheet 2 · Money** (`.../sheet2`): advances this month · current open loans (as-of-today;
  "due this month" only on the current month) · improvement holds · ALL fines/leaves/night-duty
  per staff. **Darpan = a separate page** (+ outstation nights/credit). No totals rows.
- **Doors everywhere** (the S198_H1 pattern): every fixable cell links to its exact fix point
  (register day page, present-request review, ledger statement/advances); corrections happen in
  the apps, the sheets recompute — "the sheets are checklists, the apps are the pen."

## Staff side
- `/register/me/month`: own row only, no money; the REMARK form ("कोई दिन गलत लगे?") lands on the
  owner's flow page with an open-day door and a "handled" button; staff see waiting/seen-by-doctor.
- Visibility windows as settings: running month live (staff_view_current) · completed month until
  **lock + 5 days** (staff_view_after_lock_days) · remarks on/off. The "revised sheet" is
  automatic — every view recomputes from the stores.

## Approval → FINAL → Lock
- **Approve Sheet 1 + Approve Sheet 2** (salary users; stored in `pack_approval`, audited) —
  Sheets 3/4 carry "FINAL — computed on the approved pack" only then ("WORKING PREVIEW" before).
- **The Lock Desk** (`/register/salary`): readiness checklist (dates ✓ · Sheet1 ✓ · Sheet2 ✓ ·
  enforcement ✓ · month ended ✓) + a summary identical to Sheet 3, computed by the D336 engine.
- **The Lock**: refuses without every ✓ — including `enforce_from` coverage (a preview month can
  never lock deductions); records the total, stores the FINAL Sheets 3+4 as the official run,
  **writes the hold ledger** (once per staff-month; unlock/re-lock never double-writes).
- The old engine (`salary_engine.py`) renders nowhere; dormant fallback (earlybig rulings still
  use it); retire after one clean locked month — the D288 retirement pattern.

## Prints (four per month)
Sheet 1 + Sheet 2 (the pre-approval working pack, A4, writing space) → Sheet 3 (detailed, all
columns) + Sheet 4 (name·amount·signature·date, separate page) — the owner's two-page format.

## Queued next (Runbook §2)
Desk Leaves/Absent columns + fines legend · the Arjun fine-threshold ruling · the owner-advances
entry on Sheet 2 (bridge until all advances live in the ledger) · printable Sheet-2 ·
the selfie-punch design (geotagged camera-only capture as EVIDENCE inside D334; outstation tool)
— to be minted as its own decision before build.
