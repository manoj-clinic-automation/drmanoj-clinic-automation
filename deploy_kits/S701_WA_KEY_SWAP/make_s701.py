#!/usr/bin/env python3
"""make_s701.py -- kit S701_WA_KEY_SWAP (the parent, S382, 03-Nov-2026). Builds the new /root/portal/portal_inbox.py from
the live one (58d5318e) by counted edits; the installer re-runs it on the box's live file and the result must be the
kit's own copy byte for byte.
  python3 make_s701.py <live portal_inbox.py> <out>
THE CHANGE (the owner, 02-Nov 14:27 IST: 'it's been 2 weeks, need to sort it out on top priority'; START_HERE_SESSION_382 B2):
a send MyOperator's gateway refuses at its authorizer is tried again until the patient's 24-hour window closes -- every
2 minutes in the first hour, every 10 minutes after -- not given up after 60 minutes. Nothing else changes: any other
failure is shown at once and never retried; the give-up mail ('NOT delivered') still goes when the window closes."""
import hashlib, sys

FROM = "58d5318eff3e880112d26d2f30c3c910"
EDITS = [
    # 1 -- the constants
    ("RETRY_GAP_MIN = 2\nRETRY_FOR_MIN = 60\nRETRY_STUCK_MIN = 10\n",
     "RETRY_GAP_MIN = 2\n"
     "RETRY_FOR_MIN = 24 * 60                 # S701: until the patient's 24-hour window closes (the window check decides)\n"
     "RETRY_SLOW_AFTER_MIN = 60               # S701: after the first hour ...\n"
     "RETRY_SLOW_GAP_MIN = 10                 # ... a try every 10 minutes\n"
     "RETRY_STUCK_MIN = 10\n\n\n"
     "def retry_gap(first, now):\n"
     "    \"\"\"S701: minutes to the next try -- 2 in the first hour, 10 after.\"\"\"\n"
     "    if first and now - first >= datetime.timedelta(minutes=RETRY_SLOW_AFTER_MIN):\n"
     "        return RETRY_SLOW_GAP_MIN\n"
     "    return RETRY_GAP_MIN\n", 1),
    # 2 -- the give-up words of the hard cap
    ('ok, mid, err = False, "", "an hour of retrying is over"',
     'ok, mid, err = False, "", "24 hours of retrying are over"', 1),
    # 3 -- the next try's time
    ("(iso(now + datetime.timedelta(minutes=RETRY_GAP_MIN)), (err or \"\")[:300], j[\"id\"]))",
     "(iso(now + datetime.timedelta(minutes=retry_gap(first, now))), (err or \"\")[:300], j[\"id\"]))", 1),
    # 4 -- the docstring of the pass
    ("other bookkeeping; a job older than RETRY_FOR_MIN is given up BEFORE any call;",
     "other bookkeeping; a job whose patient's 24-hour window has closed (S701; or older than RETRY_FOR_MIN) is given up\n"
     "    BEFORE any call;", 1),
    # 5 -- the queue's docstring
    ("inbox_retry.py tries again every RETRY_GAP_MIN minutes for RETRY_FOR_MIN minutes.\"\"\"",
     "inbox_retry.py tries again every RETRY_GAP_MIN minutes (RETRY_SLOW_GAP_MIN after the first hour) until the\n"
     "        patient's 24-hour window closes (S701).\"\"\"", 1),
    # 6 -- the words shown on the page when a send is kept
    ("\"note\": \"MyOperator is refusing for the moment. The server will try again every %d minutes \"\n"
     "                                \"for up to %d minutes.\" % (RETRY_GAP_MIN, RETRY_FOR_MIN)})",
     "\"note\": \"MyOperator is refusing for the moment. The server will try again by itself every %d \"\n"
     "                                \"minutes (every %d after the first hour) until the patient's 24-hour window closes.\" % (\n"
     "                                    RETRY_GAP_MIN, RETRY_SLOW_GAP_MIN)})", 1),
    # 7 -- the health route names this kit
    ('return jsonify({"inbox": "ok", "kit": "S666"})', 'return jsonify({"inbox": "ok", "kit": "S701"})', 1),
    # 9 -- a photo / PDF / voice note's link is kept alive while its send is retried (cold review R1, blocker 1: the link
    #      lives INBOX_LINK_HOURS (6 h); a retry accepted after that would make MyOperator fetch a dead link)
    ("def retry_gap(first, now):\n",
     "def refresh_link(c, data_json, cfg_get):\n"
     "    \"\"\"S701: before a retry of a photo / PDF / voice note, its public link is given INBOX_LINK_HOURS from NOW again, so\n"
     "    MyOperator can still fetch the file when it accepts the send. Never raises.\"\"\"\n"
     "    try:\n"
     "        link = str(((json.loads(data_json) or {}).get(\"context\") or {}).get(\"link\") or \"\")\n"
     "        m = re.search(r\"/portal/inbox/f/([0-9a-f]{32})/\", link)\n"
     "        if not m:\n"
     "            return False\n"
     "        hours = float(cfg_get(\"INBOX_LINK_HOURS\", \"\") or 6)\n"
     "        c.execute(\"UPDATE links SET expires=? WHERE token=?\", (iso(now_ist() + datetime.timedelta(hours=hours)), m.group(1)))\n"
     "        c.commit()\n"
     "        return True\n"
     "    except Exception:                                                   # noqa: BLE001\n"
     "        return False\n\n\n"
     "def retry_gap(first, now):\n", 1),
    ("            else:\n                try:\n                    ok, mid, err = send(token, j[\"phone\"], json.loads(j[\"data\"]), trace=tr)",
     "            else:\n                refresh_link(c, j[\"data\"], cfg_get)       # S701: the file's link alive for this try\n"
     "                try:\n                    ok, mid, err = send(token, j[\"phone\"], json.loads(j[\"data\"]), trace=tr)", 1),
    # 8 -- the header's record of the change
    ("import os, re, json, time, uuid, sqlite3, secrets, hashlib, threading, mimetypes, datetime, urllib.request, urllib.error\n",
     "# S701 (03-Nov-2026, the parent S382): a send refused at MyOperator's authorizer is retried until the patient's 24-hour\n"
     "# window closes (every 2 min in the first hour, every 10 after), not for 60 minutes only;\n"
     "# a photo / PDF / voice note's link is renewed before each retry (it lives 6 h). Nothing else changed.\n"
     "import os, re, json, time, uuid, sqlite3, secrets, hashlib, threading, mimetypes, datetime, urllib.request, urllib.error\n", 1),
]


def build(src):
    if hashlib.md5(src).hexdigest() != FROM:
        raise SystemExit("make_s701: the live file is %s, not %s" % (hashlib.md5(src).hexdigest()[:8], FROM[:8]))
    t = src.decode("utf-8")
    for i, (old, new, n) in enumerate(EDITS, 1):
        c = t.count(old)
        if c != n:
            raise SystemExit("make_s701: edit %d expects %d place(s), found %d" % (i, n, c))
        t = t.replace(old, new)
    return t.encode("utf-8")


if __name__ == "__main__":
    out = build(open(sys.argv[1], "rb").read())
    open(sys.argv[2], "wb").write(out)
    print("make_s701: %d edits, %s" % (len(EDITS), hashlib.md5(out).hexdigest()))
