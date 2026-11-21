# S916_MANOJZ_SENDS_FU_CONS — his PC's Docterz exports reach the server

*The parent · S496 · 21-Nov-2026 · installed on manojz by the assistant (connected folder), after S915 is live.*

| file (manojz) | pin | what changes |
|---|---|---|
| C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker\docterz_clinical_send.py | 4dd38304 → e77e0854 | Besides clinical data reports, it now copies his **follow-up logs** and **one-day consultation reports** from D:\Downloads into the Drive folder the server reads (`followup_logs_<first due>_manojz_<hex>.csv`, `consultation_report_<day>_manojz_<hex>.csv`). It skips anything the server fetch brought (a `_reception_` name, or an md5 in `_server_fetch_state.json`; everything waits if that record is unreadable), files from before 20-Nov 12:00, and a consultation report of more than one day or with no patients (logged: use the Docterz reports page). **Every copy keeps the file's own time**, so the server dates a follow-up log by its export. Own off file: `D:\Downloads\DocterzArchive\_fu_cons_send_OFF.txt`. |

## Proof
- `walk_s916.py` (made-up Downloads): **WALK 15/15**; the live (S780) file **4/15** (red).
- Cold review: its MUST (the copy's time) built in.

Undo: the backup `docterz_clinical_send.py.bak_S916_4dd38304` beside it, or the off file above.
