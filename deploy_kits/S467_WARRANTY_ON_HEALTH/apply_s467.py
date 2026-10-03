#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_s467.py -- S467_WARRANTY_ON_HEALTH (D664, session 292, 03-Oct-2026): two exact insertions in finance_app.py.

Built from the real file (/root/finance/finance_app.py at 49f52391, as S463 left it).
  1  a small reader, _s467_warranties(today), above _health_state: the Dr MK expense warranties that are INSIDE THEIR
     OWN reminder window, read READ-ONLY from the asset app's database (the path purchase_app already takes).
  2  a block '6b' right after the Renewals row is made: if such a warranty exists it is said on that row, and the row
     is raised to 'info' (to 'warn' inside 7 days) if it was quieter. Section 6 itself is not edited (wrap, don't edit).
A warranty that has ended is never said and can never turn the row red. No file, no table, any error: the row is
exactly what section 6 made it. Nothing is written anywhere. Every anchor must be found exactly once.
   usage: apply_s467.py <finance_app.py>
"""
import hashlib
import sys

FROM = "49f52391f44643c10b052609cffc5bbe"

A1 = '''def _health_state(con):\n'''
N1 = '''# --- S467_WARRANTY_ON_HEALTH begin -- D664: a Dr MK expense's warranty rides the Renewals row ---
def _s467_warranties(today):
    """[(days_left, what, dateISO)], nearest first: the Dr MK expense warranties INSIDE THEIR OWN reminder window.
    The asset app keeps them (assets.db, table d664_warranty -- S466); this reads that file READ-ONLY and writes
    nothing. An ended warranty, one with 'No reminder', and one whose paper left the lane or was rejected are not
    returned. The path is read at call time so the walk can point it at a made-up file."""
    path = os.environ.get("ASSETS_DB", "/root/assetapp/assets.db")
    if not os.path.isfile(path):
        return []
    out = []
    ac = sqlite3.connect("file:%s?mode=ro" % path, uri=True, timeout=2)
    try:
        for what, till, rd in ac.execute(
                "SELECT w.what, w.till, w.remind_days FROM d664_warranty w JOIN bills b ON b.id=w.bill_id "
                "WHERE COALESCE(b.lane,'clinic')='owner_expense' AND b.status<>'rejected'"):
            try:
                dd = (dt.date.fromisoformat(str(till)[:10]) - today).days
                rd = int(rd or 0)
            except (ValueError, TypeError):
                continue
            if rd and 0 <= dd <= rd:
                out.append((dd, str(what or "")[:60], str(till)[:10]))
    finally:
        ac.close()
    out.sort()
    return out
# --- S467_WARRANTY_ON_HEALTH end ---


def _health_state(con):
'''

A2 = '''        add("renewals", "Renewals", "info", "could not be read (%s)" % ex)

    worst = "ok"
'''
N2 = '''        add("renewals", "Renewals", "info", "could not be read (%s)" % ex)

    # ---- 6b. S467 (D664): a warranty inside its own reminder window is said on the Renewals row. Section 6 above
    # is not edited; this only adds to the row it made. A quiet row is raised to info (warn inside 7 days); a row
    # already warn or bad keeps its state and its own words first. Any error: the row stays exactly as it was.
    try:
        _w467 = _s467_warranties(today)
        if _w467:
            _dd7, _what7, _iso7 = _w467[0]
            _txt7 = "warranty: %s ends %s (%s)%s" % (
                _what7, "today" if _dd7 == 0 else "in %d day%s" % (_dd7, "" if _dd7 == 1 else "s"), _iso7,
                " · %d more warranty reminder%s" % (len(_w467) - 1, "" if len(_w467) == 2 else "s")
                if len(_w467) > 1 else "")
            for _c7 in checks:
                if _c7["key"] == "renewals":
                    if _c7["state"] in ("ok", "info"):
                        _c7["detail"] = "%s · %s" % (_txt7, _c7["detail"])
                        _c7["state"] = "warn" if _dd7 <= 7 else "info"
                    else:
                        _c7["detail"] = "%s · %s" % (_c7["detail"], _txt7)
                    break
    except Exception:                                             # noqa: BLE001
        pass

    worst = "ok"
'''
EDITS = [(A1, N1), (A2, N2)]


def apply(src):
    for n, (old, new) in enumerate(EDITS, 1):
        got = src.count(old)
        if got != 1:
            raise SystemExit("!! anchor %d was found %d time(s), expected 1 - nothing written" % (n, got))
        src = src.replace(old, new)
    return src


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply_s467.py <path to finance_app.py>")
    path = sys.argv[1]
    raw = open(path, "rb").read()
    have = hashlib.md5(raw).hexdigest()
    if have != FROM:
        raise SystemExit("!! %s is %s, not %s - nothing written" % (path, have, FROM))
    out = apply(raw.decode("utf-8")).encode("utf-8")
    compile(out, path, "exec")
    with open(path, "wb") as fh:
        fh.write(out)
    print("finance_app.py %s -> %s (%d insertions; %+d bytes)" % (have[:8], hashlib.md5(out).hexdigest()[:8], len(EDITS), len(out) - len(raw)))


if __name__ == "__main__":
    main()
