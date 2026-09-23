# S376_FU_PUSH_ON_ARRIVAL — the Callback Tracker's follow-up list, refreshed on arrival

**The owner, 23-Sep-2026:** *"I exported yesterday's doctor's consultation report and follow-up logs from my PC
this morning. But it has not been picked up by the system and processed, so the callback tracker is also not updated."*

**What was found.** The export *was* picked up: the PC's Docterz pickup (S239) processed 22-Sep at 07:45 IST,
wrote `Staff_Action_Today_2026-09-23.xlsx` (24 calls for today) and uploaded it to the server at 07:45. But the
job that writes that list into the Callback Tracker (`clinic-followup-push`) runs only at **22:00, 07:00 and
11:00**. The 07:00 run came 40 minutes before the export, so the tracker kept 22-Sep's list until 11:00.
An evening export (before 22:00) was always fine; a morning one waited up to four hours.

**What changes.** A small script checks the upload folder every 5 minutes; when a workbook newer than the last one
it saw has arrived, it starts the same push job at once. The three timer runs stay as they are. No code changes.

**Off switch:** `/root/finance/_off/FU_PUSH_ON_ARRIVAL` (or `ALL_OFF`). **Undo:** `crontab /root/wa/crontab.bak_S376`.
