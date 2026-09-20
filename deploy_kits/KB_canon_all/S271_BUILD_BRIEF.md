# S271 BUILD BRIEF — the slip tile is live, and the 360° patient-records plan is settled

*Session 271 · the parent project · 19–20 September 2026 · written at the close.*
*This is the one document for the next session. It carries everything this session decided, built and
planned, so the next chat can build the records plan **in one go** without reading anything else.*

---

## 1 · WHAT IS LIVE NOW (built, installed and read back this session)

Seven kits, **S324 → S330**, all installed by Dr Manoj from one VPS line each, every installer green.
One tile in the staff app: **OPD & X-ray/Proc Slips** (`/finance/slips`). It opens a **menu**; each item is
its own screen with a Back button to the menu; the menu's Back goes to the portal.

| menu item | who | what it does |
|---|---|---|
| **OPD parchi** | chamber (Shavez; sometimes Alisha, Shivani, Bhati) | next slip number pre-filled from the running book; type the clinic ID → name autofills; an ID above the highest ever issued reads **NAYA** (new); "ID nahi hai" takes a name |
| **X-ray / Proc parchi** | chamber | patient picked from today's OPD in one tap; **separate** X-ray and procedure dropdowns from his rate page; up to 6 X-rays, 3 procedures; R/L/Both where the line asks; "Other" with an optional name |
| **Blood test** | chamber | pick the patient, one tap — no test names |
| **X-ray room work** | Awdhesh (Shavez/Bhati when away) | each X-ray/Proc slip with its **amount read-only**, then **UPI · Cash · Done**; never blocks anything |
| **Docterz upload** | reception (Alisha, Shivani, Shavez) | one line **per X-ray** and per blood report, oldest day first, "Upload ho gaya" per line, undo, all-of-a-day; blood orders with no report ask once, **at upload time only** |
| **Aaj ki list** | all | the day in slip order; every skipped number asks **Radd / Kharab / Baad mein** |
| **Report** | Dr Manoj, Dr Bhawna, Shavez | English: problems first, OPD and X-ray/Proc in slip order, Docterz lines with no slip, **pending uploads only**, blood tests to follow up |
| **Start new book** | all | only when a slip book runs out |

Menu order by person: Awdhesh sees the room first; Alisha and Shivani see Docterz upload first.

**His rulings that shaped it (all his words this session):**
- The two books: OPD slip book at reception **19201–19600**, first slip on 19-Sep **19373**; X-ray &
  procedure book in his chamber **1001–1400**, first on 19-Sep **1137**. System numbers run **alongside**
  the paper numbers, never replace them.
- **Every skipped number is answered** by the person using the tile (Radd / Kharab / Baad mein). The only
  exception was the one-time clean-up at the start: X-ray/Proc numbers up to 1136 were earlier days.
- **NEW means above the highest clinic ID issued before that day** (Docterz lines, visits, master rows
  actually seen). The patient master is missing some old IDs (2681 was one) and carries one stray row far
  ahead of the series — neither decides "new" any more.
- The room ticks Paid / Done whenever convenient; open ticks show as a short reminder, **never a block**.
- **Nothing is asked of reception during patient flow.** Blood-test outcomes ("Test nahi karaya" /
  "Sample diya, email nahi aaya") are asked only at upload time, the next afternoon.
- Knee studies (K/S) AP & Lateral is **₹1,000** (set on his rate page this session; every other X-ray price
  unchanged — Ankle was mis-set for about a minute and restored).
- The slip report runs **alongside** the old end-of-day report; the old one is replaced only on his word.

**Lab reports arrive by themselves.** NK Pathology e-mails every report to `drmka.ortho@gmail.com` with the
clinic ID in the subject (*"Your Report  MRS. … ( 8118)"*). `VPS_Push_Lab.gs` in that account's
**UPIReconciliation** Apps Script project sends the server **only the message id, the clinic ID and the
time** — never the name or the file — every 15 minutes. Installed by him 19-Sep 19:40 IST; first run sent 5.

**The 18-Sep "Pradeep" case, settled:** Docterz itself booked his ₹1,600 as one consultation with no
X-ray line (₹600 + two X-rays at ₹500). Our sheet copied Docterz faithfully. The new report names this kind
directly: *"the extra looks like the X-ray/procedure money booked as consultation."*

---

## 2 · THE PLAN HE SETTLED — THE 360° PATIENT RECORD (to build next, in one go)

### 2.1 The goal, in his words
He wants to open any patient's reports **when the patient visits again** — many forget their papers —
**without depending on Docterz**. Uploading into Docterz is a staff burden and cannot be verified. So the
**360° view becomes the record**: a tab on his chamber PC, patients of the day at the top, one click to a
patient's whole history. It is also the future gateway for sending soft copies to patients on WhatsApp.

### 2.2 Where the files live
- **The clinic's own Google Drive** (`drmka.ortho@gmail.com`), which is already installed and syncing on the
  **reception PC**. The server keeps only an index (clinic ID · kind · date · file id · source) — never the
  files. Files never become public links; every open is logged; only the doctors can open patient records.
- Folders by kind and date: *Clinic Records → X-ray → Sep 2026 → 19-Sep*, *→ Blood → …*. Files named
  *"2026-09-19 · 8118 · Name · Knee AP-Lat R.jpg"*.

### 2.3 Each source, and how it flows
| source | how it arrives | human step |
|---|---|---|
| **Blood reports** (NK Pathology) | the mailbox script also **saves the PDF** into Drive (it already reads the mail) | none |
| **X-rays** | X-ray PC stays **off the network** (his rule). JPG, **file name = clinic ID**, ~150–200 a month. Staff move the pen drive's files into **one Drive folder, "X-ray inbox"**, on the reception PC | that one move — no renaming, no dates |
| **Reports patients send on WhatsApp** to the clinic WABA number | saved automatically; sender's mobile matched to the patient master → **suggested** patient | reception confirms: right patient + Blood / X-ray / MRI-CT / Other / **Not a report** |
| **Outside MRI / CT reports, discharge papers** | photographed or scanned with the scanner already in the staff app, clinic ID picked | the scan |
| **Hospital admissions & surgeries** | an "Add event" form on the patient's page: date, hospital, what was done, note, attach the paper; later fed by the surgical-episode system | the form |

**X-ray filing, exactly:** the date comes from the file's own time (so the X-ray PC clock must be right —
the test run proves it); the ID from the file name; matched against that day's X-ray lines from the slip
tile and Docterz; renamed with the study from the slip; when a patient has several files they pair with the
slip's X-rays in time order, and **if the counts differ they are named "X-ray 1 / 2", never guessed**; the
original is kept a month; a file whose ID is not in that day's list goes to a **check folder**; duplicates
kept once.

### 2.4 What the 360° page shows (his additions included)
Top line: name, ID, age, first and last visit, counts. Below, **sections closed until tapped**:
**Timeline** (everything, newest first) · **Visits** (Docterz, fee/free/concession) · **X-rays & reports**
(thumbnails; full-screen; **old and new X-ray side by side**) · **Pharmacy** (Sanjeevni bills and medicines,
**returns shown against the bill**; only bills the system is sure of — walk-in and name-only bills never
guessed) · **Procedures** · **Hospital & surgery**. Pharmacy and money stay in the doctor's view only.

### 2.5 The doubtful ones — one reception queue, one line for him
**"Check karein"** (reception; Shavez the checker): an X-ray file whose ID did not match · an X-ray with no
file by the next day · a blood order with no report · a lab e-mail it could not place · a WhatsApp document
not yet confirmed. One-tap answers, each with who and when, ageing oldest first.
**He sees one collapsed line** — *"Patient records: all clear"* or *"4 need a look · oldest 2 days"* — that
opens to the items and from an item to the file and its full trail. *"I don't need to go at places or enquire
from people."*

### 2.6 What happens to Docterz uploads
They continue for **2–4 weeks in parallel** while the 360° view proves itself, then **stop on his word**;
the upload list then becomes the "files arrived" checklist. (Staff-log idea he raised — phone open beside the
reception PC, tap per upload, the day's folder emptying into "Uploaded" — is the design for that parallel
period, with a weekly **3-file random spot-check** by Shavez in Docterz.)

### 2.7 The build order he accepted
1. **Blood PDFs into Drive + the 360° page** (with visits, procedures, pharmacy bills and returns).
2. **The X-ray inbox** — a **read-only test run first** (a separate "X-ray test" folder for 2–3 days; the
   system renames nothing, writes a sheet: original name → proposed name → matched or not; he looks once),
   then live, then the **one-time import of the old X-rays** from the X-ray PC.
3. **"Check karein"** and his one collapsed line — early, because everything after feeds it.
4. **WhatsApp-received reports** into that queue.
5. **Outside MRI/CT scans and hospital/surgery events.**
6. **Sending reports to patients on WhatsApp** — once sending is cleared (WABA sending is held in dry-run
   by the vendor block, F-82).

### 2.8 Settle before building (assistant's work, not his)
- **Drive space** on the clinic account (X-rays add a few GB a year; a paid Google plan may be needed later).
- **Two or three real X-ray file names** from the X-ray PC (one patient with two views) — ask him in one line
  only if the test run cannot show it.
- **Whether MyOperator passes WhatsApp attachments to us** — read the vendor's webhook, do not ask him.
- The reception PC's Drive path (for the staff screen to name the folder exactly).

---

## 3 · WHAT IS WHERE

```
https://followup.dr-manoj.in/finance/slips
```
```
https://followup.dr-manoj.in/finance/slips/report
```
```
https://followup.dr-manoj.in/finance/clinic/sheets
```

| live file | pin |
|---|---|
| `/root/finance/slip_log.py` | `0b3195d2610e64a4b637e0ed89eb8454` (S330) |
| `/root/finance/finance_app.py` | `41e0ffb4ce8c94a76c251294ef3e5d31` (S324: unit `slips`, guarded mount) |
| `/root/portal/portal.py` | `4085b76781696f80f64283aa1eef57bb` (S324 = S329: one tile) |
| `/root/portal/tile_grants.json` | `fe38b97494ee7a43091323dfd64e7836` (v22) |
| Apps Script `VPS_Push_Lab` | drmka.ortho → UPIReconciliation, trigger every 15 min |

Tables (finance.db, created on first use): `slip_book`, `slip`, `slip_item`, `emr_upload`, `blood_order`,
`lab_report`. Unit `slips`: makers shavez, alisha, shivani, bhati, awdhesh · checkers manoj, bhawna.
New door: `POST /finance/slips/api/lab-report` (X-Finance-Cron, the Gmail pushes' existing token).

---

## 4 · THE BACKLOG AFTER THE RECORDS PLAN
Carried from S269, untouched this session: his approvals and procedure prices on the rate page · the
phonebook from the two contact exports · the freshness page (F-540) · the `watcher` kit (D554/F-547) · the
last four units into the bundle (D555) · fault injection for `backup`/`outbox` (D525) · "Attendance report
not received" on the daily report · **Manoj Bhati's petty book** — Back link only at the bottom, he scrolls
a lot; give it the slip tile's layout (offered, not yet ruled) · bank-SMS feed PARKED.

*S271 · written at the close, 20-Sep-2026. Decisions D557–D563, findings F-550–F-555.*
