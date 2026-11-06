#!/usr/bin/env python3
"""make_s710.py -- S710_VIEWER_FIT: the PC scan viewer opens a PDF full width, without Chrome's thumbnail strip (one edit).
    python3 -B make_s710.py <dir holding order_track_page.py> <out dir>"""
import hashlib
import os
import sys

FROM = {"order_track_page.py": "eaa23b1fc0f5251f64b5315532710bc0"}
E_OTP = [
    ("""fr.src=f+'#view=FitH';""", """fr.src=f+'#navpanes=0&view=FitH';"""),
    ("""#s7v .vimg iframe{height:calc(100vh - 260px)}""", """#s7v .vimg iframe{height:calc(100vh - 230px)}"""),
    ("""KIT = "S708\"""", """KIT = "S708"                                                   # S710 (05-Nov): the PC viewer -- '#navpanes=0&view=FitH'"""),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def main():
    sd, od = sys.argv[1], sys.argv[2]
    os.makedirs(od, exist_ok=True)
    name = "order_track_page.py"
    raw = open(os.path.join(sd, name), "rb").read()
    if md5(raw) != FROM[name]:
        sys.exit("REFUSED: %s is %s, not the pinned %s" % (name, md5(raw)[:8], FROM[name][:8]))
    src = raw.decode("utf-8")
    for i, (a, b) in enumerate(E_OTP, 1):
        if src.count(a) != 1:
            sys.exit("REFUSED: edit %d matches %d times" % (i, src.count(a)))
        src = src.replace(a, b)
    out = src.encode("utf-8")
    open(os.path.join(od, name), "wb").write(out)
    print("%s  %s -> %s" % (name, FROM[name][:8], md5(out)))


if __name__ == "__main__":
    main()
