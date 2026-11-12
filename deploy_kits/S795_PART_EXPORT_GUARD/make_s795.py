#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s795.py FINANCE_DIR OUT_DIR -- builds purchase_app.py for S795_PART_EXPORT_GUARD from the LIVE file, which must be at FROM.
Two insertions at anchors read from the live bytes (12-Nov bundle), each required exactly once. Deterministic: same input, same output."""
import hashlib
import os
import sys

FROM = "54d27cd34b5088383887ecc19cafd4c8"
A1 = '@bp.route("/api/push", methods=["POST"])\ndef api_push():\n'
A2 = '        con.commit()\n        return jsonify(ok=True, stored=False, reason="superseded_older")\n'
FUNC = '''# ---- S795_PART_EXPORT_GUARD (12-Nov-2026, Sanjeevni session 434): a part list may not retire a fuller export ----
# 11-Nov-2026: two bill-wise reports of 1-11 Nov arrived 15 seconds apart -- 29 bills, then 4.  "Same period, the later stamp
# wins" let the 4-bill list retire the 29-bill one, and 25 of the month's bills stopped being effective (the scan pairing said
# "no bill on the server yet" for bills that were there).  A report with fewer than half the rows of a live, older report it
# would retire -- and more than two rows short of it -- is a PART list: it is kept, marked as retired by that fuller report,
# and nothing is read from it.  The next full report retires the older one as before.
S795_HALF = 0.5
S795_GAP = 2


def _s795_fuller(con, typ, pf, pt, stamp, n_rows):
    """The md5 of the live, older export of this type inside this period that the incoming one is only a PART of, or None."""
    try:
        r = con.execute(
            "SELECT md5, COALESCE(n_rows, 0) FROM purchase_export WHERE type=? AND period_from>=? AND period_to<=? "
            "AND superseded_by IS NULL AND export_stamp<? ORDER BY COALESCE(n_rows, 0) DESC, export_stamp DESC LIMIT 1",
            (typ, pf, pt, stamp)).fetchone()
    except Exception:                                          # noqa: BLE001 -- a push never fails for this
        return None
    if not r:
        return None
    big = int(r[1] or 0)
    return r[0] if (n_rows < S795_HALF * big and big - n_rows > S795_GAP) else None
# ---- end S795_PART_EXPORT_GUARD (the function) ----


'''
CALL = '''    part_of = _s795_fuller(con, typ, pf, pt, stamp, len(rows))    # S795: a part list is kept, never counted, retires nothing
    if part_of:
        con.execute("INSERT INTO purchase_export (md5,type,file,period_from,period_to,"
                    "export_stamp,received_at,n_rows,grand_amount_p,superseded_by) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (md5, typ, str(b.get("file") or "")[:200], pf, pt, stamp, now_iso(),
                     len(rows), _int_or_none(b.get("grand_amount_p")), part_of))
        con.commit()
        return jsonify(ok=True, stored=False, reason="part_export")
'''


def build(src):
    s = src.decode("utf-8")
    for name, a in (("A1 the push route", A1), ("A2 the superseded_older return", A2)):
        if s.count(a) != 1:
            raise SystemExit("make_s795: anchor %s found %d time(s), need exactly 1 -- nothing built" % (name, s.count(a)))
    if "S795_PART_EXPORT_GUARD" in s:
        raise SystemExit("make_s795: the file already carries S795 -- nothing built")
    s = s.replace(A1, FUNC + A1)
    s = s.replace(A2, A2 + CALL)
    return s.encode("utf-8")


def main():
    fin, out = sys.argv[1], sys.argv[2]
    src = open(os.path.join(fin, "purchase_app.py"), "rb").read()
    got = hashlib.md5(src).hexdigest()
    if got != FROM:
        raise SystemExit("make_s795: purchase_app.py is %s, expected %s -- nothing built" % (got[:8], FROM[:8]))
    os.makedirs(out, exist_ok=True)
    b = build(src)
    open(os.path.join(out, "purchase_app.py"), "wb").write(b)
    print("make_s795: built purchase_app.py %s (%d bytes, +%d)" % (hashlib.md5(b).hexdigest(), len(b), len(b) - len(src)))


if __name__ == "__main__":
    main()
