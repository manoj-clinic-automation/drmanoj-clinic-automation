#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""first_load_s454.py -- kit S454_BILL_REGISTER, part 1 (S454 3.5): yesterday's paper order, loaded once.

The order of 02-Oct was placed by phone from Marg's print, and part of it has arrived. The installer brings Darpan's own sheet of that day
(D:\\Downloads\\ClaudeCowork\\03_WORKING_PAPERS\\S283\\MARG_ORDER_SHEET_02-10-2026.txt -- it goes up with the installer to /tmp and is written
neither into the repository nor into the kit), converts it with the reader's OWN code (marg_txt S454, as the medical PC will), and runs the
loader on the result once with the switch that means ALREADY ORDERED: its new lines become one order per supplier, made "on paper" at 15:00
IST on the sheet's date (the moment the bill-scan tie compares with), awaiting arrival -- never a card under "Order karna hai". What Marg
already has as purchases clears itself (porders.detect_supplies; order_sheet.refresh). A later sheet that has reached the server by then is
loaded as new (order_sheet.load_pending). Idempotent: the same bytes again add nothing.

    first_load_s454.py --db DB --finance DIR --marg DIR --reader FILE --sheet FILE
Prints counts and supplier names only -- never a phone number.
"""
import argparse
import hashlib
import importlib.util
import os
import sqlite3
import sys
import tempfile


def _reader(path):
    spec = importlib.util.spec_from_file_location("marg_txt_s454_first_load", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def load_text(con, raw, reader_path, name="MARG_ORDER_SHEET (first load)"):
    """Convert with the reader's own code, then load once, as already ordered. Returns the loader's summary."""
    import order_sheet as OS                                  # noqa: PLC0415
    mt = _reader(reader_path)
    if mt.kind(raw) != "ORDER":
        raise SystemExit("STOP: the first-load sheet is not a complete PENDING ORDERS (PURCHASE) text (the reader says %r)" % mt.kind(raw))
    xls, info = mt.convert(raw)
    md5 = hashlib.md5(xls).hexdigest()
    d = tempfile.mkdtemp(prefix="s454_first_")
    p = os.path.join(d, "first_load_%s.XLS" % md5[:8])
    try:
        with open(p, "wb") as fh:
            fh.write(xls)
        r = OS.load_file(con, p, md5, name, "first_load", "", as_ordered=True)
    finally:
        try:
            os.remove(p)
            os.rmdir(d)
        except OSError:
            pass
    r["md5"] = md5
    r["rows"] = info.get("rows")
    return r


def main():
    ap = argparse.ArgumentParser()
    for k in ("--db", "--finance", "--marg", "--reader", "--sheet"):
        ap.add_argument(k, required=True)
    a = ap.parse_args()
    for p in (a.finance, a.marg):
        if p not in sys.path:
            sys.path.insert(0, p)
    os.environ.setdefault("MARG_INGEST_DIR", a.marg)
    con = sqlite3.connect(a.db, timeout=60)
    con.row_factory = sqlite3.Row
    import order_sheet as OS                                  # noqa: PLC0415
    import porders                                            # noqa: PLC0415
    OS.ensure(con)
    raw = open(a.sheet, "rb").read()
    r = load_text(con, raw, a.reader)
    if r.get("already"):
        print("S454 first load: these bytes are already loaded (md5 %s) -- nothing added" % r["md5"][:8])
    else:
        print("S454 first load: sheet of %s, %d lines -- %d new, %d old pending, %d known; md5 %s" % (r["newest"], r["lines"], r["new"], r["old"], r["known"], r["md5"][:8]))
        for o in r.get("paper_orders") or []:
            print("  order #%d  %-34s %d line(s), made on paper %sT15:00 IST" % (o["order_id"], o["supplier"], o["lines"], r["newest"]))
        if r.get("unresolved"):
            print("  names not found in Marg's stock list: %s" % ", ".join(x["item"] for x in r["unresolved"]))
    later = OS.load_pending(con)
    print("  later sheets the door had taken, loaded as new: %d" % later)
    n = porders.detect_supplies(con)
    OS.refresh(con)
    print("  cleared by Marg's purchases: %d order line(s)" % n)
    for row in con.execute("SELECT o.vendor, l.item, l.billed_qty, l.billed_bill_no FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                           "WHERE o.order_via='paper' AND l.billed_qty IS NOT NULL ORDER BY o.vendor, l.item"):
        print("    %s · %s · billed %s (bill %s)" % (row[0], row[1], row[2], row[3]))
    for row in con.execute("SELECT supplier, item_printed, line_date, marg_date FROM order_sheet_line WHERE state IN ('old','lapsed') ORDER BY supplier, line_date"):
        print("  old pending  %-30s %-22s %s  %s" % (row[0], row[1], row[2], ("aa chuka %s" % row[3]) if row[3] else "nahi aaya"))
    c = con.execute("SELECT cmp FROM order_sheet WHERE md5=?", (r["md5"],)).fetchone()
    if c and c[0]:
        import json                                           # noqa: PLC0415
        j = json.loads(c[0])
        print("  the comparison: the system agreed on %s of %s items with Darpan's sheet (only on the sheet %d, only on the system's list %d; stock as on %s)"
              % (j.get("x"), j.get("y"), len(j.get("only_sheet") or []), len(j.get("only_system") or []), j.get("as_on")))
    con.commit()
    print("S454 first load done")


if __name__ == "__main__":
    main()
