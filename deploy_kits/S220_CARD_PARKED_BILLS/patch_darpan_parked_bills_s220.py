#!/usr/bin/env python3
"""
patch_darpan_parked_bills_s220.py -- S220 F-282b: the parked bills EXPAND, like the CN bills.

The owner, 02-Sep 22:55: "bina pehchaan ke bill (7) -- are they supposed to expand to the
bill details?" Yes. The line had the number but not the bills; for Darpan the bills ARE the
point -- which seven need a name. TWO anchored changes to darpan_app.py (pin ee0e8a8f) and
ONE to darpan_card.html (part 2): the card API lists the parked bills of the day (bill number,
rupees, the name and clinic ID as typed at the counter, the phone's last four -- the parked
row keeps only those four digits, so that is what can be shown),
and the card shows them under a tap, exactly like "CN bills".

Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_darpan_parked_bills_s220.py
Offline: DARPAN_PATH=/path/to/darpan_app.py.
"""
import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get('DARPAN_PATH', '/root/finance/darpan_app.py')
MARK = 'S220 F-282b'

A_OLD = "    review_n = int(_va[\"in_review_count\"] or 0) if _va is not None else 0\n    day_sale_p = sold_p - ret_p + review_p\n"
A_NEW = '''    review_n = int(_va["in_review_count"] or 0) if _va is not None else 0
    day_sale_p = sold_p - ret_p + review_p
    # S220 F-282b: the parked bills themselves, so Darpan sees WHICH need a name.
    # Bill, rupees (signed -- a parked return shows negative), the name as typed,
    # the phone's last four. Never the whole number.
    review_bills = []
    try:
        import json as _json                                        # noqa: PLC0415
        for r in con.execute(
                "SELECT r.raw_text, r.guess_name, r.guess_clinic_id, r.amount_p FROM sale_item_review r "
                "JOIN day_entry e ON e.id=r.day_entry_id "
                "WHERE e.unit=? AND e.business_date=? AND r.status='open' ORDER BY r.id",
                (_unit, iso)):
            try:
                raw = _json.loads(r["raw_text"] or "{}")
            except Exception:                                       # noqa: BLE001
                raw = {}
            review_bills.append(dict(
                bill=(raw.get("bill_no") or "?"), amount_p=int(r["amount_p"] or 0),
                name=(r["guess_name"] or raw.get("patient_name") or ""),
                clinic_id=(r["guess_clinic_id"] or raw.get("clinic_id") or ""),
                last4=(raw.get("phone_last4") or "")))
    except Exception:                                               # noqa: BLE001
        review_bills = []
'''
B_OLD = "                             review_p=review_p, review_n=review_n,   # S220 F-282\n"
B_NEW = ("                             review_p=review_p, review_n=review_n,   # S220 F-282\n"
         "                             review_bills=review_bills,             # S220 F-282b\n")
PAIRS = [("A", A_OLD, A_NEW), ("B", B_OLD, B_NEW)]


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
    bak = TARGET + ".bak_S220_f282b_" + stamp
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
