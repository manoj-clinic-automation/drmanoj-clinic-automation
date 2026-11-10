#!/usr/bin/env python3
"""make_s776.py -- S776_XRAY_FEWER_LEFT (the parent, S422, 10-Nov-2026): the owner 13:01 IST, "I do not want to leave any work for
staff in Check karein as much as possible". Five counted edits on the LIVE bytes (/root/finance/records.py bfd5b845 = S772's TO),
each anchor found exactly once, plus the S776 block appended (s776_block.py).
usage: make_s776.py <live records.py> <out_dir>"""
import hashlib
import os
import sys

FROM_MD5 = "bfd5b845d2218ba93cd04791f9b6505d"
HERE = os.path.dirname(os.path.abspath(__file__))


def md5(b):
    return hashlib.md5(b).hexdigest()


def edit(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.exit("STOP: anchor %s found %d times (must be 1)" % (label, n))
    return text.replace(old, new, 1)


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if len(a) != 2:
        sys.exit(__doc__)
    raw = open(a[0], "rb").read()
    if md5(raw) != FROM_MD5:
        sys.exit("STOP: records.py is %s, not the FROM %s" % (md5(raw)[:8], FROM_MD5[:8]))
    t = raw.decode("utf-8")
    t = edit(t, "Flask, requests and the standard library. No patient name, no number, no secret in this file (F-185).\n",
             "S776 (S422, 10-Nov-2026, the owner's 'no work for staff in Check karein as much as possible'): a parked picture nothing\n"
             "else placed is filed by the film's ID with a whole-word name and no one-digit neighbour that day, by a whole-word name\n"
             "shared with ONE X-ray patient of the day whose photo is missing, or on a patient who came that day with no X-ray billed.\n"
             "Flask, requests and the standard library. No patient name, no number, no secret in this file (F-185).\n", "E1 doc")
    t = edit(t, "        if x != cid and film and _s772_strict(con, x, orig):\n"
                "            d = _s772_match(con, x, film)\n"
                "            if d and d != first:\n",
             "        if x != cid and film:\n"
             "            d = _s772_match(con, x, film)\n"
             "            if d and d != first and _s776_ok(con, x, orig, d, cache):   # S776: strict, or a whole word and no neighbour ID\n",
             "E2 film ID day")
    t = edit(t, "        if fids and cid not in fids:\n"
                "            return \"\", \"\"                                # the film prints another ID: a person decides\n"
                "        if cid not in fids and not _s772_strict(con, cid, orig):\n"
                "            return \"\", \"\"                                # the patient not confirmed: a person decides\n",
             "        if (fids and cid not in fids) or (cid not in fids and not _s772_strict(con, cid, orig)):\n"
             "            return _s776_day_only(con, cid, film, first, cache)   # S776: the film's day only; the file's ID never files\n",
             "E3 day only")
    t = edit(t, "    got = sorted({x for x in fr[1] if x in pats and _s772_strict(con, x, orig)})\n",
             "    got = sorted({x for x in fr[1] if x in pats and _s776_ok(con, x, orig, day, cache)})   # S776\n", "E4 film ID")
    t = edit(t, "        if not cid:\n            continue\n        if sid in s772_why:",
             "        if not cid and r[\"kind\"] == \"check\" and day < today:   # S776: what nothing else placed\n"
             "            cid, how = _s776_more(con, sid, r[\"orig\"], day, cache)\n"
             "        if not cid:\n            continue\n        if sid in s772_why:", "E5 more")
    t = t.rstrip("\n") + "\n" + open(os.path.join(HERE, "s776_block.py"), encoding="utf-8").read()
    os.makedirs(a[1], exist_ok=True)
    out = os.path.join(a[1], "records.py")
    open(out, "wb").write(t.encode("utf-8"))
    print("records.py %s -> %s" % (FROM_MD5[:8], md5(open(out, "rb").read())))


if __name__ == "__main__":
    main()
