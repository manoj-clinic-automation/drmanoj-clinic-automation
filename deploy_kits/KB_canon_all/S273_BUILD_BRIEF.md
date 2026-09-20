# S273 BUILD BRIEF — the 360° patient record is live (five of six steps); the X-ray filing waits on staff files

*Session 273 · the parent project · 20-Sep-2026 · written at the close. The one document for the next session.*

---

## 1 · WHAT IS LIVE NOW

**For the doctors — the portal tile *Patient records*:**
```
https://followup.dr-manoj.in/finance/records
```
- Top: **one collapsed line** — *"Patient records: all clear"* or *"N need a look · oldest D days"* — opening
  to the open items and the last 7 days' answers (who, when).
- Search by clinic ID or name; **today's patients** from the slip tile; blood reports filed in the last 3 days.
- **One page per patient**, sections closed until tapped: Timeline · Visits (Docterz) · X-rays & reports (files
  open from Drive; *Add a paper*) · Pharmacy (sure bills only; returns against the bill) · Procedures ·
  Hospital & surgery (*Add event*: date, hospital, what was done, note, paper).
- The X-ray **test run** (read-only):
```
https://followup.dr-manoj.in/finance/records/xray-test
```

**For reception — the tile *Check karein* (Alisha, Shivani, Shavez; the doctors):**
```
https://followup.dr-manoj.in/finance/checks
```
Hindi, one tap, who and when. Items: blood test with no report after 2 days · lab report for an unknown ID
(confirm or correct) · lab e-mail with no PDF · **WhatsApp photo/PDF from a patient** (open it, pick the patient
— the ones on that number are offered — and Blood / X-ray / MRI-CT / Other / *Report nahi hai*). **Kagaz jodein**
adds an outside MRI/CT or discharge paper.

**Behind it:** the clinic Google Drive (drmka.ortho) → *Clinic Records/* holds every file; the server keeps only
the index. The mailbox script `VPS_Lab_Files.gs` (UPIReconciliation, every 15 min) is the only writer: lab PDFs,
WhatsApp media, the papers added on the server. **The assistant updates it itself in the owner's signed-in
browser (D577)** — the built-in browser is signed in to drmka.ortho as the second account (`/u/1/`).

## 2 · NEXT — THE X-RAY FILING (step 2, live)

**Entry condition:** 2–3 days of staff files in *X-ray test*; read the test page first — matched share, the
clock verdict, the real file-name shapes (the brief's "two or three real names" is answered by the page).

Build, in this order:
1. **Live filing.** The server decides (the same `xray_plan()` the test page uses); **the mailbox script executes**
   — renames/moves from *X-ray inbox* to *Clinic Records / X-ray / Mon YYYY / DD-Mon*, unmatched to *X-ray check*,
   duplicates kept once, originals kept a month (D574: the script is the only Drive writer). The server files each
   one as `record_file` kind `xray`, source `xray_inbox`.
2. **X-ray items in Check karein:** a file whose ID did not match; an X-ray (slip/Docterz) with no file by the next
   day. Plus **old and new X-ray side by side** on the patient page (images are already served inline).
3. **The one-time import of the old X-rays** from the X-ray PC — a separate folder, the same plan, a report first.

**Then:** Docterz uploads continue 2–4 weeks in parallel, stop on his word (the upload list becomes the "files
arrived" checklist). Step 6 (sending reports) waits on F-82.

## 3 · PINS

| file | pin |
|---|---|
| `/root/finance/records.py` | `8cdd334f2f1329899afd8fc09df145fd` (S346) |
| `/root/finance/records_drive.py` | `83a7171fb2e2bd8022613383641e4821` (S335) |
| `/root/finance/finance_app.py` | `7866b1ee6e70d19b5c096ef1b0099bd3` (S342) |
| `/root/portal/portal.py` | `d9a9dc409b203a4d8dcdd623aa54565f` (S342) |
| `/root/portal/tile_grants.json` | `a5f8b3b1ef40047052b65d9735f02e3f` (v23) |
| Apps Script `VPS_Lab_Files.gs` | sha256 `95463aa4…` (S346 build) |

## 4 · THE LESSON THAT MUST NOT RECUR (F-581)

Two kits refused themselves on the box because their walks counted "exactly N" of something the live data already
held. **A walk on a copy of live data asserts only about the rows it created itself.** Before a kit is placed, run
its walk once on a copy seeded with a real-shaped row of every kind it counts.

*S273 · 20-Sep-2026. Decisions D573–D577, findings F-579–F-584.*
