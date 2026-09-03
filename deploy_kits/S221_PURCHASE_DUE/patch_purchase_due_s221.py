#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_purchase_due_s221.py -- S221: HIS ARRIVAL BECOMES THE ASK.

THE OWNER, 03-Sep-2026, on Amir:

    "He comes biweekly mostly. So when he comes, he punches, and the system
     knows he has come. And so the purchase can be exported accordingly, and
     the working can progress seamlessly."

The first half of that was already true the moment he was enrolled: he punches
as 101 and attendance sees him. The second half was not connected to anything.
The pipeline's own words are "purchases arrive when Amir visits" -- which in
practice meant *when Amir remembers, or when the owner asks*. Nothing joined the
punch to the books.

WHAT THIS DOES. One read-only rule, on data both sides already hold:

    purchases are known up to PUR_TO          <- push_expected reports it
    Amir was last here on LAST_VISIT          <- punches.csv, the attendance feed
    LAST_VISIT > PUR_TO  =>  he came and the export did not

`pur_to` needs no new plumbing: push_expected already stamps it into the source
string it sends ("push_expected base=... pur_to=..."), and since S221_TWO_PRICES
every pushed figure is kept in `stock_feed` with its source. The date was
already arriving; nothing was reading it.

WHY punches.csv AND NOT THE REGISTER'S DATABASE. Attendance owns that file --
one writer per store -- and staff_register reads it exactly this way, read-only,
failing soft when it is missing. Opening another application's database would
couple two systems that have no reason to be coupled. A CSV read that returns
None on any problem cannot break anything.

FAIL-SOFT, AND IT MATTERS HERE. If punches.csv is unreadable the purchase
staleness is still reported -- the visit is an ENRICHMENT of the answer, never a
dependency of it. And if nobody is configured as the purchase person, no visit
line appears at all: the code will not guess who fetches the purchases.

WHO IS THE PURCHASE PERSON is data, not code: `setting` key
`purchase.staff_id`, defaulting to 101, which is the Emp Code issued to Amir
Sohail on 03-Sep-2026. Change the row, not this file.

NOTHING HERE WRITES. No money, no status, no table. It is one more thing the
drift page can say.

Target: /root/finance/stock_app.py (pin c627e440... == the S221_TWO_PRICES result,
reproduced offline and md5-proven before building)
Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_purchase_due_s221.py
Offline:         SA_PATH=./stock_app.py python3 -B patch_purchase_due_s221.py
"""

import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get('SA_PATH', '/root/finance/stock_app.py')
MARK = "S221 PURCHASE DUE"


A_OLD = '''def _feed_kind(source):
'''

A_NEW = '''# ---- S221 PURCHASE DUE: the punch that asks for the export ------------------
PUNCH_CSV = os.environ.get("SR_PUNCH_CSV", "/root/punches.csv")
_PUR_TO_RE = _re221.compile(r"pur_to\\s*=\\s*(\\d{4}-\\d{2}-\\d{2}|\\d{2}-\\d{2}-\\d{4})")


def _iso(d):
    """dd-mm-yyyy or yyyy-mm-dd -> yyyy-mm-dd. None when it is neither."""
    s = str(d or "").strip()
    if _re221.fullmatch(r"\\d{4}-\\d{2}-\\d{2}", s):
        return s
    m = _re221.fullmatch(r"(\\d{2})-(\\d{2})-(\\d{4})", s)
    return "%s-%s-%s" % (m.group(3), m.group(2), m.group(1)) if m else None


def _purchases_known_to(con):
    """The last date purchases are known up to, read out of the feed log.

    push_expected stamps it into the source string it sends; since
    S221_TWO_PRICES every source is kept. Nothing new is sent for this.
    """
    best = None
    try:
        for r in con.execute("SELECT DISTINCT source FROM stock_feed"):
            m = _PUR_TO_RE.search(str(r[0] or ""))
            if m:
                d = _iso(m.group(1))
                if d and (best is None or d > best):
                    best = d
    except Exception:
        return None
    return best


def _last_punch(staff_id):
    """The last date this person punched. None on ANY problem -- a missing or
    unreadable feed must never become 'he did not come'. Read exactly the way
    staff_register reads it; attendance owns the file and we only look."""
    if not staff_id:
        return None
    try:
        import csv as _csv                                    # noqa: PLC0415
        if not os.path.exists(PUNCH_CSV):
            return None
        want = str(staff_id).strip()
        last = None
        with open(PUNCH_CSV, newline="", encoding="utf-8") as fh:
            for row in _csv.DictReader(fh):
                if str(row.get("user_id") or "").strip() != want:
                    continue
                d = str(row.get("datetime") or "")[:10]
                if _re221.fullmatch(r"\\d{4}-\\d{2}-\\d{2}", d) and (last is None or d > last):
                    last = d
    except Exception:
        return None
    return last


def purchase_due(con):
    """Is a purchase export owed, and why? READ-ONLY, and every branch says
    what it knows rather than implying more."""
    try:
        r = con.execute("SELECT value FROM setting WHERE key='purchase.staff_id'").fetchone()
        sid = (r[0] if r else None) or "101"
    except Exception:
        sid = "101"
    pur_to = _purchases_known_to(con)
    visit = _last_punch(sid)
    today = now_iso()[:10]

    def _days(a, b):
        try:
            return (dt.date.fromisoformat(b) - dt.date.fromisoformat(a)).days
        except Exception:
            return None

    out = dict(staff_id=str(sid), purchases_known_to=pur_to, last_visit=visit,
               punch_feed=os.path.exists(PUNCH_CSV), due=False, state="unknown",
               line="")
    if not pur_to:
        out["state"] = "no_purchase_date"
        out["line"] = ("No purchase date has reached the server yet. It arrives "
                       "stamped on the computed stock push, so this fills in "
                       "once that job has run.")
        return out
    out["stale_days"] = _days(pur_to, today)
    if visit and visit > pur_to:
        out["due"] = True
        out["state"] = "came_and_did_not_export"
        out["line"] = ("Purchases are known only to %s, and he was here on %s. "
                       "The export from that visit has not arrived." % (pur_to, visit))
    elif visit:
        out["state"] = "current_as_of_his_last_visit"
        out["line"] = ("Purchases are current as far as his last visit (%s). "
                       "Known to %s." % (visit, pur_to))
    else:
        out["state"] = "no_visit_seen"
        out["line"] = ("Purchases are known to %s. No punch has been seen for "
                       "this person%s." % (pur_to,
                                           "" if out["punch_feed"]
                                           else " -- and the punch feed is not readable "
                                                "from here, so this is not evidence "
                                                "that he did not come"))
    return out
# ---- end S221 PURCHASE DUE --------------------------------------------------


def _feed_kind(source):
'''


B_OLD = '''    return jsonify(ok=True, items=out, feeds=feeds,
                   comparable=len(out),
'''

B_NEW = '''    return jsonify(ok=True, items=out, feeds=feeds,
                   purchase=purchase_due(con),
                   comparable=len(out),
'''


PAIRS = [("A", A_OLD, A_NEW), ("B", B_OLD, B_NEW)]


def main():
    src = open(TARGET, encoding="utf-8").read()
    if MARK in src:
        print("already patched -- nothing to do")
        return 0
    for nm, old, _new in PAIRS:
        n = src.count(old)
        if n != 1:
            raise SystemExit("REFUSED: anchor %s matches %d times (need exactly 1). "
                             "NOTHING was changed." % (nm, n))
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = TARGET + ".bak_S221_purdue_" + stamp
    shutil.copyfile(TARGET, bak)
    out = src
    for _nm, old, new in PAIRS:
        out = out.replace(old, new, 1)
    open(TARGET, "w", encoding="utf-8").write(out)
    try:
        compile(out, TARGET, "exec")
    except SyntaxError as ex:
        shutil.copyfile(bak, TARGET)
        raise SystemExit("REFUSED: the result does not compile (%s). "
                         "RESTORED from %s." % (ex, bak))
    print("patched  %s" % TARGET)
    print("backup   %s" % bak)
    print("next     copy stock_drift.html, then the walk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
