# S798_WA_MESSAGES_SHOWONLY — the approved WhatsApp messages, SHOW ONLY

**The owner, 12-Nov-2026 (D934, 08:34 / 09:39 IST):** start the approved templates through the WABA — post-visit, follow-up,
appointment reminders — *show only first*. **10:12 IST:** "ok" on the order shown to him (artifact D1QjJULDa64UM1oGx5pUX2):
follow-up tomorrow · after the visit · appointment reminder · follow-up date passed (the next morning, again after 5 days) ·
long overdue (two weeks, only the names he ticks).

**This kit sends nothing.** `wa_ladder.py` opens no network connection and calls no sender (the walk checks the file for it).

- NEW `/root/portal/wa_ladder.py` — **`/portal/messages`** (the doctor role only, English): for any day, six folded lists —
  who would get which approved message — each row with the name, clinic ID, the FULL mobile and the date, and either
  *would go* or *Held:* with its reason. A seventh list: the numbers that said STOP. Its data: `/portal/messages/api/plan`.
- **The rules:** a follow-up counts from the patient's latest visit only, and a patient who has come since is on no list ·
  no 10-digit mobile → held · on the stop list → held · one number, one message a day (the list order decides) · a patient
  with an online booking ahead is not told his date has passed. **Not yet:** leaving out patients who bought medicines
  meanwhile (D919) — the page says so.
- **The STOP listener:** cron every 5 minutes (`# S798_WA_STOP_LISTENER`): does what opening the WhatsApp Inbox does (reads the
  receiver's log forward into the Inbox store, `portal_inbox.ingest`), then reads the new incoming messages; a short message that
  says STOP / unsubscribe / "mat bhejo" / "message band" (Hindi too) puts that number in `/root/portal/wa_ladder.db` (its own
  store). The older opt-out file `/root/wa/wa_opt_outs.csv` is honoured too (read-only).
- `/root/portal/portal.py` 8b723919 → the **WhatsApp messages** tile in **Patients** (roles doctor) + the page mounted.
- READS only: `finance.db` (`dx_visit`, `patient_visit`, `patient_ref`, `online_booking`), the Inbox store, the opt-out file.

**Untouched, still there:** `/portal/wa/followups` (S172, the tracker-sheet batch sender), `/wa-approve`, `/portal/wa`.

Built by `make_s798.py` on the live bytes (the 12-Nov bundle's portal.py). **Walk** 41/41 on made-up patients (a scratch
finance.db and Inbox store built at run time); the CONTROL red on the live portal.py without the new file (4 of 6). The page
rendered in Chromium at 400 and 1100 px with made-up rows: nothing off-screen, no script error. **Cold review** (a reviewer
who did not write it): SAFE AFTER FIXES — its four must-fixes are built: the crontab is edited only from a good read of it
and every other line must survive; a STOP is recognised only when the WHOLE short message is one (so "report nahi bheji" or
"mera whatsapp band tha" never lands on the list, and "stop please" / "Stop promotions" do); the listener is never silently
deaf (a store it cannot read is said on the page and in its status line; the installer proves the store first); `--rescan`
re-reads every stored message after the rule is widened. Its should-fixes too: the lists in his approved order; `--undo`
checks what it undoes; a stop list that cannot be read holds every row; a plain 10-digit mobile only; "came since" by
clinic ID as well as by patient key; the long-overdue rows wait for his tick. The installer re-runs the walk on the box,
prints today's counts from the live records (counts only), proves the Inbox store, places, restarts the portal, checks the
page's door, runs the listener once, reads its status and adds the cron line; anything red puts everything back.
**A wrong entry on the stop list** is taken off on his word (one line: `sqlite3 /root/portal/wa_ladder.db "DELETE FROM optout WHERE mobile='<number>'"`).

**Install** (after the publish), one line on the server:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s798kit && cp -rp /root/deploy/repo/deploy_kits/S798_WA_MESSAGES_SHOWONLY /tmp/s798kit && bash /tmp/s798kit/install_S798_WA_MESSAGES_SHOWONLY.sh
```
Undo: `bash /tmp/s798kit/install_S798_WA_MESSAGES_SHOWONLY.sh --undo` (the stop list is kept).
