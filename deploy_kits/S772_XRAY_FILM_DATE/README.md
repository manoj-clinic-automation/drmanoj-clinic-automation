# S772_XRAY_FILM_DATE — file the parked X-ray pictures by the date (and ID) printed on the film; clear the extra copies

**The owner, 10-Nov-2026 10:56–11:13 IST:** the October *photo baaki* X-rays were re-prepared on the X-ray PC and re-added on 09-Nov
evening, and the system read their date as 9-Nov — *"finalize a plan to remove all unnecessary re-uploaded X-rays from there and settle
the pending X-rays issues"* · *"X-rays carry date of X-ray also, so a better match is possible?"* · *"do all thats possible"*.

**What was wrong.** A freshly exported picture carries no picture time, so the filing run took its file time (09-Nov) as the X-ray day,
found none of the 18 IDs on 09-Nov's list and parked all 18; the S752 re-try only ever looks at that same day.

**What S770 proved on the server (read-only):** no picture carries a date in its metadata (0 of 95), but the film prints it — RapidOCR
read the film's date on 24 of 25 already-filed X-rays, all 24 their known day, none wrong — and prints the clinic ID beside the name.

**What changes**
- `/root/finance/records.py` (d86f2ada → built by `make_s772.py`, six counted edits + `s772_block.py`): every filing run's re-try plans a
  parked picture on another day ONLY after its film has been read, and only for a confirmed patient — the film prints the file's ID, or
  the picture's name matches the ID's patient STRICTLY (the S752 filing rule; a loose match never files):
  1. the date printed on the film, when it is one of that ID's X-ray days (or its one open day within 2 days — a slip written next day);
  2. the ID printed on the film when the file's name has none or another — that patient's name strict, the film's date that day;
  3. with no date on the film: the ID's ONE X-ray day with no photo in the 60 days before the picture was first seen.
  Anything else stays for a person (Check karein), as now.
- **The clean-up** runs only AFTER the mailbox has filed the corrected copy, and moves to *X-ray inbox / _filed / duplicates*
  (nothing deleted): (a) the older parked copies of the same name — no ID or an ID not on that day's list, never the same ID, first
  seen within 3 days, their own film agreeing (date, no other ID), the corrected copies covering the study's films, no more old than
  new (held out of the plan meanwhile so they are not filed beside it); (b) a copy filed to ANOTHER patient that day under a mistyped
  ID, when that patient shares no word of the name and has more photos than films that day — its record made `void` with the reason.
- NEW `/root/finance/xray_filmdate.py`, cron every 30 minutes, RapidOCR in its own `/root/xray_ocr/venv`: reads each parked picture's
  film ONCE into the new table `xray_filmdate` (dates, IDs); writes nothing else; the picture is held in a private temp folder only while
  read. Switch: `/root/finance/_off/XRAY_FILMDATE_OFF`.
- The Drive side (`VPS_Lab_Files.gs`) is unchanged: it already files, checks and moves any file to *duplicates* by the server's word.

**Cold review (S422):** R1 NOT SAFE, R2 NOT SAFE (one case: a film ID differing from a file ID that was also X-rayed that day); the reviewer: "safe after it" — built, its probe cases stay parked. R1 found: a mistyped ID could land on another patient's open day; a misread film ID plus a loose name
could file to a namesake; "not read yet" filed by the ID rule; the clean-up could hide a second view or a patient's own X-ray. All
built (the rules above); the walk carries each as a case.

**Proof on the 10-Nov database copy (manojz, counts only, no film reads there — every picture as "read, nothing found"):** 70
parked → 10 filed by the ID's one open day with a strict name, 1 by S752 as before, 59 still for a person; the next run's clean-up
voids 1 copy filed to the wrong patient. With the film's IDs and dates on the box the installer's proof counts more (17 of the 18
re-added films print their ID). The installer runs the first film read and this proof on the live database before anything is placed.

**Walks:** S772 39/39 (cloud, made-up database), CONTROL red on the live file; S752's walk 50/50 on the new file; the film reader 19/19
(tesseract and RapidOCR; built-in font). On the box the installer re-runs all of these plus S373's walk.

**Install** (after the publish), one line on the server — about 5–8 minutes (the film reader's set-up and the first read):
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s772kit && cp -rp /root/deploy/repo/deploy_kits/S772_XRAY_FILM_DATE /tmp/s772kit && bash /tmp/s772kit/install_S772_XRAY_FILM_DATE.sh
```
Undo: `bash /tmp/s772kit/install_S772_XRAY_FILM_DATE.sh --undo` (records.py back, the cron line out).
