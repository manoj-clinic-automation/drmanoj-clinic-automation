#!/usr/bin/env python3
"""seed_icici_anchor.py -- kit S377_ICICI_COUNT. Records, once, the balance the BANK itself printed on the
owner's ICICI Sanjeevni statement for August 2026: closing 1,50,263.42 as on 31-Aug-2026 (opening 71,487.42,
27 POS credits, one 1,50,000 transfer to his HUF savings; the statement closes on itself). From that date the
position is that balance plus every settlement credited since, less the transfers recorded.

Idempotent: a second run says ALREADY and changes nothing. A different balance already on record is left
alone and named -- it is not overwritten.
  cd /root/finance && python3 seed_icici_anchor.py [--db PATH] [--dry-run]
"""
import argparse, datetime as dt, os, sys

AS_ON, BALANCE_P = "2026-08-31", 15026342
SOURCE = "ICICI Sanjeevni statement 01-Aug..31-Aug-2026, the bank's own closing balance"
ap = argparse.ArgumentParser(); ap.add_argument("--db"); ap.add_argument("--dry-run", action="store_true")
a = ap.parse_args()
APP = os.environ.get("FINANCE_APP_DIR", "/root/finance")
sys.path.insert(0, APP); os.chdir(APP)
if a.db:
    os.environ["FINANCE_DB"] = a.db
import finance_app as fa, sanjeevni_approvals as sa
with fa.app.app_context():
    con = fa.db(); sa.ensure_schema(con)
    have = sa.anchor_for(con, "icici")
    if have:
        same = (have["as_on"] == AS_ON and have["balance_p"] == BALANCE_P)
        print("ALREADY: ICICI anchored at %s as on %s%s" % (sa.rs(have["balance_p"]), have["as_on"],
              "" if same else "  -- DIFFERENT from this kit's figure; left as it is"))
        sys.exit(0)
    if a.dry_run:
        print("WOULD: anchor ICICI at %s as on %s" % (sa.rs(BALANCE_P), AS_ON)); sys.exit(0)
    con.execute("INSERT INTO bank_anchor (unit, account, as_on, balance_p, source, entered_by, entered_at) "
                "VALUES (?,?,?,?,?,?,?)",
                ("medical", "icici", AS_ON, BALANCE_P, SOURCE, "seed S377",
                 dt.datetime.now().replace(microsecond=0).isoformat()))
    con.commit()
    ip = sa.icici_position(con)
    print("DONE: ICICI anchored at %s as on %s" % (sa.rs(BALANCE_P), AS_ON))
    print("      it now holds %s -- %s on the statement, %s collected since, %s moved out"
          % (sa.rs(ip["holds_p"]), sa.rs(ip["base_p"]), sa.rs(ip["credited_p"]), sa.rs(ip["out_p"])))
