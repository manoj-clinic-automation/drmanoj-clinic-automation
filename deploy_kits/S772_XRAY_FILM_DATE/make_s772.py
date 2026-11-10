#!/usr/bin/env python3
"""make_s772.py -- S772_XRAY_FILM_DATE (the parent, S422, 10-Nov-2026): the owner 10:56-11:13 IST, "do all thats possible".
A parked X-ray picture is planned on the date printed on its film (xray_filmdate, read by xray_filmdate.py), else on its ID's
one X-ray day with no photo; the corrected copies' older parked copies and copies filed to another patient under a mistyped
ID go to the mailbox's duplicates folder (never deleted). Five counted edits on the LIVE bytes (/root/finance/records.py
d86f2ada = the 10-Nov bundle = kit S757's TO), each anchor found exactly once, plus the S772 block appended (s772_block.py).
usage: make_s772.py <live records.py> <out_dir>"""
import hashlib
import os
import sys

FROM_MD5 = "d86f2adae16afa32afc4443042e5aacc"
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
             "S772 (S422, 10-Nov-2026, the owner's 'do all thats possible'): once xray_filmdate.py has read a parked X-ray's film, the\n"
             "picture is planned on the date (and ID) printed on it, else on its ID's one X-ray day with no photo -- only for a patient\n"
             "confirmed by the film's ID or a strict name; after the corrected copy is filed, its older parked copies and a copy filed\n"
             "to another patient under a mistyped ID go to the duplicates folder -- never deleted.\n"
             "Flask, requests and the standard library. No patient name, no number, no secret in this file (F-185).\n", "E1 doc")
    t = edit(t, "    feed = []\n    for f in files:\n        f2 = dict(f)\n",
             "    feed = []\n    c772, s772_why, s772_day = {}, {}, {}                # S772: the planned day and its reason, per picture\n"
             "    for f in files:\n        f2 = dict(f)\n", "E2 s772 state")
    t = edit(t, '        u = _s752_utc((rows.get(f.get("id")) or {}).get("file_time"))\n'
                '        if u:                                              # the day first seen, not a time Drive may have moved\n',
             '        u = _s752_utc((rows.get(f.get("id")) or {}).get("file_time"))\n'
             '        d772, w772 = _s772_day(con, f, rows.get(f.get("id")) or {}, c772)   # S772: the film\'s date / the ID\'s one open day\n'
             '        if d772:\n'
             '            u = _s752_utc(d772 + " 12:00:00")\n'
             '            s772_why[f.get("id")] = w772\n'
             '            s772_day[f.get("id")] = d772\n'
             '        if u:                                              # the day first seen, not a time Drive may have moved\n',
             "E3 the S772 day")
    t = edit(t, "    cache, placed = {}, {}\n    today = _today()\n    plan = [",
             "    feed, s772_held = _s772_hold(con, feed, files, rows, s772_day, c772)   # S772: older copies held for the clean-up\n"
             "    cache, placed = {}, {}\n    today = _today()\n    plan = [", "E3b hold")
    t = edit(t, '        elif r["kind"] == "check" and xray_id(r["orig"])[1] == "none" and day < today:\n',
             '        elif r["kind"] == "check" and day < today and _s772_film_id(con, sid, r["orig"], day, cache):   # S772\n'
             '            cid = _s772_film_id(con, sid, r["orig"], day, cache)\n'
             '            how = "the clinic ID printed on the film, %s, is one of %s\'s X-ray patients" % (cid, _dmy(day))\n'
             '        elif r["kind"] == "check" and xray_id(r["orig"])[1] == "none" and day < today:\n', "E4a film ID")
    t = edit(t, "        if not cid:\n            continue\n        filed = _s752_day(con, day, cache)[1].get(cid, 0)\n",
             "        if not cid:\n            continue\n"
             "        if sid in s772_why:                              # S772: say why this day\n"
             "            how = s772_why[sid] + \" -- \" + how\n"
             "        filed = _s752_day(con, day, cache)[1].get(cid, 0)\n", "E4 why")
    t = edit(t, "    con.commit()\n    return out\n\n\ndef _s752_retry_safe(",
             "    out.extend(_s772_tidy(con, files, rows, stamp, c772))   # S772: the clean-up\n"
             "    con.commit()\n    return out\n\n\ndef _s752_retry_safe(", "E6 tidy")
    t = t.rstrip("\n") + "\n" + open(os.path.join(HERE, "s772_block.py"), encoding="utf-8").read()
    os.makedirs(a[1], exist_ok=True)
    out = os.path.join(a[1], "records.py")
    open(out, "wb").write(t.encode("utf-8"))
    print("records.py %s -> %s" % (FROM_MD5[:8], md5(open(out, "rb").read())))


if __name__ == "__main__":
    main()
