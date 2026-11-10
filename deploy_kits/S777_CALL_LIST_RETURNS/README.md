# S777_CALL_LIST_RETURNS — patients who already came drop off the calling list

**The owner, 10-Nov-2026 09:44 IST:** staff keep calling patients who have already visited. **F-1226.**
Two rules, in the follow-up tracker's engine on manojz (`processor.py`, `recalculate_statuses` replaced whole; nothing else changes):

- **(a)** a visit from **half the advised period before the due date** (7-day advice: 3 days before; 30-day: 15 days before; at least 1 day — the owner, 18:39 IST: a fixed 3 days is wrong for a month's follow-up) closes the follow-up — **never the visit at which it was prescribed.**
  Docterz's Appointment ID on a follow-up is the prescribing appointment and rises day by day (no overlap between days on
  825 anchors); the prescribing day is read from the IDs of follow-ups whose prescribing visit is certain. 184 of 825 follow-ups
  are prescribed only 1–3 days ahead, so without this guard the prescribing visit itself would close them. Prescribing day
  unknown (the newest IDs), or no visit of the patient on/before it → the old rule: only a visit on or after the due date.
- **(b)** one visit closes **every** open follow-up of the **same Patient UID** it qualifies for (never on a name or mobile).

**Proof (device VM, copy of the live data folder, 09-Nov 20:30 IST ledger):** CONTROL (old engine) reproduces the stored statuses
and the live `Staff_Action_Today_2026-11-10.xlsx` exactly. New engine: 129 rows close (every one on a visit of the same UID; no
already-closed row changes); of the 63 on the 10-Nov list, 9 close; of the 16 counted at S421, 8 close and the other 8 are 5 follow-ups whose only
visit in the window IS the prescribing visit (3-day follow-ups — the patient has not come back) and 3 of the newest IDs (old rule).
The Call Sheet (120 calls) loses the patients who came and takes the next 10 waiting. Same-day re-run identical; next day no flips.
`probe_s777.py` (made-up cases incl. a wrong-patient visit, a prescribing visit at due−3, overlapping rows): new 13/13 GREEN,
CONTROL RED on exactly rules (a) and (b) (4 cases). The tracker's own `test_call_readback.py` 7/7 on both; `test_suite.py` identical on both.

The late side (on time / reminder / call list / dropout) is unchanged.

**Install** — on manojz, the live file kept beside it as `processor.py.bak_S777_0e7c129f` (live md5 0e7c129f → f1c02736).
The daily Docterz pickup (20:30 IST) loads the engine fresh, so the next run uses it; no restart.
**Undo:** copy the .bak back over `processor.py`.
