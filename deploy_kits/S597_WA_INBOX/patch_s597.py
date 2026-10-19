#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patch_s597.py -- kit S597_WA_INBOX (session S329, 19-Oct-2026) · D744 -- the three small edits to live files.

    python3 -B patch_s597.py            -- check every pin and anchor, keep the three files, write, read back
    DRY=1 python3 -B patch_s597.py      -- check every pin and anchor; change nothing
    python3 -B patch_s597.py --undo     -- put the three files back from /root/s597_backup/

Each file is changed ONLY if it is byte-for-byte the file this kit was built from (the 19-Oct 03:12 IST nightly bundle),
and the result must be byte-for-byte the file the rehearsal produced. Anything else: stop, nothing changed.

  /root/portal/portal.py         -- the "WhatsApp Inbox" tile (doctor role; the inbox itself checks wa_required), its group
                                    entry, bhawna's code-fallback mask, and the register block for portal_inbox (a failure
                                    to load costs that page alone, like portal_wa's own block above it)
  /root/portal/tile_grants.json  -- "WhatsApp Inbox" added to bhawna's mask; version 36 -> 37
  /root/wa/wa_alert.py           -- the ntfy alert carries a Click link: tapping it opens that chat in the inbox
"""
import os, sys, json, shutil, hashlib

BK = os.environ.get("S597_BACKUP", "/root/s597_backup")
ROOT = os.environ.get("S597_ROOT", "")            # rehearsal only: a folder that stands in for /
DRY = os.environ.get("DRY", "0") == "1"

FILES = {
    "portal": ("/root/portal/portal.py", "25cb73e7869813a56df1f0bef6c0dce5", None),
    "grants": ("/root/portal/tile_grants.json", "e54f59db715d73f1ba7f4dcccfbd9fdb", None),
    "alert": ("/root/wa/wa_alert.py", "e7d0b766090b718a81f9f63f05fb4c6a", None),
}
WANT = {}   # filled below: the md5 each file must have after the edit (from the rehearsal)

P_TILE_OLD = '''    {"icon": "\\U0001F4AC", "name": "Send WhatsApp",
     "desc": "Approved templates \\u00b7 clinic number \\u00b7 any patient", "live": True,
     "url": "/portal/wa",
     "roles": ["doctor"]},
'''
P_TILE_NEW = '''    # S597 (D744, 19-Oct-2026): the owner's WhatsApp Inbox -- every chat, photos / PDFs / voice inline, replies, call.
    # Owner only: the page checks wa_required; the tile is masked for bhawna in tile_grants.json.
    {"icon": "\\U0001F4E5", "name": "WhatsApp Inbox",
     "desc": "Chats \\u00b7 photos \\u00b7 voice \\u00b7 reply \\u00b7 call", "live": True,
     "url": "/portal/inbox",
     "roles": ["doctor"]},

''' + P_TILE_OLD
P_GROUP_OLD = '''    "Call ke baad": "Calls & WhatsApp", "Send WhatsApp": "Calls & WhatsApp",
'''
P_GROUP_NEW = '''    "Call ke baad": "Calls & WhatsApp", "Send WhatsApp": "Calls & WhatsApp", "WhatsApp Inbox": "Calls & WhatsApp",
'''
P_MASK_OLD = '''    "bhawna": {"GMB Review Assist", "Vitals & Plan", "Surgical Case Pack", "Send WhatsApp", "Follow-up WhatsApps",
'''
P_MASK_NEW = '''    "bhawna": {"GMB Review Assist", "Vitals & Plan", "Surgical Case Pack", "Send WhatsApp", "Follow-up WhatsApps",
               "WhatsApp Inbox",
'''
P_REG_OLD = '''

try:
    import portal_followups
'''
P_REG_NEW = '''

# S597 (D744, 19-Oct-2026): the owner's WhatsApp Inbox -- its own module (portal_inbox.py) behind the same WhatsApp gate.
# A failure to load costs this one page, never the portal.
try:
    import portal_inbox
    portal_inbox.register(
        app, wa_required,
        lambda: ((_sso_user(request) or {}).get("user") or "doctor"),
        _cfg_get)
    INBOX_IMPORT_ERR = ""
except Exception as _ib_e:
    INBOX_IMPORT_ERR = str(_ib_e)

    @app.route("/portal/inbox")
    @login_required
    def _inbox_broken():
        return make_response("WhatsApp Inbox failed to load: " + INBOX_IMPORT_ERR, 500)


try:
    import portal_followups
'''

A_POST_OLD = '''def _post(url, title, body, priority="high", tags="speech_balloon"):
    """One HTTP POST to ntfy. True on 2xx. The walk replaces this function."""
    req = urllib.request.Request(url, data=body.encode("utf-8"), method="POST")
    req.add_header("Title", ascii_title(title) or "New WhatsApp")
    req.add_header("Priority", priority)
    req.add_header("Tags", tags)
'''
A_POST_NEW = '''def _post(url, title, body, priority="high", tags="speech_balloon", click=""):
    """One HTTP POST to ntfy. True on 2xx. The walk replaces this function."""
    req = urllib.request.Request(url, data=body.encode("utf-8"), method="POST")
    req.add_header("Title", ascii_title(title) or "New WhatsApp")
    req.add_header("Priority", priority)
    req.add_header("Tags", tags)
    if click:                                                      # S597 (D744): tapping the alert opens the chat
        req.add_header("Click", click)
'''
A_SEND_OLD = '''def _send(item):
    url = _topic_url()
'''
A_SEND_NEW = '''def _click(item):
    """S597 (D744): the owner's WhatsApp Inbox, opened at this message's chat. The link carries the message id, no number."""
    try:
        from urllib.parse import quote
        base = _env("INBOX_PUBLIC_BASE", "https://followup.dr-manoj.in").rstrip("/")
        mid = str(item.get("mid") or "").strip()
        return base + "/portal/inbox" + (("?m=" + quote(mid, safe="")) if mid else "")
    except Exception:                                              # noqa: BLE001
        return ""


def _send(item):
    url = _topic_url()
'''
A_CALL_OLD = '''        if _post(url, title, body):
'''
A_CALL_NEW = '''        if _post(url, title, body, click=_click(item)):
'''
A_Q_OLD = '''        _q.put({"phone": phone, "text": text})
'''
A_Q_NEW = '''        _q.put({"phone": phone, "text": text, "mid": mid})
'''

EDITS = {
    "portal": [(P_TILE_OLD, P_TILE_NEW), (P_GROUP_OLD, P_GROUP_NEW), (P_MASK_OLD, P_MASK_NEW), (P_REG_OLD, P_REG_NEW)],
    "alert": [(A_POST_OLD, A_POST_NEW), (A_SEND_OLD, A_SEND_NEW), (A_CALL_OLD, A_CALL_NEW), (A_Q_OLD, A_Q_NEW)],
}
WANT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "AFTER.md5")


def die(msg):
    print("!! STOPPED: %s" % msg)
    print("   Nothing was changed. Send a photo of this screen to Claude.")
    sys.exit(1)


def md5b(b):
    return hashlib.md5(b).hexdigest()


def path(p):
    return (ROOT.rstrip("/") + p) if ROOT else p


def new_bytes(key, old):
    if key == "grants":
        d = json.loads(old.decode("utf-8"))
        mask = d["users"]["bhawna"]["mask"]
        if "WhatsApp Inbox" not in mask:
            mask.append("WhatsApp Inbox")
        if d.get("version") != 36:
            raise ValueError("tile_grants.json is not version 36")
        d["version"] = 37
        return (json.dumps(d, indent=1, ensure_ascii=False) + "\n").encode("utf-8")
    s = old.decode("utf-8")
    for a, b in EDITS[key]:
        if s.count(a) != 1:
            raise ValueError("an anchor is not found exactly once in %s: %r" % (FILES[key][0], a.strip()[:60]))
        s = s.replace(a, b)
    return s.encode("utf-8")


def main():
    want = {}
    if os.path.exists(WANT_FILE):
        for line in open(WANT_FILE):
            h, _, k = line.strip().partition("  ")
            if k:
                want[k] = h
    if "--undo" in sys.argv:
        for key, (p, pin, _) in FILES.items():
            b = os.path.join(BK, os.path.basename(p) + ".before_s597")
            if not os.path.exists(b):
                print("  %s: no backup -- left as it is" % p)
                continue
            shutil.copy2(b, path(p))
            print("  %s: put back (%s)" % (p, md5b(open(path(p), "rb").read())[:8]))
        print("UNDONE.")
        return
    plan = {}
    for key, (p, pin, _) in FILES.items():
        fp = path(p)
        if not os.path.exists(fp):
            die("%s is not there" % p)
        old = open(fp, "rb").read()
        now = md5b(old)
        if want.get(p) and now == want[p]:
            print("  %s: already carries the S597 edit (%s) -- left as it is" % (p, now[:8]))
            continue
        if now != pin:
            die("%s is not the file this kit was built from (%s, expected %s) -- someone changed it since 19-Oct 03:12" % (p, now[:8], pin[:8]))
        try:
            nb = new_bytes(key, old)
        except ValueError as e:
            die(str(e))
        if want.get(p) and md5b(nb) != want[p]:
            die("the edit of %s does not come out as rehearsed (%s, expected %s)" % (p, md5b(nb)[:8], want[p][:8]))
        plan[key] = (fp, old, nb)
        print("  %s: pin %s matched -> will become %s" % (p, pin[:8], md5b(nb)[:8]))
    if DRY or not plan:
        print("-- DRY: nothing changed" if DRY else "-- nothing to change")
        return
    os.makedirs(BK, mode=0o700, exist_ok=True)
    for key, (fp, old, nb) in plan.items():
        b = os.path.join(BK, os.path.basename(FILES[key][0]) + ".before_s597")
        if not os.path.exists(b):
            with open(b, "wb") as fh:
                fh.write(old)
            os.chmod(b, 0o600)
    for key, (fp, old, nb) in plan.items():
        st = os.stat(fp)
        tmp = fp + ".s597tmp"
        with open(tmp, "wb") as fh:
            fh.write(nb)
        os.chmod(tmp, st.st_mode & 0o7777)
        os.replace(tmp, fp)
        back = md5b(open(fp, "rb").read())
        print("  %s: written and read back (%s)" % (FILES[key][0], back[:8]))
        if back != md5b(nb):
            die("%s did not read back as written" % FILES[key][0])
    print("PATCHED.")


if __name__ == "__main__":
    main()
