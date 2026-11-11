# S786_ONLINE_BOOKING — online bookings paid on Docterz, shown to staff

**The owner, 11-Nov-2026 07:15 IST:** *"One patient has booked a consultation through the doctor's system online, and she has paid
online, and I have received a mail in my Google account. So I need this to be pulled and displayed when this happens, so that staff
can see this."* — **07:59 IST:** *"Full mobile number required. Display required — patient name, clinic id (for existing ones), full
mobile number, paid 600/- online, appointment time booked (if it's out of these timings — 11 am to 1.30 pm, and 7 pm to 8.30 pm
(Monday to Saturday) — then they call patient and inform them to come in these timings)."*

**The road.** Docterz mails *"<name> appointment at <day time> payment completed."* (support@docterz.in) to his personal Gmail. A filter
there (the owner's one GUI step) forwards only these mails to the clinic Gmail, which the server already reads by IMAP
(`/root/deploy/email_agent.json`, read here, never written).

- NEW `/root/finance/online_booking.py` — cron every 3 minutes (flock): the clinic Gmail opened **read-only** (no mail marked,
  labelled, moved); each Docterz payment mail of the last 7 days read (name, **full mobile**, amount, booked time, Razorpay ids);
  the clinic ID(s) on that mobile from `patient_ref` (the ring pop-up's own lookup); kept once in **finance.db table
  `online_booking`** (UNIQUE on the Razorpay payment id, insert-only); a **push notification** to the phones of reception, shivani,
  alisha, shavez and the owner for a booking of today or later; its state in `online_booking_state.json` ("Last checked" on the page).
- NEW `/root/portal/online_booking_portal.py` — **`/portal/booking`**: one card per booking (arrived in the last 3 days, or booked
  for today or later): name · Clinic ID (or "new patient") · the full mobile (tap to call) · *₹600 online paid* · the booked day and
  time · *do not collect the fee again — Wallet in Docterz*; outside Mon–Sat 11:00–1:30 / 7:00–8:30 (or a Sunday) a red box
  *call the patient* and a **Phone kar diya** button (who and when, once). Hindi for staff, English for the doctors. Who: the doctor
  role and the logins the tile is granted to by name.
- `/root/portal/portal.py` 34750b24 → the **Online booking** tile in **Patients** (roles doctor) + the page mounted.
- `/root/portal/tile_grants.json` 66de5e20 (v45) → v46: the tile to **reception, shivani, alisha, shavez** (shipped as
  `tile_grants.json.s786` — the repository ignores `*.json`).
- `/root/finance/owner_console.py` 1a3d4fd4 → **Needs you**: *"Online booking paid on Docterz: <name>, <day time>"* — red while one
  outside his timings has not been called by staff.

Built by `make_s786.py` on the live bytes (S785's portal.py and owner_console.py; the 11-Nov bundle's tile_grants.json). **Walk**
34/34 on a copy of finance.db with made-up patients (an ID checked absent first); the CONTROL red on the live files (8 of 10).
The installer runs the walk again on a fresh copy, reads the clinic Gmail once read-only (yes/no per mail, never a value), places,
restarts both services, checks the page's door, runs the first pass and adds the cron line; anything red puts everything back.

**Install** (after the publish), one line on the server:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s786kit && cp -rp /root/deploy/repo/deploy_kits/S786_ONLINE_BOOKING /tmp/s786kit && bash /tmp/s786kit/install_S786_ONLINE_BOOKING.sh
```
Undo: `bash /tmp/s786kit/install_S786_ONLINE_BOOKING.sh --undo` (the table is kept, unread).
