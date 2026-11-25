#!/usr/bin/env python3
"""make_s953.py -- S953_STAFF_NOTIFY: remake the kit's two TO files from the LIVE bytes on the box.

  python make_s953.py <live calls_staff.py> <live callback_clock.py> <out dir>

calls_staff.py 1cb4941f (S951) -> ONE exact edit (must match once; VERSION stays 'S951 1.1', which S951's walk pins): the page's script reads ?tab= before the
remembered tab and then clears it from the address (the page reloads itself every 5 minutes) (so a notification's tap opens Incoming missed / Call again / WhatsApp). callback_clock.py 70eb1197 (S796) -> the
kit's whole new file (built on those exact bytes, read whole). Refuses any other FROM. Writes nothing else."""
import hashlib
import os
import sys

CS_FROM = "1cb4941f3d387abba93f76e650d78fa1"
CB_FROM = "70eb11972362eee87a9f7d056e04cae5"
EDITS = [
    ('try{var k0=sessionStorage.getItem("s948tab");if(k0&&document.getElementById("t-"+k0))tab(k0);}catch(e){}',
     'try{var k0=null,q=0;try{k0=new URLSearchParams(location.search).get("tab");q=!!k0;}catch(e){}'
     'if(!k0||!document.getElementById("t-"+k0))k0=sessionStorage.getItem("s948tab");'
     'if(k0&&document.getElementById("t-"+k0))tab(k0);'
     'if(q&&history.replaceState)history.replaceState(null,"",location.pathname);}catch(e){}'),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def main(cs_p, cb_p, out):
    here = os.path.dirname(os.path.abspath(__file__))
    cs, cb = open(cs_p, "rb").read(), open(cb_p, "rb").read()
    if md5(cs) != CS_FROM:
        sys.exit("REFUSED: calls_staff.py is %s, not S951's %s" % (md5(cs)[:8], CS_FROM[:8]))
    if md5(cb) != CB_FROM:
        sys.exit("REFUSED: callback_clock.py is %s, not S796's %s" % (md5(cb)[:8], CB_FROM[:8]))
    s = cs.decode("utf-8")
    for old, new in EDITS:
        if s.count(old) != 1:
            sys.exit("REFUSED: an edit's anchor is found %d times (must be 1): %r" % (s.count(old), old[:60]))
        s = s.replace(old, new)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "calls_staff.py"), "wb") as fh:
        fh.write(s.encode("utf-8"))
    with open(os.path.join(here, "to", "callback_clock.py"), "rb") as fh:
        tob = fh.read()
    with open(os.path.join(out, "callback_clock.py"), "wb") as fh:
        fh.write(tob)
    print("calls_staff.py %s -> %s" % (CS_FROM[:8], md5(s.encode("utf-8"))[:8]))
    print("callback_clock.py %s -> %s" % (CB_FROM[:8], md5(tob)[:8]))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
