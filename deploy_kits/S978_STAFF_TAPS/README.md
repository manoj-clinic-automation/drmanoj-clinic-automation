# S978_STAFF_TAPS — the staff taps on the morning's money cards (K2b)

*The parent, S545, 28-Nov-2026. D1100 (S537_MORNING_CHECK_FINAL_BUILD_PLAN §3 K2.2 – K2.4 + "Sab ho gaya"). His words: 14:03 "build K2 today"; 17:4x "Next blank paper" (the late parchi takes the book's next number). K2a (S977) is live; this kit adds the buttons.*

**What changes for the staff.** On the Day check page (Shavez, Shivani, Alisha; his page in English):
- **Register MORE (`nf:` card)** — *Parchi banayein*: pick the patient from the card, the service from the list of that head at exactly the gap's price (a list of one is pre-chosen), and the parchi number — the book's next number is filled in: they write that blank paper for the patient and file it. The parchi is made by the slip page's own code, dated that day, and kept outside Docterz at once. Refused: a patient already billed of that head, a service not at the price, a day older than 7. *Wapas* (Undo) voids that parchi.
- **Register galat likha — theek karein** on `nf:` and `less:`: the one register figure that holds the gap is corrected in one tap (audited like the register's Save; the push re-runs; **he is told on his phone**). Undo puts the old figure back. Within the staff's 7 days only; for cash only when the drawer was not counted, or when the fix makes the day's handover equal the count; never on a section whose money had to be guessed into a payment mode.
- **Refund tha (cash)** on `less:`: the refund (radd, money returned, in cash) on the picked patient's slip, for his approval as every radd.
- **Pata nahi**: the line leaves the staff list and goes to his phone, once (*"Staff don't know: …"*).
- **Sab ho gaya**: one tap writes the existing per-card ticks (only where a card's tick is a plain "done", and only the lines the page showed).
- **The Day check tile** in the Docterz group for Shavez, Shivani and Alisha (tile file v49 → v50).
- **The register opens on the last working day** until that day is saved — mornings only, until 13:00 IST (then on today, as before).

**Switch.** `DAYCHK_TAPS=0` hides every new button — the K2a cards exactly as they were. The register's "yesterday first" and the tile need the undo.

**Files.** `/root/finance/day_check.py` 5843d3d5 → baca5f66 · `register_push.py` 2ba0d63b → b7834202 · `clinic_register.py` ba56418d → 42a81900 · `/root/portal/tile_grants.json` 8a3cff12 → 325a7655. No new table: the taps write `day_check_tick` (acts `lateslip`, `regfix`, `dunno`), `slip` / `slip_item` through `slip_log.log_slip`, `slip_adjust` through `add_cancel`, `nid_mark` through `not_in_docterz.mark`, the register through `clinic_register.s978_set_cell`. `slip_log.py` is not touched.

**Install** (one server line, any hour; it waits for a quiet minute between the 5-minute push runs):
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s978kit && \cp -rp /root/deploy/repo/deploy_kits/S978_STAFF_TAPS /tmp/s978kit && bash /tmp/s978kit/install_S978_STAFF_TAPS.sh
```
**Undo:** `bash /tmp/s978kit/install_S978_STAFF_TAPS.sh --undo`

**Proof.** walk_s978 (made-up data, through the real Flask routes) 74/74 on the TO, red on the FROM (the control), thirteen mutants red; the S977, S970 and S968 walks green on the new files (both switch settings); the live shape on the 28-Nov copy, 60 days, counts only: every day's cards, totals and his lines identical to S977's, 0 errors; offered: 1 late parchi, 2 register fixes, 3 refunds, 11 "don't know"; every offered tap tried on a scratch copy — each day then matches by itself; rehearsal on a made-up root.

**Cold review (NOT SAFE, 3 MUST — all built in):** the drawer guard compared the count with the register's cash, not the day's handover (the float) — now a cash fix only when the fix makes the handover equal the count; the fix's tick sat on the card's key and could hide a gap that came back — now its own key, and a returning gap is a fresh line; any typed parchi number skipped slip_log's number checks — now only the book's next number does. SHOULDs built in: a parchi the check could not record is voided at once; the register fix within 7 days; no fix on a guessed payment mode; "Sab ho gaya" ticks only what the page showed; the register opens on yesterday only before 13:00 IST; every register fix is pushed to him once. Left as notes: staff errors from slip_log read in Hindi on his page; the parchi page link stays beside the form for a patient missing from the list.
**Second look (SAFE, 0 MUST; its SHOULDs built in):** an Undo of a cash fix refused when the drawer was counted since and would disagree; his push names every fix by itself (and an Undo as "fix UNDONE"); a fix never adds to the "not explained" figure; a parchi the check could not record is voided and read back (else "tell Dr Manoj"), audited; a register fix the check could not record is put back at once; the register's day and hour both read in IST; the number box empty with the next number as a hint (a paper already handed out that morning is never taken by the pre-fill).
