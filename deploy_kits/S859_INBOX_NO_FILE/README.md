# S859_INBOX_NO_FILE — the Inbox says when MyOperator never gave a file; its file route never errors bare (the parent, S478, 17-Nov-2026) — F-1358's page half, F-1366, D964

**The gaps.** (F-1358) On 12-Nov two incoming files (a photo, a PDF) were pushed once with no link and never again; the Inbox
shows "(document — the file has not arrived yet)" for good. (F-1366) The Inbox's file route catches only URLError: a link
with a space or a non-English letter, or a read timeout, gives a bare Internal Server Error tab.

**The change** (`/root/portal/portal_inbox.py` 973cc74f → ff0f02a8, one file):
- an incoming photo / PDF / voice note with no link and no local copy **10 minutes** after it came is drawn as
  "(document — MyOperator did not give this file)" with an **Open in MyOperator** link (the chat's own MyOperator address);
  for the first 10 minutes the old "has not arrived yet" line stays;
- the Inbox's health answer (`/portal/inbox/health`) keeps `inbox: ok`, `kit: S793` and adds `no_file_30d` — how many such
  rows in the last 30 days (a number only, no name, no number);
- the file route fetches the stored link **percent-encoded** (a space or a non-English letter; the host is never changed and
  must still be on the list), and a read timeout, an invalid link or a refused fetch answers **502 with a plain sentence**
  ("The file could not be fetched from MyOperator just now…"), never a bare 500.

**Proof.** `walk_s859.py` runs the file in a throw-away Flask app on a made-up store with a stand-in fetch (no network, no
real data): the 10-minute rule and its exceptions, the chat answer, the page opened (200) with the new line and link and its
script through `node --check`, the health count (a 40-day-old row out), the encoded fetches, 502 for timeout / invalid /
refused / non-ASCII, 404 for a host not on the list (24/24). Control: the live file goes red. The installer (S802/S816's
pattern): doors before and after the restart, the Inbox's health carrying the new count, the journal; any red puts it back.

**Install** (after the publish): the S478 combined line, or alone:
`cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s859kit && cp -rp /root/deploy/repo/deploy_kits/S859_INBOX_NO_FILE /tmp/s859kit && bash /tmp/s859kit/install_S859_INBOX_NO_FILE.sh`
Undo: `bash /tmp/s859kit/install_S859_INBOX_NO_FILE.sh --undo`.
