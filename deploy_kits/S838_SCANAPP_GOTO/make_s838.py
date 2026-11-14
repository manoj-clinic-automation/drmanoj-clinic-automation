#!/usr/bin/env python3
"""make_s838.py -- kit S838_SCANAPP_GOTO: sorting_desk.py from its pinned bytes (S835s TO, d49e48ff) by exact, counted edits.
usage: python3 make_s838.py <base dir> <block dir> <out dir>"""
import hashlib, os, sys
BASE, BLK, OUT = sys.argv[1:4]
PIN = "d49e48ff4f91a4bb190a8045e07d2354"
b = open(os.path.join(BASE, "sorting_desk.py"), "rb").read()
if hashlib.md5(b).hexdigest() != PIN:
    sys.exit("STOP: sorting_desk.py is not the pinned file %s" % PIN[:8])
t = b.decode("utf-8")
blk = open(os.path.join(BLK, "block_goto.py"), "rb").read().decode("utf-8")
n = 0
def e(old, new, what):
    global t, n
    c = t.count(old)
    if c != 1:
        sys.exit("STOP: %s -- anchor found %d times:\n%s" % (what, c, old[:160]))
    t = t.replace(old, new); n += 1
e('            ("desk.cn", "Credit notes on the desk"))                                    # S835 (absent = OFF; the owner sees it always)\n',
  '            ("desk.cn", "Credit notes on the desk"),                                    # S835 (absent = OFF; the owner sees it always)\n'
  '            ("bar.goto", "Go to menu for Shavez"))                                      # S838 (absent = OFF; the owner sees it always)\n', "G1 SWITCHES")
e('            "desk.cn": (_setting(db, "desk.cn", "off") or "").strip().lower() == "on"}               # S835\n',
  '            "desk.cn": (_setting(db, "desk.cn", "off") or "").strip().lower() == "on",               # S835\n'
  '            "bar.goto": (_setting(db, "bar.goto", "off") or "").strip().lower() == "on"}             # S838\n', "G2 switch_states")
e('    app.jinja_env.globals.update(s551_on=True, s551_switches_card=switches_card, s551_month_href=month_href)\n',
  '    app.jinja_env.globals.update(s551_on=True, s551_switches_card=switches_card, s551_month_href=month_href)\n'
  '    _s838_mount(ar)                                                  # S838: Go to ▾ on the bar (taken over at the first request)\n', "G3 init")
e('\n\n# ---------------------------------------------------------------------------------------------- the mount\ndef init(ar):\n',
  blk.rstrip("\n") + '\n\n\n# ---------------------------------------------------------------------------------------------- the mount\ndef init(ar):\n', "G4 the S838 block")
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, "sorting_desk.py"), "wb").write(t.encode("utf-8"))
print("sorting_desk.py    %s   (%d counted edits)" % (hashlib.md5(t.encode("utf-8")).hexdigest(), n))
