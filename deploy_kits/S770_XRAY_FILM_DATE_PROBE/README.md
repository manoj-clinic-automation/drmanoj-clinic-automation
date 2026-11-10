# S770_XRAY_FILM_DATE_PROBE — read the X-ray date from the film itself (READ-ONLY probe)

**The owner, 10-Nov-2026 10:56–11:13 IST:** the October *photo baaki* X-rays were prepared afresh on the X-ray PC and re-added
on 09-Nov evening, but the system read their date as 9-Nov. *"X-rays carry date of X-ray also, so a better match is possible?"* —
*"do all thats possible"*.

**What was found (S422, on the 10-Nov database copy, counts only).** The 18 re-added pictures carry no picture time, so the filing
run dated them by file time (09-Nov), found none of their IDs on 09-Nov's X-ray list and parked all 18 in the check folder; the
S752 re-try only ever looks at that same day. 16 have an ID with exactly one X-ray day still missing its photo; 1 has two such days;
1 has no ID and repeats an older parked picture. 8 older parked pictures are the first uploads these replace, and 3 first uploads
(two on 05-Nov, one on 08-Oct) were filed to another X-ray patient of that day under a mistyped ID.

**This kit measures, on the server, before anything is built:** for every picture in the check folder (70) and the 25 newest filed
X-rays (their day known — the score), whether the date can be read (1) from the picture's own metadata, (2) from the text printed
on the film (tesseract, white-on-black bands inverted; the whole picture if the bands give none); whether the film carries the
ID and the name; and what the film's date would do for each parked picture. Pictures are held in a private temp folder only while
read. **No database write, no Drive write, no /root file changed.** It installs `tesseract-ocr` and Pillow only if missing.

**The report** (`/root/s770_probe/report.txt` and one mail to the clinic mailbox): counts and dates only — pictures numbered,
the film's words masked, no name, no clinic ID, no Drive id.

**Walk (cloud, made-up root, drawn films):** 11/11 — printed date read and scored; EXIF date read; no-date picture says so;
ID + film date → file; no-ID → by name on the film date; no name / ID in the report; database unchanged; **CONTROL** (no OCR)
goes red as it must.

**Run** (after the publish), one line on the server:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s770kit && cp -rp /root/deploy/repo/deploy_kits/S770_XRAY_FILM_DATE_PROBE /tmp/s770kit && bash /tmp/s770kit/run_S770.sh
```
Nothing to undo. The build (filing by the film's date, the clean-up) follows as its own kit.
