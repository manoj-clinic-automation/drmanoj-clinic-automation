# S606_STAFF_JOIN_EASY — Add staff in two touches (session S331, 20-Oct-2026)

**The owner, 20-Oct-2026:** *"look into new staff addition flow, because when I tried with one new staff, Arjun Dev,
I got stuck up at one point of the flow. So I need such a flow which can be executed easily."* — and, 17:41 IST:
*"Few might not have whatsapp or smartphone occasionally, build this functionality, biometric new staff entry is also
confusing for us."*

**The one line (VPS):**

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S606_STAFF_JOIN_EASY/install_S606_STAFF_JOIN_EASY.sh

## What was wrong (read from the live code and data, S331)
- Arjun Dev's joining (JOIN-2026-0002, opened 18-Oct 11:08 IST) stood at 2 of 6. Step 3 opened WhatsApp with **no
  number**; step 4 asked for a tick nobody can know (the portal records no sign-ins); step 6 asked for a tick that
  **no button made true** — nothing on the page put a person into attendance or salary.
- The staff register keys a person on the **machine's number** (`staff_id` = the biometric user id), so his row
  cannot exist before the machine enrols him; the ladder said the row came first.
- His login was saved as `arjun dev` — the username box took a space as typed.

## What it does
1. **https://followup.dr-manoj.in/finance/staff/new** — *Add staff*. One form: name, mobile, **what phone he has**
   (WhatsApp · simple phone → SMS · smartphone without WhatsApp → printed slip · **no phone → no login**, attendance
   on the machine alone), job, full/part time, joining date, duty hours, Sunday duty (A/B/C in words), salary, offs,
   late minutes counted or not. Save makes a clean login (first name; the whole name when another staff member has
   that first name — so a second Arjun is `arjundev`).
2. **His login**: WhatsApp opens **his** chat with the message typed; SMS opens the phone's messages app; the slip
   prints in Roman Hindi. "Sent ✓" records it. *Signed in once* is recorded honestly as not tracked.
3. **The machine**: the page lists the steps (MENU → your finger → 1 Register → 1 New Reg. → his finger → ESC → he
   presses once) and **watches the punches**: *"Number 102 · first pressed today 17:52 — Yes, this is Arjun Dev"*.
   One tap: the number on the never-reuse register, a row in `/root/staff_master.csv` (backup first, atomic), rows in
   `staff_register.db` (`staff` + `staff_shift`, audit line), and the joining closes itself. A leaver's old number
   punching again is flagged, never offered.
4. `staff_pages.py` mounts it (guarded: a failure cannot take the old page down); `/finance/staff` keeps working and
   gets one banner line pointing to the new page. `joiner_app.py` and `finance_app.py` are untouched.
5. Data step (the page's own `_settle`, run once): Arjun Dev's login `arjun dev` → `arjundev` (password unchanged).
   His details, mobile and salary are then filled once on the new page.

Salary is on these pages, so every route is the doctor's alone (F-31). No phone number is written to finance.db;
the mobile lives in `staff_register.db`'s new table `joiner_pending`.

**Proven by:** `walk_s606.py` — 36 checks on scratch copies of the live files (made-up people, punches dated 2099),
the WhatsApp and the no-phone joiner start to finish, the space-login heal, the leaver-number flag; the same walk on
the old files goes RED (the control). Rehearsed on a made-up root: install, second run ALREADY INSTALLED, a failed
restart putting the old files back, `--undo`.

**Undo:** `bash .../install_S606_STAFF_JOIN_EASY.sh --undo` (files back; data written by the page stays; backups in
`/root/s606_backup/`).
