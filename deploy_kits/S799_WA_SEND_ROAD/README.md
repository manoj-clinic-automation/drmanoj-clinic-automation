# S799_WA_SEND_ROAD — why the tracker's WhatsApp goes and the Inbox's does not (F-1031)

**The owner, 12-Nov-2026 11:25 IST:** *"google app script call back tracker whatsapp section is sending whatsapp thru api while
my inbox is failing."*

**What was read.** The tracker's WhatsApp box sends through the server's relay (`/wa-send` → `/root/wa/wa_send.py`, Python's
`http.client`). The Inbox (`portal_inbox.myop_send`) and the portal's template sender (`portal_wa.send`) post to the **same**
MyOperator address with the **same** four headers, through `urllib`. On the wire the two differ only in what urllib adds by
itself (its own `User-Agent: Python-urllib/3.x`, and `Connection: close`). The Inbox's own log, 30 days: first tries 10
accepted / 27 refused (HTTP 500 at their authorizer), none accepted on a first try since 30-Oct; retries 5 of 658. His test
template of 11:31 IST through the portal's sender was refused the same way (nothing sent).

**The kit asks before it changes anything.** `probe_s799.py` — **sends nothing**: a made-up key, and the real key with an
EMPTY number and EMPTY text, four ways (urllib as today · urllib with a plain User-Agent · http.client as the relay ·
http.client with urllib's User-Agent), three rounds each; it prints a table and a verdict. It also counts the relay's own
record since 1 Nov (sent / not sent — counts only).

- **Only on the verdict `DECISIVE-UA`** (urllib's way refused, the same call with a plain User-Agent accepted) the installer
  adds **one line** in each sender — `req.add_header("User-Agent", "clinic-portal/1.0")`:
  `/root/portal/portal_inbox.py` 06e2c28e → ab5df207 · `/root/portal/portal_wa.py` 34994b23 → 0964c598; restarts the portal;
  then tries the INSTALLED Inbox sender three times (real key, empty number, empty text): still refused → both files go back.
- **Any other verdict:** nothing is changed; the table is printed for the next step (and for MyOperator's ticket 691386).

After a DONE, replies still waiting in the Inbox's retry queue go out by themselves within 2 minutes (the S666 retry, while
the patient's 24-hour window is open). The retry rule itself is untouched: a real refusal is still seen and tried again.

**The kit carries no copy of the two files** — `portal_wa.py` holds the clinic's number in its page text and no number
goes into the repository (F-185; the number gate refused the first placing). The installer makes both on the box with
`make_s799.py` from the live bytes and checks the result against the pins before anything else.

Built by `make_s799.py` on the live bytes (the 12-Nov bundle). **Walk** 17/17 against a stand-in gateway on the same machine
that answers as MyOperator's does in F-1031; the CONTROL red on the live files (6 of 17).

**Install** (after the publish), one line on the server:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s799kit && cp -rp /root/deploy/repo/deploy_kits/S799_WA_SEND_ROAD /tmp/s799kit && bash /tmp/s799kit/install_S799_WA_SEND_ROAD.sh
```
Undo: `bash /tmp/s799kit/install_S799_WA_SEND_ROAD.sh --undo`.
