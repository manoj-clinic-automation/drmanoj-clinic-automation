# S898_PHONE_STUCK_AND_SILENT · Sanjeevni session 490 · 20-Nov-2026

The owner, 17:49 IST: "old 2 messages not sent need to be removed from reminder or sent again, but thru a built in functionality in the reception phone page as well".

* **The owner's Reception phone card** (https://followup.dr-manoj.in/finance/porders?old=1#s454phone) now shows the phone's last "sent" report and lists every message the phone took and never reported (payment notices, month-summary reminders; not orders, not tests), each with **Send again** (handed to the phone once more) and **Remove** (marked skipped, kept with who and when), plus **Send all again / Remove all**. Two-tap, no dialog. Owner only.
* **Needs-you**: one line when the phone took messages 15 min – 24 h ago and its "sent" report has not reached the server since — the 12–20 Nov MacroDroid constraint case.
* **The Hub's Go to** → Payments → "Reception phone — test message, messages not reported".

Files (all this project's, by `make_s898.py` from the live bytes): `/root/finance/supplier_msg.py` bdfe4ce7 → see TO_PINS · `porders_s454.py` c992ba91 → · `finance_ui/finance_approvals.html` f045686d →.
Install: one server line (in the installer's header). Undo: `undo_s898.sh`. Rehearsal: `rehearse_s898.sh` on a made-up root.
