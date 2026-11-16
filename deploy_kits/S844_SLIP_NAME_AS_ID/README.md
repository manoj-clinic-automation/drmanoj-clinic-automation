# S844_SLIP_NAME_AS_ID — old slips with a name as the clinic ID (the parent, S469, 15-Nov-2026) — F-1424

**The fault.** Before S840 the old slip pages accepted letters in the clinic-ID box, so a typed name was saved as the clinic ID.
On the 14-Nov database copy: 8 such slips since 29-Sep — 4 live X-ray/Proc slips and 4 cancelled numbers (counts only). A live
one cannot match its X-ray photo, its Docterz line or its follow-up.

**His word.** "Start with this" (12:34 IST 15-Nov), on the entry point's item B.1 (list them with one tap to set the ID).

**The change — one file, `/root/finance/parchi_desk.py` (6eaf9896 → `TO_PINS.md5`); clinic-finance is restarted.**
- On the slips desk (`https://followup.dr-manoj.in/finance/slips/desk`, Shavez's and the owner's), above the day's lists: a box
  **"Parchi par naam likha hai, clinic ID nahi — N"** (English for the owner). Each live slip (state ok) whose clinic ID holds a
  letter the master and Docterz do not know: its date, OPD / X-ray-Proc and number, what was written, up to four likely patients
  (`check_screens.find_people` on the slip's day — the ones who came that day first; the mobile's last four only) as one-tap
  buttons, and a box to type the ID. Cancelled / spoilt numbers are not listed — nothing waits on them.
- `POST /finance/slips/desk/api/set_id` — the desk's roles; digits only; a patient the clinic knows; the slip must still hold the
  name (the update is guarded on the old value); `name_seen` and `is_new` filled as `log_slip` does; audited `slip_set_id_s844`.
- **The old doors** — `/finance/slips/save`, `/finance/slips/blood`, `/finance/slips/pending/new`, the lab report's `noid_pick` —
  refuse a clinic ID with a letter the master does not know, as S840's desk doors do. Done by a guard in `parchi_desk.py` that
  reads the field the door reads before the door runs, so `slip_log.py` is not touched; on a fault in the guard the door runs as
  before. A GET is never stopped; 'ID nahi hai' (no ID, the name in its own box) still saves.

**Install (one line on the server):**
`cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s844kit && cp -rp /root/deploy/repo/deploy_kits/S844_SLIP_NAME_AS_ID /tmp/s844kit && bash /tmp/s844kit/install_S844_SLIP_NAME_AS_ID.sh`
Undo: `bash /tmp/s844kit/install_S844_SLIP_NAME_AS_ID.sh --undo`. `DRY=1` before `bash`: every gate, nothing written.

**Proof.** `walk_s844.py` on a copy of the database with made-up slips (31 checks; counts only) and `--control` (five broken
copies go red: the master's knowledge ignored, the guard off, the fix door without its roles, letters accepted on the fix,
cancelled slips listed); `walk_s840.py` (S840's own, 25/25) on the new file — the desk otherwise unchanged. The installer runs all
three on a copy of the live database before placing anything.
