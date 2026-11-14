#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s824.py -- S824_REVISED_BILL_SETASIDE (F-1378): makes the new /root/finance/scan_register.py from the LIVE bytes, by exact,
counted replacements; refuses any other starting file.
    python3 -B make_s824.py <live scan_register.py> <out file>
The change: _s740_revised (S740's revised-bill road) also reads the pharmacy scans the scan app SET ASIDE as a second scan of another
bill (status 'rejected', dup_of set, not a page of a bill) -- accepted only where it already accepts a captured scan: the same dealer
and bill number, its amount the paper less the return within _s740_tol, and more than Rs 1 off the paper (a true double reads the
paper's own amount and settles nothing). A captured scan is always tried first. Nothing else in the file changes."""
import hashlib
import sys

FROM = "9262c5dc05f0aa3cd52595b0894cd8ca"

R = [
# 1 -- the read of the set-aside scans, beside asset_scans
('''def _scan_day(r):
    """The scan's day in IST: submitted_at (IST) else created_at (UTC) + 5:30."""''',
 '''def s824_set_aside(con=None):
    """S824 (F-1378): {id: scan} -- the pharmacy scans the scan app SET ASIDE as a second scan of another bill (status 'rejected', dup_of
    set, not a page of a bill; assets.db, READ ONLY), in asset_scans' shape. Read ONLY by _s740_revised: a dealer's revised bill set aside
    by a "same paper" answer is still the dealer's revised bill. {} when unreachable or the columns are not there."""
    pa = _pa()
    acon = pa._assets_con()
    if acon is None:
        return {}
    try:
        cols = {r[1] for r in acon.execute("PRAGMA table_info(bills)")}
        if not {"dup_of", "status", "kind"} <= cols:
            return {}
        sel = [c for c in ("id", "stamp_no", "vendor", "bill_no", "bill_date", "total_amount", "submitted_at", "created_at", "ocr_status", "dup_of",
                           "bill_month", "lane", "status", "kind") if c in cols]
        rows = [dict(r) for r in acon.execute("SELECT %s FROM bills WHERE kind='Pharmacy' AND status='rejected' AND dup_of IS NOT NULL%s ORDER BY id"
                                              % (", ".join(sel), " AND page_of IS NULL" if "page_of" in cols else ""))]
    except sqlite3.Error:
        return {}
    finally:
        acon.close()
    out = {}
    for r in rows:
        r["amount_p"] = _amount_p(r.get("total_amount"))
        r["day"] = _scan_day(r)
        out[int(r["id"])] = r
    return out


def _scan_day(r):
    """The scan's day in IST: submitted_at (IST) else created_at (UTC) + 5:30."""'''),
# 2 -- _s740_revised: a set-aside scan is read when asked for
('''def _s740_revised(cx, scans, r, b):
    """A scan of the same supplier and bill number reading the paper less the return -- the dealer's revised bill. (sid, paise, stamp) | None."""
    P, A = int(r["paper_p"] or 0), int(r["amount_p"] or 0)
    net = P - A
    for sid, s in scans.items():
        if sid == r.get("scan") or str(s.get("lane") or "pharmacy") != "pharmacy" or s.get("dup_of"):
            continue''',
 '''def _s740_revised(cx, scans, r, b, set_aside=False):
    """A scan of the same supplier and bill number reading the paper less the return -- the dealer's revised bill. (sid, paise, stamp) | None.
    S824 (F-1378): set_aside=True reads the scans of s824_set_aside (each has dup_of) by the same rules, and returns (sid, paise, stamp, True)."""
    P, A = int(r["paper_p"] or 0), int(r["amount_p"] or 0)
    net = P - A
    for sid, s in scans.items():
        if sid == r.get("scan") or str(s.get("lane") or "pharmacy") != "pharmacy" or (s.get("dup_of") and not set_aside):
            continue'''),
('''        if supplier(cx, s.get("vendor"), b["supplier"], cx.chosen.get(sid)) != "agree":
            continue
        return (sid, int(sa), s.get("stamp_no") or "#%d" % sid)
    return None''',
 '''        if supplier(cx, s.get("vendor"), b["supplier"], cx.chosen.get(sid)) != "agree":
            continue
        if set_aside:
            return (sid, int(sa), s.get("stamp_no") or "#%d" % sid, True)
        return (sid, int(sa), s.get("stamp_no") or "#%d" % sid)
    return None'''),
# 3 -- _s740_build: the set-aside scans only when no captured scan settles it (read once, lazily)
('''    minus = [b for b in bills if int(b["amount_p"] or 0) < 0]
    rets = []''',
 '''    minus = [b for b in bills if int(b["amount_p"] or 0) < 0]
    aside = None                                              # S824 (F-1378): the set-aside scans, read once and only when needed
    rets = []'''),
('''        r["_rev"] = _s740_revised(cx, scans, r, b)
        rets.append(r)''',
 '''        r["_rev"] = _s740_revised(cx, scans, r, b)
        if r["_rev"] is None and assets_ok:                   # S824 (F-1378): a revised bill set aside by a "same paper" answer
            if aside is None:
                aside = s824_set_aside(con)
            rv = _s740_revised(cx, aside, r, b, set_aside=True)
            if rv is not None and abs(int(b["amount_p"] or 0) - rv[1]) <= 100:   # only when Marg already holds the revised figure: a set-aside
                r["_rev"] = rv                                # scan never outranks a credit note, never sends Amir to a paper he cannot open
        rets.append(r)'''),
# 4 -- _s740_stage: a set-aside scan is named, but not offered as a link (the scan door serves captured scans only)
('''            r["revised"] = dict(scan=rev[0], amount_p=rev[1], stamp=rev[2])''',
 '''            if len(rev) < 4:                                  # S824: a set-aside scan is named in the words, never linked (the door serves captured scans)
                r["revised"] = dict(scan=rev[0], amount_p=rev[1], stamp=rev[2])'''),
]


def main():
    src, out = sys.argv[1], sys.argv[2]
    b = open(src, "rb").read()
    h = hashlib.md5(b).hexdigest()
    if h != FROM:
        print("make_s824: the live file is %s, not %s -- STOP" % (h[:8], FROM[:8]))
        return 2
    t = b.decode("utf-8")
    for i, (old, new) in enumerate(R, 1):
        n = t.count(old)
        if n != 1:
            print("make_s824: replacement %d found %d times -- STOP" % (i, n))
            return 2
        t = t.replace(old, new, 1)
    nb = t.encode("utf-8")
    open(out, "wb").write(nb)
    print("make_s824: %s -> %s" % (FROM[:8], hashlib.md5(nb).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
