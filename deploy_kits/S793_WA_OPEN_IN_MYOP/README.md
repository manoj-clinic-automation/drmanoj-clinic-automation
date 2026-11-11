# S793_WA_OPEN_IN_MYOP — "Open in MyOperator" on each chat of his WhatsApp inbox

**The owner, 11-Nov-2026 17:46 IST:** an interim while the clinic's own WhatsApp sends fail (F-1031, MyOperator ticket 691386) —
from his inbox he opens the same patient's chat in MyOperator and replies there.

`/root/portal/portal_inbox.py` f89ad282 (S701) → TO: the chat header gets a white-outlined **MyOperator** button before **Call**
(on a narrow phone only its icon shows). It opens, in a new tab, MyOperator's own page for that patient's chat:
`https://in.app.myoperator.com/chat/<the clinic number's id>/91/<the 10 digits>` — the address read from MyOperator's app at S431 and
proven in his signed-in browser on three patients' numbers (each opened that patient's own conversation; the name matched).
A chat whose number is shorter than 10 digits gets no button. Nothing that sends, reads or stores messages changes; the health
answer now names S793. No database is touched.

**Walk** 13/13 (static, no import); the CONTROL red on the live file (9 of 13); the page's script passes `node --check`;
rendered in Chromium with made-up chats at 1200 px and 375 px: the link, new tab, `rel=noopener`, before Call, no overflow, no
script error, no button and no "null" for a short number.

**Install** (after the publish), one line on the server:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s793kit && cp -rp /root/deploy/repo/deploy_kits/S793_WA_OPEN_IN_MYOP /tmp/s793kit && bash /tmp/s793kit/install_S793_WA_OPEN_IN_MYOP.sh
```
Undo: `bash /tmp/s793kit/install_S793_WA_OPEN_IN_MYOP.sh --undo`.
