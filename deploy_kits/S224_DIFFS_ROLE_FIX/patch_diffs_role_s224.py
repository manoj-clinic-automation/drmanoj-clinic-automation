#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_diffs_role_s224.py -- S224: the diffs page learns WHO is looking.

THE TRAP (S222 ruling: a control that refuses is a trap). stock_diffs.html
showed the eight cause buttons to every login that could open it, while
/api/diff/<id>/cause is checker-only. Darpan, Amir and the desk girls tapped a
cause and got "not_permitted". S221's own finding page does it right -- the
server tells the page `you.may_decide` and the page draws accordingly.

THREE additive changes to stock_app.py, nothing removed, no gate relaxed:

  1  _has_role(u, role): the live login carries the UNIT roles in `roles`
     (finance_app.require: dict(u, roles=sorted(have))) and the broker's
     clinic-wide role ('doctor', 'staff') in `role`. Look in both.
     _may_decide now uses it -- until now it read `role` alone, and the
     owner's SSO role is 'doctor', not 'checker'.
  2  /api/open answers `you` = {user, may_cause, may_answer} and, per line,
     the latest staff `answer` (reason, note, who), exactly as /api/finding
     already does. The page draws the cause buttons only for may_cause
     (checker), the staff reason buttons only for may_answer (maker), and
     text for everyone else. The server still refuses on its own.
  3  page_diffs docstring/comment: the button is no longer shown to him.

Target: /root/finance/stock_app.py at pin 4e929d0b (S213 + STOCK_FINDING +
TWO_PRICES + PURCHASE_DUE + AMIR_ACCESS, reproduced offline and md5-proven).
Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_diffs_role_s224.py
Offline:         SA_PATH=./stock_app.py python3 -B patch_diffs_role_s224.py
"""

import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get('SA_PATH', '/root/finance/stock_app.py')
MARK = "S224 DIFFS ROLE"

A_OLD = '''    # S221 COUNTER VIEWER -- he may SEE the difference his count produced.
    # Naming its cause is still checker-only; that button will refuse him.
    u, err = _require("checker", "maker", "viewer")
'''
A_NEW = '''    # S221 COUNTER VIEWER -- he may SEE the difference his count produced.
    # Naming its cause is still checker-only. S224 DIFFS ROLE: the page no
    # longer shows him that button -- /api/open tells it who is looking.
    u, err = _require("checker", "maker", "viewer")
'''

B_OLD = '''    out = [dict(r) if hasattr(r, "keys") else dict(zip(
        ("id", "item", "found_on", "marg_qty", "counted_qty", "diff", "value_p",
         "cause", "cause_note", "counted_by"), r)) for r in rows]
    return jsonify(ok=True, open=len(out), items=out, causes=list(CAUSES),
                   labels=CAUSE_LABEL)
'''
B_NEW = '''    out = [dict(r) if hasattr(r, "keys") else dict(zip(
        ("id", "item", "found_on", "marg_qty", "counted_qty", "diff", "value_p",
         "cause", "cause_note", "counted_by"), r)) for r in rows]
    # S224 DIFFS ROLE -- the page draws only the controls this login may use.
    # `you` is the same shape /api/finding sends; the latest staff answer per
    # line rides along so a maker sees what he recorded. ADDITIVE: every field
    # the S213 page read is still here, unchanged.
    _f_ensure(con)
    _ans = _f_latest(con, "stock_diff_answer", [x["id"] for x in out],
                     ("reason", "note", "answered_by", "answered_at"))
    for x in out:
        _a = _ans.get(x["id"])
        x["answer"] = (dict(_a, label=STAFF_REASONS.get(_a["reason"], _a["reason"]))
                       if _a else None)
        x["cause_label"] = CAUSE_LABEL.get(x["cause"], x["cause"])
    _mc = _may_decide(u)
    return jsonify(ok=True, open=len(out), items=out, causes=list(CAUSES),
                   labels=CAUSE_LABEL, reasons=STAFF_REASONS,
                   you=dict(user=(u or {}).get("user") or "", may_cause=_mc,
                            may_answer=(not _mc) and _has_role(u, "maker")))
'''

C_OLD = '''def _may_decide(u):
    """Only the checker rules on a line. The server decides this, not the page."""
    return (u or {}).get("role") in ("checker",) or bool((u or {}).get("is_checker"))
'''
C_NEW = '''def _has_role(u, role):
    """S224 DIFFS ROLE. The live login carries the UNIT roles in `roles`
    (finance_app.require: dict(u, roles=sorted(have))) and the broker's
    clinic-wide role ('doctor', 'staff') in `role`. Look in both, so the owner
    is the checker here exactly when the unit_role table says so."""
    u = u or {}
    return role in (u.get("roles") or ()) or u.get("role") == role


def _may_decide(u):
    """Only the checker rules on a line. The server decides this, not the page."""
    return _has_role(u, "checker") or bool((u or {}).get("is_checker"))
'''


def main():
    with open(TARGET, "r", encoding="utf-8", newline="") as fh:
        src = fh.read()
    if MARK in src:
        print("already patched: %s" % TARGET)
        return 0
    for name, old in (("A", A_OLD), ("B", B_OLD), ("C", C_OLD)):
        if src.count(old) != 1:
            print("REFUSING: anchor %s found %d times, expected 1" % (name, src.count(old)))
            return 1
    bak = "%s.bak_S224_diffsrole_%s" % (TARGET, dt.datetime.now().strftime("%Y%m%d-%H%M%S"))
    shutil.copyfile(TARGET, bak)
    src = src.replace(A_OLD, A_NEW).replace(B_OLD, B_NEW).replace(C_OLD, C_NEW)
    with open(TARGET, "w", encoding="utf-8", newline="") as fh:
        fh.write(src)
    compile(src, TARGET, "exec")          # syntax-proven, no .pyc written
    print("patched %s (backup %s)" % (TARGET, os.path.basename(bak)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
