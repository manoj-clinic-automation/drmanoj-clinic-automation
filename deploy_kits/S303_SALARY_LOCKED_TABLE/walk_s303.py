#!/usr/bin/env python3
"""walk_s303.py -- S303 (F-519): the live-shape walk of the salary lock desk.

THE KIT's staff_register.py over a SCRATCH COPY of the live staff_register.db, with the LIVE salary engine
(/root/staff_register/salary_policy.py) computing today's figures read-only. For every locked month the desk
must answer 200 and show the card; for 2026-08 the frozen table MUST read back and add up to the card, and
today's recompute total must not be shown. It prints, for August, each staff member whose recompute differs
from the locked run and what moved -- the answer F-519 asks for. Nothing is written except to the scratch copy.

Usage: SR_DB_PATH=/tmp/.../sr_walk.db python3 walk_s303.py <dir holding the kit staff_register.py> <live app dir>
"""
import os
import sqlite3
import sys

N = [0]


def check(name, cond):
    N[0] += 1
    if not cond:
        print("FAIL %d: %s" % (N[0], name))
        sys.exit(1)


def main():
    kit, live = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    dbp = os.path.abspath(os.environ.get("SR_DB_PATH", ""))
    if not dbp.startswith("/tmp/"):
        print("FAIL 0: refusing a database outside /tmp")
        sys.exit(1)
    sys.path.insert(0, kit)
    sys.path.insert(1, live)
    os.chdir(kit)
    os.environ["ATT_REGISTER_DB"] = dbp
    import staff_register as sr
    check("the kit copy is the module imported", os.path.dirname(os.path.abspath(sr.__file__)) == kit)
    check("the database is the scratch copy", os.path.abspath(sr.DB_PATH) == dbp)
    sr.init_db()
    P, perr = sr._policy_module()
    check("the live salary engine imports: %s" % perr, P is not None)
    check("the engine is the live one", os.path.dirname(os.path.abspath(P.__file__)) == live)
    con = sqlite3.connect(dbp)
    con.row_factory = sqlite3.Row
    months = [dict(r) for r in con.execute("SELECT ym, total_payout, report_html, status FROM locked_run ORDER BY ym")]
    check("a locked run exists for 2026-08", any(m["ym"] == "2026-08" and m["status"] == "locked" for m in months))
    c = sr.app.test_client()
    with c.session_transaction() as s:
        s["sr_user"], s["sr_role"] = "manoj", "override"
    lines = []
    for m in months:
        if m["status"] != "locked":
            continue
        card = "{:,}".format(int(m["total_payout"]))
        r = c.get("/register/salary?ym=%s" % m["ym"])
        t = r.get_data(as_text=True)
        check("%s: the desk answers 200" % m["ym"], r.status_code == 200)
        check("%s: the card shows the locked total" % m["ym"], "TOTAL PAYOUT &#8377;%s" % card in t)
        snap, why = sr.locked_snapshot(m["report_html"], m["total_payout"])
        if snap:
            check("%s: the table's TOTAL is the card's" % m["ym"], "<td><b>%s</b></td></tr>" % card in t)
            check("%s: no second (recompute) table" % m["ym"], "Computed by the NEW policy engine" not in t)
            lines.append("%s locked %s: frozen table read, %d rows, adds up" % (m["ym"], card, len(snap)))
        else:
            check("%s: unreadable frozen table says so, no second total" % m["ym"],
                  "could not be read back" in t and "Computed by the NEW policy engine" not in t)
            lines.append("%s locked %s: frozen table NOT readable (%s) -- desk shows the card only" % (m["ym"], card, why))
        check("%s: the frozen sheets open" % m["ym"], c.get("/register/salary/locked?ym=%s" % m["ym"]).status_code == 200)
    aug = [m for m in months if m["ym"] == "2026-08"][0]
    snap, why = sr.locked_snapshot(aug["report_html"], aug["total_payout"])
    check("2026-08: the frozen table reads back and adds up to the card (%s)" % why, snap is not None)
    res = P.compute("2026-08")
    diffs = sr.locked_differences(snap, res["staff"], P.money)
    now_total = int(round(sum(st["net"] for st in res["staff"])))
    lines.append("2026-08 today's recompute %s; differs for %d staff:" % ("{:,}".format(now_total), len(diffs)))
    for d in diffs:
        lines.append("   %s: locked %s, today %s (%s) -- %s" % (d["name"], d["locked"], d["today"], d["diff"] or "-", d["moved"]))
    for ln in lines:
        print("   " + ln)
    print("WALK OK — %d checks; %d locked month(s); August reads back and adds up to the card; %d staff differ today"
          % (N[0], sum(1 for m in months if m["status"] == "locked"), len(diffs)))


if __name__ == "__main__":
    main()
