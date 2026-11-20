# S909_PHONE_DAILY_CHECK · Sanjeevni session 494 · 20-Nov-2026

The owner, 19:37 IST ("GO") and 20:38-20:43 IST ("if the message does not reach the clinic inbox, can it go to the clinic doctor ... and then come to me as a notification and in Needs-you both"; "OK").

* **Every day at 10:00 IST** the server queues ONE check message (its own kind, `check`) on the reception phone's road. The phone sends it by WhatsApp to the **clinic's own WhatsApp number** (saved once by the owner on his Reception phone card; masked to its last four everywhere). The message carries a random code; the server looks for it in the WhatsApp receiver's own files and the inbox store (read only).
* **Not there in 20 minutes** -> the failed step is found: not collected by the phone (FAILED: is the phone on, online, MacroDroid running) · collected, no "sent" report (queued once more; second miss FAILED) · reported sent, not in the inbox (the clinic doctor runs, as it is, then one fresh message; second miss FAILED: MyOperator or the number).
* **Fixed itself / FAILED** reach the owner twice: a clinic-app notification (owner_notice's table and its own tick) and a Needs-you line (the Hub). A plain pass is quiet. The card shows the last result, the clinic number, Save and **Check now**.
* A check message is never retried by the door, never on the stuck list, never counted by the silent-phone line. The check message is visible in the staff's WhatsApp inbox (one a day, "automatic, no reply needed") -- hiding it would be the parent's portal_inbox.py.

Files: NEW `/root/finance/phone_check.py` · `/root/finance/supplier_msg.py` 407d2b1d -> see TO_PINS · `/root/finance/porders_s454.py` 06966a0f -> (both by `make_s909.py`, exact anchors + one tail block each) · cron `*/5 ... phone_check.py tick # S909_PHONE_CHECK`.
Reads only: `/root/wa/wa_logs/*.jsonl`, `/root/wa/wa_inbox/inbox.db` (the parent's). Runs as it is: `/root/deploy/clinic_doctor.py` (the parent's).
Switches: `/root/finance/_off/ALL_OFF`, `/root/finance/_off/PHONE_CHECK_OFF`, setting `phone_check.on`. Install: one server line (the installer's header). Undo: `undo_s909.sh`. Rehearsal: `rehearse_s909.sh` on a made-up root. Walk: `synth_s909.py` (made-up numbers built at run time).
