# S780_CLINICAL_FROM_DOWNLOADS — a clinical data report exported on manojz reaches the server by itself

**The owner, 10-Nov-2026 19:23 IST:** "It should also pick up when I export to my downloads folder in my PC."

On manojz, `DOCTERZ_PICKUP.bat` (Task Scheduler, every 5 minutes) now runs `docterz_clinical_send.py` after the server fetch and
before the pickup. It recognises a Docterz *Clinical data report* in `D:\Downloads` by its columns (any file name), and copies each
new one (downloaded on or after 10-Nov-2026, at least 2 minutes old) once into `H:\My Drive\Clinic Records\Docterz exports`
as `clinical_data_report_<latest day>_manojz_<6 hex>.csv`. The server's pickup takes it within 15 minutes (S779: its own kind,
every visit's diagnosis read). Nothing else in Downloads is touched; nothing moved or deleted; counts, dates and md5s only in its log.

Why Drive and not the reception door: the server's upload door trusts only the reception PC's key (manojz's key is enrolled
for reading exports only); the Drive folder is the road the server already reads, and needs no server change.

**Proof:** `walk_s780.py` 13/13 (made-up files). On the real Downloads (126 CSV files, sent to a scratch folder): exactly one —
the 01-Jul → 09-Nov export (5ba401e3).

**Installed 10-Nov-2026 by the assistant at the owner's word** (C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker):
`docterz_clinical_send.py` (NEW) and `DOCTERZ_PICKUP.bat` 1a52d792 → the kit's copy (one REM block, one line), the old kept as
`DOCTERZ_PICKUP.bat.bak_S780_1a52d792`.
**Off:** a file `D:\Downloads\DocterzArchive\_clinical_send_OFF.txt` (or `D:\Downloads\margsync\_off\ALL_OFF.txt`).
**Undo:** copy the .bak back over `DOCTERZ_PICKUP.bat`.
**Log:** `D:\Downloads\DocterzArchive\_clinical_send_log.txt`.
