#!/usr/bin/env python3
"""state_s556.py -- kit S556_REFUSED_TEXT_ROAD: the install-day state (charter 7), read on a COPY of finance.db. Writes nothing.
    python3 -B state_s556.py --fin <a folder with the reports_tile.py / reports_watch.py / order_sheet.py to read with> --db <a COPY of finance.db>
                             --map <DUTY_MAP.json>
Prints only state names, times and counts: the two morning rows (sale report, closing stock) as the page judges them now, whether either is
held, Darpan's order-sheet card (refused or not), the reader stops received today, and the three duties' counts by the map given."""
import argparse
import json
import os
import sqlite3
import sys


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.curdir) != here]
    ap = argparse.ArgumentParser()
    for k in ("--fin", "--db", "--map"):
        ap.add_argument(k, required=True)
    a = ap.parse_args()
    assert os.path.abspath(a.db).startswith("/tmp/") or os.environ.get("S556_WALK_ANYWHERE") == "1", "a COPY in /tmp only"
    sys.path.insert(0, os.path.abspath(a.fin))
    import reports_tile as RT                                 # noqa: E402
    import order_sheet as OS                                  # noqa: E402
    c = sqlite3.connect(a.db, timeout=60)
    c.row_factory = sqlite3.Row
    s = RT.status(c)
    for r in s["rows"]:
        if r.get("pair"):
            w = r.get("s500") or {}
            print("   %s: %s%s (tries %s, wrong %s, loose lines %d)" % (r["label"], r["state"], (" at " + r["at"]) if r.get("at") else "",
                                                                     w.get("tries"), w.get("wrong"), len(r.get("loose") or [])))
    n_stop = c.execute("SELECT COUNT(*) FROM mi_file WHERE substr(received_at,1,10)=date('now','localtime') AND verdict<>'VERIFIED' AND "
                       "reason GLOB 'the medical PC refused it: the reader refused it (line [0-9]*)' AND reason NOT GLOB '*(line *[^0-9]*)'").fetchone()[0]
    print("   reader stops received today: %d; held rows on the page: %d" % (n_stop, sum(1 for r in s["rows"] if r.get("state") == "held")))
    try:
        dc = OS.darpan_card(c)
        print("   Darpan's order-sheet card: refused %s%s" % (dc.get("refused"), (" (" + dc.get("refused_at") + ")") if dc.get("refused") else ""))
    except Exception as e:                                    # noqa: BLE001
        print("   Darpan's order-sheet card: could not be read (%s)" % e.__class__.__name__)
    m = json.load(open(a.map, encoding="utf-8"))
    for d in m["duties"]:
        if d["id"] in ("shavez.sale_report", "shavez.closing_stock", "darpan.order_sheet"):
            r = c.execute(d["due_sql"]).fetchone()
            print("   map v%s %s: n %s" % (m.get("version"), d["id"], r[0]))
    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
