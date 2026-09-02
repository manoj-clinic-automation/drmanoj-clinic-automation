#!/usr/bin/env python3
"""
patch_darpan_intent_s220.py -- S220 item 4, part 1 of 2: the intent signals reach the owner.

ONE anchored change to darpan_app.py (pin 44ed9a5e, the owner-English bytes): the
endpoint `/finance/darpan/api/intent` (checker only -- the owner alone until the
scorer has proven itself, his rule) returning the newest run of finance_intent.py
from `intent_signal`. Fail-soft: without the module or the table it answers an
empty list and says so. READ-ONLY.

Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_darpan_intent_s220.py
Offline: DARPAN_PATH=/path/to/darpan_app.py.
"""
import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get('DARPAN_PATH', '/root/finance/darpan_app.py')
MARK = 'S220 INTENT'

A_OLD = '@bp.route("/finance/darpan/api/cn-approve", methods=["POST"])\ndef api_cn_approve():\n'
A_NEW = '''@bp.route("/finance/darpan/api/intent")
def api_intent():
    """S220 INTENT: the newest run of the intent scorer (finance_intent.py), for the
    owner's card. Signals are patterns against their own baselines -- rows to look
    at, never findings. Owner-only until proven (his rule). READ-ONLY."""
    u, err = _require("checker")
    if err:
        return err
    con = _db()
    if not _is_owner(con, u):
        return jsonify(ok=True, as_of=None, signals=[], note="owner only")
    try:
        import finance_intent                                   # noqa: PLC0415
        as_of, rows = finance_intent.latest(con, _unit)
    except Exception as ex:                                     # noqa: BLE001
        return jsonify(ok=True, as_of=None, signals=[],
                       note="the intent scorer is not installed or has not run yet (%s)" % ex)
    look = sum(1 for r in rows if r.get("level") == "look" and not r.get("historical"))
    return jsonify(ok=True, as_of=as_of, signals=rows, look=look,
                   note=None if rows else "no run recorded yet -- finance_intent.py runs nightly")


@bp.route("/finance/darpan/api/cn-approve", methods=["POST"])
def api_cn_approve():
'''
PAIRS = [("A", A_OLD, A_NEW)]


def main():
    src = open(TARGET, encoding="utf-8").read()
    if MARK in src:
        print("already patched -- nothing to do")
        return 0
    for nm, old, _new in PAIRS:
        n = src.count(old)
        if n != 1:
            raise SystemExit("REFUSED: anchor %s matches %d times (need exactly 1). NOTHING was changed." % (nm, n))
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = TARGET + ".bak_S220_intent_" + stamp
    shutil.copyfile(TARGET, bak)
    out = src
    for _nm, old, new in PAIRS:
        out = out.replace(old, new, 1)
    open(TARGET, "w", encoding="utf-8").write(out)
    try:
        compile(out, TARGET, "exec")
    except SyntaxError as ex:
        shutil.copyfile(bak, TARGET)
        raise SystemExit("REFUSED: the result does not compile (%s). RESTORED from %s." % (ex, bak))
    print("patched  %s" % TARGET)
    print("backup   %s" % bak)
    return 0


if __name__ == "__main__":
    sys.exit(main())
