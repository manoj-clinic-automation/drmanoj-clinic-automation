#!/usr/bin/env python3
"""make_s742.py -- S742_CALLS_R3 (the parent, S397, 07-Nov-2026). Counted edits on two live files, each anchor
required EXACTLY ONCE; anything else STOPS with nothing written. Run on the box by install.sh; the walk runs it too.

  /root/wa/portal_console.py   (FROM 3317394c)  +build_fu_all() after build_no_shows, +its call in cmd_build
  /root/portal/portal.py       (FROM 5cf80f82)  the 'Follow-up WhatsApps' tile opens the cleaned list (F-1107)

usage: make_s742.py <portal_console.py> <portal.py> <out_dir> [--expect]
"""
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FROM = {"portal_console.py": "3317394c", "portal.py": "5cf80f82"}
TO = {"portal_console.py": "a8d050ef8c9e78b57467b58a68789841", "portal.py": "d52261a25791fb00bfdc6cbfcb44a124"}


def md5(b):
    return hashlib.md5(b).hexdigest()


def edit(text, anchor, new, where):
    n = text.count(anchor)
    if n != 1:
        raise SystemExit("STOP: anchor for %s found %d times (want 1) -- nothing written" % (where, n))
    return text.replace(anchor, new)


def main(a):
    if len(a) < 3:
        raise SystemExit(__doc__)
    pc_path, portal_path, out = a[0], a[1], a[2]
    expect = "--expect" in a
    pc = open(pc_path, "rb").read()
    po = open(portal_path, "rb").read()
    for name, b in (("portal_console.py", pc), ("portal.py", po)):
        if md5(b)[:8] != FROM[name]:
            raise SystemExit("STOP: %s is %s, not the FROM %s -- nothing written" % (name, md5(b)[:8], FROM[name]))
    block = open(os.path.join(HERE, "fu_all_block.txt"), "r", encoding="utf-8").read()
    call = open(os.path.join(HERE, "fu_all_call.txt"), "r", encoding="utf-8").read()
    t = pc.decode("utf-8")
    t = edit(t, "\ndef unjudged_reason(has_join_key, has_recording, verdict):\n",
             "\n" + block + "def unjudged_reason(has_join_key, has_recording, verdict):\n", "build_fu_all")
    t = edit(t, "    # (S171: sheet push of send-backs removed -- F-76 withdrawn, reviews db is\n",
             call + "    # (S171: sheet push of send-backs removed -- F-76 withdrawn, reviews db is\n", "the fu_all call")
    p = po.decode("utf-8")
    p = edit(p, '''    {"icon": "\\U0001F4E3", "name": "Follow-up WhatsApps",
     "desc": "Today's due list \\u00b7 batch send by section", "live": True,
     "url": "/portal/wa/followups",''',
             '''    {"icon": "\\U0001F4E3", "name": "Follow-up WhatsApps",
     "desc": "The follow-up list, cleaned \\u00b7 on the Call Console", "live": True,
     "url": "/portal/console#followups",''', "the tile")
    nb = {"portal_console.py": t.encode("utf-8"), "portal.py": p.encode("utf-8")}
    os.makedirs(out, exist_ok=True)
    for name, b in nb.items():
        if expect and not TO[name].startswith("@@") and md5(b) != TO[name]:
            raise SystemExit("STOP: the made %s is %s, not the TO %s -- nothing written" % (name, md5(b)[:8], TO[name][:8]))
    for name, b in nb.items():
        with open(os.path.join(out, name), "wb") as fh:
            fh.write(b)
        print("made %s %s -> %s" % (name, FROM[name], md5(b)[:8]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
