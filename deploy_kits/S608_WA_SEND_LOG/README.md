# S608_WA_SEND_LOG — every WhatsApp send logged, shareable with MyOperator (S331, 21-Oct-2026)

**The owner, 21-Oct 10:57 IST:** *"maintain a detailed log, which I can share with myoperator team as needed, without
needing you."* The inbox kept no record when MyOperator refused a message (HTTP 500 to Deep Singhal ..8850, 20-Oct
~16:00 and 21-Oct ~10:50 IST), so nobody could give MyOperator times or request ids. Ticket 691386 reopened 21-Oct.

**The one line (VPS):**

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S608_WA_SEND_LOG/install_S608_WA_SEND_LOG.sh

**What it does** (one file: `/root/portal/portal_inbox.py` 7bb6e0d7 → new, by 8 exact edits in `edits_s608.py`)
1. Every send from the inbox — text, photo, PDF, voice, template — is appended to `/root/wa/wa_inbox/send_log.jsonl`
   (600): time IST, who, customer (full number), what, MyOperator's HTTP status, full reply, **x-amzn-requestid**,
   time taken, the exact request body. **Never the key**; cookies dropped.
2. **https://followup.dr-manoj.in/portal/inbox/sendlog** — the owner's page (same WhatsApp gate as the inbox; a "Send
   log" link on the inbox header): all / refused only, 1–365 days, **Download CSV**, **Email to MyOperator** (from the
   clinic Gmail via the watchdog's SMTP settings, to support@myoperator.com + khushi.jain@myoperator.co, subject
   `Re:[## 691386 ##] …`, the CSV attached, an optional line from him). Ticket and addresses: settings
   `INBOX_MYOP_TICKET`, `INBOX_MYOP_MAIL_TO`, `INBOX_MYOP_MAIL_CC`.
3. Each refused send is mailed to the clinic Gmail itself — `[WA send refused] <time> · ••••<last 4> · HTTP <code>` —
   batched, at most one mail per two minutes, so the record sits in the mailbox ready to forward.
4. Sending is unchanged: the same request, the same key, the same answer on screen. Health line → `S608`.

**Proven by:** `walk_s608.py` — 25 checks with a stand-in MyOperator (200 for one made-up customer, 500
`{"message":null}` for another, each with an x-amzn-requestid) and a stand-in mail server; the S599 file goes RED.
Rehearsed on a made-up root: DRY, install, ALREADY INSTALLED, `--undo`, a failed restart putting S599 back.

**Undo:** `--undo` puts the S599 file back (`/root/s608_backup/`); the log file stays.
