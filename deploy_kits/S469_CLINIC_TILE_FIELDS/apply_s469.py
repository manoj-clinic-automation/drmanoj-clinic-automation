#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_s469.py -- S469_CLINIC_TILE_FIELDS (session 292, 03-Oct-2026): two exact edits of finance_app.py.

Built from the real bytes: /root/finance/finance_app.py at 8f69f192 (72d25382, live since 03-Oct, with S468 applied).
The clinic tile and the clinic exceptions list were left as they were by S463 (F-707) because reception's entry page
reads both. They hand ANY signed-in clinic identity the unit's whole position -- cash in hand and who holds it, the
month to date, drawings, the bank-trip clock, every open shout -- while that page shows one deposit banner and the
missing-day list. The medical side closed exactly this at F-127. Here, FIELDS ONLY -- nobody who gets in today is
refused:
  1  /finance/clinic/api/tile        a non-checker gets ok, unit_name, deposit_due, and -- only when the limit is
                                     crossed -- the three figures of the banner. The checker's answer is unchanged.
  2  /finance/clinic/api/exceptions  a non-checker gets the missing-day rows only. The checker's answer is unchanged.
Every anchor must be found exactly once.   usage: apply_s469.py <finance_app.py>
"""
import hashlib
import sys

FROM = "8f69f192020205b302ac413a039f7c31"

EDITS = [
    ('''    return jsonify(ok=True, unit_name=CLINIC_NAME,
                   drawings_month_to_date=rupees(drawings_mtd),
''',
     '''    # S469 (F-707's last part, the clinic twin of F-127): reception's entry page reads this for ONE deposit banner.
    # A non-checker is given that banner's figures and nothing else; the checker's answer below is unchanged.
    _u469 = current_user()
    if "checker" not in roles_for(con, CLINIC_UNIT, _u469["user"], _u469["role"]):
        _due469 = bool(thr and cash_p > thr)
        _out469 = dict(ok=True, unit_name=CLINIC_NAME, deposit_due=_due469)
        if _due469:
            _out469.update(cash_in_hand=rupees(cash_p), deposit_threshold=rupees(thr),
                           deposit_excess=rupees(max(cash_p - thr, 0)))
        return jsonify(**_out469)
    return jsonify(ok=True, unit_name=CLINIC_NAME,
                   drawings_month_to_date=rupees(drawings_mtd),
'''),
    ('''def clinic_api_exceptions():
    return jsonify(ok=True, exceptions=open_exceptions(db(), CLINIC_UNIT))
''',
     '''def clinic_api_exceptions():
    # S469: reception's entry page has only ever used the missing-day rows, so that is all a non-checker is given
    # (the medical side: F-127). The checker's answer is what it always was.
    con = db()
    excs = open_exceptions(con, CLINIC_UNIT)
    _u469 = current_user()
    if "checker" not in roles_for(con, CLINIC_UNIT, _u469["user"], _u469["role"]):
        excs = [e for e in excs if e.get("kind") == "missing_day"]
    return jsonify(ok=True, exceptions=excs)
'''),
]


def apply(src):
    for n, (old, new) in enumerate(EDITS, 1):
        got = src.count(old)
        if got != 1:
            raise SystemExit("!! anchor %d was found %d time(s), expected 1 - nothing written" % (n, got))
        src = src.replace(old, new)
    return src


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply_s469.py <path to finance_app.py>")
    path = sys.argv[1]
    raw = open(path, "rb").read()
    have = hashlib.md5(raw).hexdigest()
    if have != FROM:
        raise SystemExit("!! %s is %s, not %s - nothing written" % (path, have, FROM))
    out = apply(raw.decode("utf-8")).encode("utf-8")
    compile(out, path, "exec")
    with open(path, "wb") as fh:
        fh.write(out)
    print("finance_app.py %s -> %s (%d edits; %+d bytes)" % (have[:8], hashlib.md5(out).hexdigest()[:8], len(EDITS), len(out) - len(raw)))


if __name__ == "__main__":
    main()
