# S599_WA_INBOX_TEMPLATES_STAFF — templates live, the right key, staff replies in each chat (D744)

**The owner, 19-Oct 08:52 IST:** *"I want to send templates. And if possible, I would like to see the replies which are
sent by my staff members in the chat also."* — 08:57 *"go"*. The S597 proof text had been refused by MyOperator (HTTP 500).

**The one line (VPS):**

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S599_WA_INBOX_TEMPLATES_STAFF/install_S599_WA_INBOX_TEMPLATES_STAFF.sh

**What it does**
1. Every WhatsApp key the server holds (`/root/wa/.env`, `/root/wa/wa_approve.env`, the text sender's chain, the portal's
   own) is held against MyOperator by *reading* the approved-template list — nothing is sent. Shown by place, never value.
2. `/root/wa/wa_inbox/config.json` names the first key that works (its place, not the key). The inbox uses it for text,
   photo, PDF, voice and templates.
3. Templates live: `portal_config.py` gets `PORTAL_WA_DRYRUN = "0"` (and `MYOP_AUTH_TOKEN` = the proved key **only if**
   the portal's own key is the refused one). This also makes **Send WhatsApp** and the **follow-up batch** send for real.
   Kept first in `/root/s599_backup/` (600).
4. `portal_inbox.py` (14c94a46 → new): each chat also shows the clinic's replies sent from the portal's template log
   (`/root/wa/wa_portal/wa_portal_sends.csv`: Send WhatsApp, follow-up batch) and the call tracker's sheet (WA_Inbox
   'out' rows), each with who sent it ("· by shavez"). The sheet is read in the background, at most every 3 minutes.
5. `clinic-portal` restarted and checked (`/portal/inbox/health` must say S599); a bad answer puts everything back.
6. **The proof, to the owner's own number only:** one text from the inbox, one approved template (Post-visit, name "Test").

Replies typed in **MyOperator's own app** reach the server only once MyOperator's "message sent" webhook is switched on
in its panel; the inbox already reads them when they come.

**Rehearsed (S329)** on a stand-in server tree with a stand-in MyOperator that accepts one key and refuses another:
the refused key reported, the working one chosen, the switch flipped and read back, the portal's stale key replaced,
the two proof messages sent with the working key, the portal log's LIVE rows brought in (DRY rows not), the sheet's
failure reported quietly, a second run changing nothing, `--undo`, and the control (an inbox that will not load →
everything put back).
