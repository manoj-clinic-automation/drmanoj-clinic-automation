#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_desk_anchor_s224.py -- S224: THE SPOT COUNT GETS ITS BILL ANCHOR (server half).

THE OWNER, 04-Sep-2026, urgent:

    "IN VAAPSI PAGE, THE STOCK CHECK SECTION DOES NOT HAVE ANY LAST SALE BILL
     NUMBER ENTRY BOX, PLEASE FIX IT."

and two hours earlier, the finding itself:

    "vapsi has random stk check, but no last sale bill no to base it upon?"

WHAT WAS WRONG. The S221_JAANKARI kit (03-Sep) put the D365 spot-count list on
the Vaapsi desk: one item a row, a number box, a button that says "gin liya".
The answer went into jaankari_answer as a bare number. The counting page
(/finance/stock/page/count, S207) has ALWAYS demanded the last sale bill number
before a count may start, and stock_app's /api/count refuses a count without
it -- the owner's own design (S208/S213): a count without a cut-off in the bill
stream is not a measurement, it is an impression. The spot count skipped that
rule because it was built as a QUESTION, not as a count. It is a count.

WHAT THIS DOES -- three small things in returns_desk.py, nothing else:
  1  _con()          -- jaankari_answer gains one column, anchor_bill TEXT,
                        added the same way V8_COLS are (PRAGMA, then ALTER once).
  2  /api/jaankari/answer -- kind=spot + answer=counted WITHOUT anchor_bill is
                        REFUSED, 400, in Hindi. The anchor is stored upper-case
                        in its own column, never buried in `note`.
  3  _rd_answers()   -- reads the anchor back, so the owner's later view of
                        an answer can say "counted after bill A003195".

Nothing else moves. No money, no patient, no stock_spot_check status -- the
S221 ruling (evidence only) stands; this only makes the evidence usable.

Target: /root/finance/returns_desk.py (live pin 3296eca0...)
Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_desk_anchor_s224.py
Offline:         RD_PATH=./returns_desk.py python3 -B patch_desk_anchor_s224.py
"""

import datetime as dt
import os
import py_compile
import shutil
import sys
import tempfile

TARGET = os.environ.get('RD_PATH', '/root/finance/returns_desk.py')
MARK = "S224 anchor"

# --------------------------------------------------------------- anchor A: the column
A_OLD = '''    have = {r[1] for r in con.execute("PRAGMA table_info(return_visit)")}
    for col, ddl in V8_COLS:
        if col not in have:
            con.execute("ALTER TABLE return_visit ADD COLUMN %s %s" % (col, ddl))
    return con
'''
A_NEW = '''    have = {r[1] for r in con.execute("PRAGMA table_info(return_visit)")}
    for col, ddl in V8_COLS:
        if col not in have:
            con.execute("ALTER TABLE return_visit ADD COLUMN %s %s" % (col, ddl))
    # S224 anchor -- a spot count is pinned to the last sale bill, like every
    # count on the counting page has been since S207. Its own column, so the
    # rows stay the truth (D367) and nobody has to parse `note` later.
    have = {r[1] for r in con.execute("PRAGMA table_info(jaankari_answer)")}
    if "anchor_bill" not in have:
        con.execute("ALTER TABLE jaankari_answer ADD COLUMN anchor_bill TEXT")
    return con
'''

# --------------------------------------------------------------- anchor B: read it back
B_OLD = '''        for r in con.execute(
                "SELECT ref, answer, value, answered_by, answered_at "
                "FROM jaankari_answer WHERE kind=? ORDER BY id", (kind,)):
            out[str(r["ref"])] = dict(answer=r["answer"], value=r["value"],
                                      by=r["answered_by"], at=r["answered_at"])
'''
B_NEW = '''        for r in con.execute(
                "SELECT ref, answer, value, answered_by, answered_at, anchor_bill "
                "FROM jaankari_answer WHERE kind=? ORDER BY id", (kind,)):
            out[str(r["ref"])] = dict(answer=r["answer"], value=r["value"],
                                      by=r["answered_by"], at=r["answered_at"],
                                      anchor=r["anchor_bill"])   # S224 anchor
'''

# --------------------------------------------------------------- anchor C: the refusal + the write
C_OLD = '''    note = b.get("note")
    note = str(note).strip() if note not in (None, "") else None
    con = _con()
    who = str((u or {}).get("user") or (u or {}).get("username") or "")
    con.execute(
        "INSERT INTO jaankari_answer (unit, kind, ref, business_date, answer,"
        " value, note, answered_by, answered_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (_unit, kind, ref, (str(b.get("date")).strip() or None) if b.get("date") else None,
         answer, val, note, who,
         datetime.datetime.now().replace(microsecond=0).isoformat()))
    con.commit()
    return jsonify(ok=True)
'''
C_NEW = '''    note = b.get("note")
    note = str(note).strip() if note not in (None, "") else None
    # S224 anchor -- THE OWNER'S RULE, the same one stock_app.py enforces at
    # /api/count: a count that is not pinned to the last sale bill cannot be
    # reconciled later, so it is not accepted at all. Refused before anything
    # is written; the page shows this message word for word.
    anchor = str(b.get("anchor_bill") or "").strip().upper() or None
    if kind == "spot" and answer == "counted" and not anchor:
        return jsonify(ok=False, error="anchor_required",
                       message="\\u0906\\u0916\\u093c\\u093f\\u0930\\u0940 \\u0938\\u0947\\u0932 "
                               "\\u092c\\u093f\\u0932 \\u0928\\u0902\\u092c\\u0930 \\u091c\\u093c\\u0930\\u0942\\u0930\\u0940 "
                               "\\u0939\\u0948 \\u2014 \\u092c\\u093f\\u0928\\u093e \\u092c\\u093f\\u0932 \\u0915\\u0940 "
                               "\\u0917\\u093f\\u0928\\u0924\\u0940 \\u092c\\u093e\\u0926 \\u092e\\u0947\\u0902 "
                               "\\u092e\\u093f\\u0932\\u093e\\u0908 \\u0928\\u0939\\u0940\\u0902 \\u091c\\u093e "
                               "\\u0938\\u0915\\u0924\\u0940 \\u0964"), 400
    con = _con()
    who = str((u or {}).get("user") or (u or {}).get("username") or "")
    con.execute(
        "INSERT INTO jaankari_answer (unit, kind, ref, business_date, answer,"
        " value, note, answered_by, answered_at, anchor_bill)"
        " VALUES (?,?,?,?,?,?,?,?,?,?)",
        (_unit, kind, ref, (str(b.get("date")).strip() or None) if b.get("date") else None,
         answer, val, note, who,
         datetime.datetime.now().replace(microsecond=0).isoformat(), anchor))
    con.commit()
    return jsonify(ok=True)
'''


def main():
    with open(TARGET, 'r', encoding='utf-8', newline='') as fh:
        src = fh.read()
    if MARK in src:
        print("already patched: %s" % TARGET)
        return 0
    for name, old in (("A", A_OLD), ("B", B_OLD), ("C", C_OLD)):
        n = src.count(old)
        if n != 1:
            print("REFUSED: anchor %s found %d times (need exactly 1) -- file left untouched" % (name, n))
            return 2
    stamp = dt.datetime.now().strftime('%Y%m%d-%H%M%S')
    bak = TARGET + '.bak_S224_anchor_' + stamp
    shutil.copy2(TARGET, bak)
    out = src.replace(A_OLD, A_NEW).replace(B_OLD, B_NEW).replace(C_OLD, C_NEW)
    with open(TARGET, 'w', encoding='utf-8', newline='') as fh:
        fh.write(out)
    cfile = os.path.join(tempfile.gettempdir(), 'returns_desk_s224_check.pyc')
    try:
        py_compile.compile(TARGET, doraise=True, cfile=cfile)
    except py_compile.PyCompileError as e:
        shutil.copy2(bak, TARGET)
        print("REFUSED: the result does not compile; restored from %s\n%s" % (bak, e))
        return 3
    finally:
        try:
            os.remove(cfile)
        except OSError:
            pass
    print("patched  %s" % TARGET)
    print("backup   %s" % bak)
    print("next     the page patcher, then the selftest")
    return 0


if __name__ == '__main__':
    sys.exit(main())
