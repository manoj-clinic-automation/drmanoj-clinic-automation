#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_s497.py -- kit S497_RING_LIST: tile_grants.json v32 -> v33, by exact text on the live bytes (F-472).

    python3 -B apply_s497.py <path to a COPY of tile_grants.json>     edits that file in place
    python3 -B apply_s497.py --pins                                   prints: FROM TO

v33: the NEW tile 'Call ke baad' (/portal/ring/list) BY NAME to alisha, shivani, shavez and reception -- the four who hold
'Call Tracker' -- placed right after it in each one's list. The doctor holds it by role. Nothing else in the file moves:
the result is read back as JSON, the tile is taken out again and what is left must equal v32, and its md5 must be the
pin below. Pinned to the md5 it starts from; a file already at v33 is left exactly as it is (running it twice is safe).
The new text is built and checked in memory before the file is opened for writing (F-792).
A .json is not shipped in the kit (.gitignore blocks *.json; F-751) -- which is why this is a script."""
import hashlib
import json
import os
import sys

FROM = "f9441311cd413bc4c12e9d4e23feb791"
TO = "64f8b04937e8841c405cb9070b604aad"
TILE = "Call ke baad"
WHO = ("alisha", "shivani", "shavez", "reception")
NOTE = (" | v33 (S497, 08-Oct-2026, D693, PARENT): the NEW tile 'Call ke baad' (/portal/ring/list -- what is filed after a "
        "call as ONE table in three parts: Nahi aaye, kept until it is dealt with; Aane baaki; Aa gaye, filled by itself "
        "from the Docterz export) to alisha, shivani, shavez and reception, the four who hold 'Call Tracker'; the doctor "
        "holds it by role. The list is installed OFF for staff: until the doctor turns it on from the page, portal.py "
        "draws this tile for no staff login and their card after the tap is the old one. The page's own gate reads THIS "
        "file: who is shown the tile may open the page. Nothing else in this file moves.")


def md5(b):
    return hashlib.md5(b).hexdigest()


def rep(s, old, new):
    if s.count(old) != 1:
        raise SystemExit("!! apply_s497: the place %r occurs %d times, not once -- nothing written" % (old[:60], s.count(old)))
    return s.replace(old, new)


def build(raw):
    """v32 bytes -> v33 bytes, checked. Writes nothing."""
    s = raw.decode("utf-8")
    for u in WHO:
        s = rep(s, '    "%s": {\n      "extra": [\n        "Call Tracker",\n' % u,
                '    "%s": {\n      "extra": [\n        "Call Tracker",\n        "%s",\n' % (u, TILE))
    s = rep(s, 'Nothing else in this file moves.",\n  "version": 32,\n',
            'Nothing else in this file moves.%s",\n  "version": 33,\n' % NOTE.replace("\\", "\\\\").replace('"', '\\"'))
    out = s.encode("utf-8")
    new, old = json.loads(s), json.loads(raw.decode("utf-8"))
    if new.get("version") != 33 or not all(TILE in new["users"][u]["extra"] for u in WHO):
        raise SystemExit("!! apply_s497: the result is not v33 with the tile for the four -- nothing written")
    if [u for u, d in new["users"].items() if TILE in (d.get("extra") or [])] != [u for u in new["users"] if u in WHO]:
        raise SystemExit("!! apply_s497: the tile reached a login it was not meant for -- nothing written")
    for u in WHO:
        ex = new["users"][u]["extra"]
        if ex[ex.index(TILE) - 1] != "Call Tracker":
            raise SystemExit("!! apply_s497: the tile is not right after Call Tracker for %s -- nothing written" % u)
        ex.remove(TILE)
    if not new["_note"].startswith(old["_note"]):
        raise SystemExit("!! apply_s497: the note was not only added to -- nothing written")
    new["version"], new["_note"] = old["version"], old["_note"]
    if new != old:
        raise SystemExit("!! apply_s497: something else moved -- nothing written")
    if not TO.startswith("@@") and md5(out) != TO:
        raise SystemExit("!! apply_s497: the result is %s, not %s -- nothing written" % (md5(out), TO))
    return out


def main(argv):
    if argv == ["--pins"]:
        print(FROM, TO)
        return 0
    if len(argv) != 1:
        print(__doc__)
        return 2
    path = argv[0]
    with open(path, "rb") as fh:
        raw = fh.read()
    if md5(raw) == TO:
        print("tile_grants.json is already v33 (%s) -- left as it is" % TO[:8])
        return 0
    if md5(raw) != FROM:
        print("!! apply_s497: this file is %s, not v32 (%s) -- it changed since this kit was built; nothing written" % (md5(raw), FROM))
        return 1
    out = build(raw)
    tmp = path + ".s497_new"
    with open(tmp, "wb") as fh:
        fh.write(out)
    os.replace(tmp, path)
    print("tile_grants.json v32 -> v33  %s -> %s" % (FROM[:8], md5(out)[:8]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
