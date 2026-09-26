#!/usr/bin/env python3
"""seed_s410.py -- kit S410_MEDICINE_ORDERING (D626). INSERT OR IGNORE only, plus the rules seed (owner-set fields never overwritten):
  setting        order.* (the shop-wide numbers of the owner's sitting), order.go_live = today, order.interim_from = today + 7
  tables         order_supplier_rule (one row per supplier with bills in 90 days -- never the orthotics vendor; Kedar's D626 row),
                 order_rule_audit, order_holiday, order_item_rule, order_proposal, order_notice
Usage: seed_s410.py DB_PATH   (FINANCE_DIR names the folder holding order_rules.py + purchase_app.py; default /root/finance)
"""
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def seed(path):
    fin = os.environ.get("FINANCE_DIR", "/root/finance")
    for d in (fin, HERE):
        if os.path.isfile(os.path.join(d, "purchase_app.py")) and d not in sys.path:
            sys.path.insert(0, d)
    if os.path.isfile(os.path.join(HERE, "order_rules.py")) and not os.path.isfile(os.path.join(fin, "order_rules.py")) and HERE not in sys.path:
        sys.path.insert(0, HERE)
    os.environ.setdefault("FINANCE_DB", path)
    import order_rules  # noqa: E402
    con = sqlite3.connect(path, timeout=30)
    con.row_factory = sqlite3.Row
    order_rules.ensure(con)
    n = order_rules.reseed(con, who="seed S410")
    rows = [dict(r) for r in con.execute("SELECT supplier_norm, cadence, order_days, blocked_days, lead_days, cover_cap_days, single_source_extra, review_on FROM order_supplier_rule ORDER BY supplier_norm")]
    ked = next((r for r in rows if r["supplier_norm"] == order_rules.KEDAR), None)
    go = con.execute("SELECT value FROM setting WHERE key='order.go_live'").fetchone()[0]
    frm = con.execute("SELECT value FROM setting WHERE key='order.interim_from'").fetchone()[0]
    con.close()
    if ked is None or ked["cadence"] != "custom" or ked["order_days"] != "MON,FRI" or ked["single_source_extra"] != 0 or ked["cover_cap_days"] != 14:
        print("SEED WRONG: Kedar's row is %s" % ked)
        return 1
    if any(r["supplier_norm"] == "YUVIKA SURGICALS" for r in rows):
        print("SEED WRONG: the orthotics vendor has a medicine rule")
        return 1
    by = {}
    for r in rows:
        by[r["cadence"]] = by.get(r["cadence"], 0) + 1
    print("seed: %d supplier rules (%s); Kedar custom Mon+Fri, Thursday open, extra waived, cap 14, review %s; go-live %s; interim from %s; %d rows touched this run"
          % (len(rows), ", ".join("%s %d" % (k, v) for k, v in sorted(by.items())), ked["review_on"], go, frm, n))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(seed(sys.argv[1]))
