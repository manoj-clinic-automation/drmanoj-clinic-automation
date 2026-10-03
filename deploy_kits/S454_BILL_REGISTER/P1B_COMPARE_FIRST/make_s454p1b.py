#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s454p1b.py -- kit S454_BILL_REGISTER, part 1B: the comparison of a sheet loaded "as already ordered" is made BEFORE its own paper
orders (CLAUDE.md rule 2: built from the live bytes, the anchor exactly once, FROM -> TO pinned).

Part 1's first load made the sheet's paper orders first and compared after: S410's plan then counted those very orders as on the way
(order_rules._on_order_units) and dropped their items, so the owner's card read "the system agreed on 0 of 21" where the truth is 5 of 21.
A sheet that arrives through the door (not "as ordered") was never affected.

    make_s454p1b.py --finance /root/finance --out DIR
"""
import argparse
import hashlib
import os

FROM = {"order_sheet.py": "4cf2f231ef026904d1ae42754846aea7"}
OLD = ('''    made = []
    if as_ordered and new_ids:
        made = _paper_orders(con, sid, new_ids, newest)
    try:
        compare(con, sid)
    except Exception as e:                                    # noqa: BLE001 -- the comparison never stops a load
        con.execute("UPDATE order_sheet SET cmp=? WHERE id=?", (json.dumps(dict(error=str(e)[:200])), sid))
    con.commit()
''')
NEW = ('''    try:                                                      # S454 P1B: compared BEFORE the sheet's own paper orders -- else S410's
        compare(con, sid)                                     # plan counts them as on the way and drops their items (0 of 21)
    except Exception as e:                                    # noqa: BLE001 -- the comparison never stops a load
        con.execute("UPDATE order_sheet SET cmp=? WHERE id=?", (json.dumps(dict(error=str(e)[:200])), sid))
    con.commit()
    made = []
    if as_ordered and new_ids:
        made = _paper_orders(con, sid, new_ids, newest)
''')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    f = "order_sheet.py"
    raw = open(os.path.join(a.finance, f), "rb").read()
    m = hashlib.md5(raw).hexdigest()
    if m != FROM[f]:
        raise SystemExit("STOP: %s is %s, not its FROM pin %s -- nothing built" % (f, m, FROM[f]))
    txt = raw.decode("utf-8")
    if txt.count(OLD) != 1:
        raise SystemExit("STOP: the anchor occurs %d times in %s -- nothing built" % (txt.count(OLD), f))
    out = txt.replace(OLD, NEW, 1).encode("utf-8")
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, f), "wb") as fh:
        fh.write(out)
    print("built %-18s %s -> %s  (1 edit)" % (f, m[:8], hashlib.md5(out).hexdigest()))


if __name__ == "__main__":
    main()
