#!/usr/bin/env python3
"""walk_s307.py -- on the box, BEFORE anything is placed: the patched amir_day.py against a SCRATCH copy of the
live database. His bill list builds exactly as S285's does (same bills, same S285 warnings); every bill on it
renders; and, over every bill a live bill-wise export carries, the new checks say how many would warn.
Prints counts only.   python3 -B walk_s307.py <live amir_day.py> <patched amir_day.py> <scratch db>"""
import sys, sqlite3, datetime as dt, importlib.util
def load(p, n):
    s = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
try:
    A0, A1 = load(sys.argv[1], "amir_live"), load(sys.argv[2], "amir_new")
    cx = sqlite3.connect(sys.argv[3]); cx.row_factory = sqlite3.Row; A1._ensure(cx)
    day = (dt.datetime.utcnow() + dt.timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d")
    L0, L1 = A0._bills(cx, day), A1._bills(cx, day)
    key = lambda rows: sorted((r["supplier_norm"], r["bill_no"], r["bill_date"], tuple(r.get("warn") or [])) for r in rows)   # noqa: E731
    assert all(key(a) == key(b) for a, b in zip(L0, L1)), "the bill list or S285's warnings changed"
    for i, d in enumerate(L1[0] + L1[1] + L1[2]):
        A1._bill_block(i, d)
    rows = [dict(r) for r in cx.execute("SELECT b.supplier_norm, MAX(b.supplier) supplier, b.bill_no, b.bill_date, MAX(b.amount_p) amount_p "
                                        "FROM purchase_bill b JOIN purchase_export e ON e.md5=b.bw_md5 WHERE e.superseded_by IS NULL "
                                        "AND e.type='BILLWISE' GROUP BY b.supplier_norm, b.bill_no, b.bill_date")]
    tw = [x for x in (A1._twin_bills_s307(cx, d) for d in rows) if x]
    same = sum(1 for x in tw if any(s for _o, _a, s in x))
    rets = [d for d in rows if int(d["amount_p"] or 0) < 0]
    rw = sum(1 for d in rets if A1._supplier_warn_s285(cx, d))
    print("list today: %d today, %d carry, %d flagged (as before); on %d live bills: %d with a same-number twin (%d same amount); %d returns, %d warned"
          % (len(L1[0]), len(L1[1]), len(L1[2]), len(rows), len(tw), same, len(rets), rw))
    print("WALK OK the bill list is S285's, every bill renders, the new checks read")
except Exception as e:                                        # noqa: BLE001
    print("WALK RED %s: %s" % (type(e).__name__, e)); sys.exit(1)
