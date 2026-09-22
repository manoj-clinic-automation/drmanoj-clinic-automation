#!/usr/bin/env python3
"""resolve_now.py -- kit S371_PURCHASE_WRONG_RESOLVE. Runs the S371 resolver once over every WRONG purchase bill
in the live database (or --db PATH): a bill whose live Marg amount is the amount marked right becomes CORRECT,
with its audit row. Prints supplier, bill number and rupees only. Idempotent.
  cd /root/finance && python3 resolve_now.py [--db PATH] [--dry-run]
"""
import argparse, os, sys
ap = argparse.ArgumentParser(); ap.add_argument("--db"); ap.add_argument("--dry-run", action="store_true")
a = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.environ.get("FINANCE_APP_DIR", "/root/finance")
sys.path.insert(0, APP); os.chdir(APP)
if a.db:
    os.environ["FINANCE_DB"] = a.db
import finance_app as fa, purchase_app as pa
with fa.app.app_context():
    con = fa.db(); pa._ensure(con)
    wrong = con.execute("SELECT supplier, bill_no, amount_p, wrong_amount_p FROM purchase_bill WHERE verdict='WRONG'").fetchall()
    print("WRONG bills before: %d" % len(wrong))
    for w in wrong:
        print("   %s %s  Marg now %s  marked right %s" % (w[0], w[1], pa._r(w[2]), pa._r(w[3]) if w[3] is not None else "?"))
    if a.dry_run:
        con.rollback(); print("dry run -- nothing changed"); sys.exit(0)
    done = pa._resolve_wrong(con, who="resolve_now S371")
    con.commit()
    for d in done:
        print("RESOLVED %s %s at %s" % (d[1], d[2], pa._r(d[3])))
    left = con.execute("SELECT COUNT(*) FROM purchase_bill WHERE verdict='WRONG'").fetchone()[0]
    print("resolved %d; WRONG bills left: %d" % (len(done), left))
