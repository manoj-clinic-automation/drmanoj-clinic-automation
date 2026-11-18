# S862_PATIENTS_WORDS_ENQUIRIES — the parent, S480, 18-Nov-2026

**His word:** "go" (07:59 IST 18-Nov) on the three last pieces of the Patients page. This kit carries two; Google's mail is S863.

**What he sees** on `https://followup.dr-manoj.in/finance/console/patients`:
1. **Diagnosis words to place** — every word his taxonomy did not recognise, with the group the page suggests (from a spelling slip read through his own taxonomy, or a fixed word list). **Place** puts the word there with its spellings and sides (ticked under it, each can be unticked); every figure moves with it. **Placed by you** lists each word with **Undo**.
2. **At the front desk → Enquiry callers who became patients** — month by month: callers not yet patients, how many came as new patients within 60 days (tap → clinic IDs), new patients of the month and how many rang the clinic before their first visit (tap → clinic IDs). A month is "so far" until 60 days after its end.
3. Google: `patients_part2.py` lays `/root/finance/patients_google_mail.json` (written by S863's reader) over `patients_google.json` — the mail's counts win, Google's year-on-year stays; the card then says "read by the server from Google's mail of …" and the "Still to come" card disappears. Without that file the page is as before.

**Files (all the parent's):** `/root/finance/patients_page.py` 561c6bf4 → d5b403a6 · `patients_page.html` 62e5dc88 → 31bc144c · `patients_part2.py` 0277cb5c → 6eae4a20. `dx_feed.py` read only (its own `dx_term_map`, `reclassify`, `term_key`).

**Writes:** only his tap — `dx_term_map` (word → standard diagnosis, set_by, set_at) and `dx_feed.reclassify()` re-reading `dx_visit`; then the reading is rebuilt at once. JSON POST only, the console's gate (his login alone).

**Proof:** `walk_s862.py` 55/55 (47/47 where there is no node) on a made-up root (Flask, every role; the page's own script under node), control on the live files red; S853's walk 39/39 and S851's 34/34 on the new files; `shape_s862.py` on copies of the live stores (Part 1 identical but the words; a Place and its Undo on a second copy move exactly the row's visits and nothing else).

**Install:** his publish, then one server line (in the installer's head). **Undo:** `bash /tmp/s862kit/install_S862_PATIENTS_WORDS_ENQUIRIES.sh --undo` (a word he placed stays placed).

**Cold review (S480):** SAFE TO INSTALL; its 3 SHOULD built in — a re-read that fails half way takes the tap back whole (rollback + the map rows put back, JSON answer); a reading that cannot be built at once is marked old and the message says so; the became/rang-first lists carry the clinic ID as written (07003). LOW built in: an ID the visit record has not reached is not 'old'; the shape's in-process Place reads the copy of the call record; a month change clears the message.
**Second look (S480):** SAFE TO INSTALL; its SHOULD built in (the Google card stands on the mail alone when the session file is missing) and two LOW ("read by the server" only when a whole mail month was laid over; a whole number written 90.0 is read as 90).
