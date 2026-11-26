#!/usr/bin/env python3
"""make_s959.py -- S959_STAFF_WHATSAPP: remakes the three TO files from the FROM bytes (never from a guess).

  python make_s959.py <calls_staff.py FROM> <calls_console.py FROM> <portal_inbox.py FROM> <out dir>

  calls_staff.py   a93cdc86 (S955)  -> the WhatsApp tab's reply (13 pieces, cs_parts.py; each anchor found exactly once)
  calls_console.py f484cbc2 (S948)  -> one script line: his Accept on a verdict dispute reads "Accepted — the verdict was wrong"
  portal_inbox.py  6abc6461 (S871)  -> the FROM bytes unchanged + pi_block.txt appended (three callables; the routes untouched)
Refuses (exit 2) when a FROM is not the expected bytes or an anchor is missing / doubled.
"""
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cs_parts  # noqa: E402

FROM = {"calls_staff.py": "a93cdc86b9870e6c6f92738cd95a2b22", "calls_console.py": "f484cbc23e85817c32cd7a6c9004dd3e",
        "portal_inbox.py": "6abc6461846a408b47f7f4ceff493c21"}
CC_OLD = "b.textContent=(ans==='accept'?'Accepted — off the count':'It stands ✓'); b.classList.add('done');"
CC_NEW = ("b.textContent=(ans==='accept'?(b.textContent.indexOf('verdict')>=0?'Accepted — the verdict was wrong':"
          "'Accepted — off the count'):'It stands ✓'); b.classList.add('done');")


def die(msg):
    print("REFUSED: " + msg)
    sys.exit(2)


def rd(p, name):
    b = open(p, "rb").read()
    if hashlib.md5(b).hexdigest() != FROM[name]:
        die("%s is %s, not the FROM %s" % (name, hashlib.md5(b).hexdigest()[:8], FROM[name][:8]))
    return b.decode("utf-8")


def put(s, old, new, what):
    n = s.count(old)
    if n != 1:
        die("%s: anchor found %d times: %r" % (what, n, old[:70]))
    return s.replace(old, new, 1)


def main(a):
    if len(a) != 4:
        die("usage: make_s959.py <calls_staff> <calls_console> <portal_inbox> <out dir>")
    cs, cc, pi = rd(a[0], "calls_staff.py"), rd(a[1], "calls_console.py"), rd(a[2], "portal_inbox.py")
    for i, (o, n) in enumerate(cs_parts.PARTS):
        cs = put(cs, o, n, "calls_staff piece %d" % (i + 1))
    cc = put(cc, CC_OLD, CC_NEW, "calls_console Accept label")
    blk = open(os.path.join(HERE, "pi_block.txt"), encoding="utf-8").read()
    if "def staff_send_text" in pi:
        die("portal_inbox.py already holds staff_send_text")
    pi = pi + blk
    os.makedirs(a[3], exist_ok=True)
    for name, s in (("calls_staff.py", cs), ("calls_console.py", cc), ("portal_inbox.py", pi)):
        with open(os.path.join(a[3], name), "wb") as fh:
            fh.write(s.encode("utf-8"))
        print("%s %s" % (hashlib.md5(s.encode("utf-8")).hexdigest(), name))


if __name__ == "__main__":
    main(sys.argv[1:])
