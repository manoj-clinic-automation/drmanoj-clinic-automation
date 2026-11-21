# S494 — what changed (20 → 21-Nov-2026, Sanjeevni)

**Live now:**

- **The reception phone works with its screen dark** (your steps, 20:33). It checks the server every minute, screen on or off. Screen lock is None, and the macro no longer has the Screen On or Device Unlocked conditions.
- **The daily delivery check** (live 21:31, proved at 22:05). Every morning at 10:00 the phone sends one check message to the clinic's own WhatsApp. If it doesn't reach the clinic inbox within 20 minutes, the server finds which step failed:
  - **The phone never collected it.** You're told the phone needs looking at: is it on, online, and is MacroDroid running?
  - **The phone collected it but never reported it sent.** The server sends it once more.
  - **The phone reported it sent, but it never arrived.** The clinic doctor checks the server and restarts anything that isn't answering, then a fresh message goes.
  - Whatever happens, "fixed itself" or "FAILED" reaches you twice: a notification on your phone and a line in Needs-you. A pass is quiet.

Your card shows the last result, the clinic's number (last four digits only) and a **Check now** button:

```
https://followup.dr-manoj.in/finance/porders?old=1#s454phone
```

- The staff will see one check message a day in the clinic's WhatsApp inbox, marked automatic, no reply needed.

**Next session, first:** the phone set-up page updated to match tonight's settings, so the staff never undo them.

**Yours:** the publish of these records; lock October; the packs page (the 25 card shops; the card and ICICI passwords); the medical PC's Wi-Fi 2 (one tap).
