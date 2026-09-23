# S374_XRAY_LIVE_2 — the X-ray pictures filed for real

*S374 = S373 with the installer's token-less probe corrected: the finance app's gate answers 302 (to the login)
before the route's own 401 — both mean locked. S373 went red at that probe, restored itself, and is frozen.*

**The owner, 23-Sep-2026:** *"The X-ray upload test period is over. Now incorporate it into the system."*

**What the staff do — unchanged.** They keep putting the X-ray photos in the same Drive folder, **X-ray test**
(or X-ray inbox), with the clinic ID anywhere in the name (D585).

**What happens now.** Every run of the mailbox script (the one that already files lab reports) asks the server
what to do with each picture, and does it:

| the picture | where it goes |
|---|---|
| ID found and matched to that day's X-ray slip / Docterz line | a **copy** under *day · clinic ID · name · study* into **Clinic Records / X-ray / Mon YYYY / DD-Mon**; the original moves to **X-ray inbox / _filed** — nothing is deleted |
| the same picture twice | **_filed / duplicates** |
| no ID, or two numbers, or an ID with no X-ray that day | **X-ray check** — and it appears in **Check karein** with a box for the right clinic ID; the next run files it |

**Check karein also asks** about any patient whose slip or Docterz line shows an X-ray from 23-Sep and who has
no picture by the next day: *File baad mein daalenge* · *X-ray nahi hua*.

**The patient page** (Patient records) gains **X-rays taken** — the newest 12 pictures side by side.

**Proof.** `walk_s373.py` 22/22 on a scratch copy of the live database, its own day (2001-01-01) and IDs only,
stub Drive folders: plan, report, idempotent re-report, check folder, the staff's ID answer, the next run filing
it, the missing-file item and its answer, the gallery, the cron doors (401 without the token); the live
`records.py` (S353) is the negative control (no plan door; +2 routes, none lost). After the restart the installer
asks the plan once against the real folders and prints the counts only.

**Files.** `/root/finance/records.py` 07ec9b41 → 6492135c (full file, made by `make_s373.py` from the live bytes
+ `xray_live_block.py`). `finance_app.py` untouched. Restarts `clinic-finance`.
The Drive side is `_fileXray()` in the mailbox script **VPS_Lab_Files.gs** (UPIReconciliation), placed by the
assistant after this is live; `deploy_kits/GAS_CURRENT/UPIReconciliation/` updated in the same breath (D583).
