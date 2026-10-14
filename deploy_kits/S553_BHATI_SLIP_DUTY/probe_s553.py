#!/usr/bin/env python3
"""probe_s553.py -- kit S553_BHATI_SLIP_DUTY, the look AFTER placing. Runs the REAL finance app from a scratch copy of the PLACED
/root/finance on a backup-API copy of the live database (header sign-in for this process only), signs in as manoj and reads
/finance/aaj?as=bhati (the page) and /finance/aaj/api/list?as=bhati (what it draws). Says whether Bhati's new line shows and
why, from the live figures -- dates and counts only, no name, no number of any person.
    python3 -B probe_s553.py --fin <scratch copy of the placed /root/finance> --db <copy of finance.db>
Prints 'PROBE OK ...' when what the list shows is what the duty's own SQL says; exit 1 otherwise."""
import argparse
import json
import os
import sqlite3
import sys

DID = "bhati.physio_register"
BASE = "https://followup.dr-manoj.in"


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.curdir) != here]      # never import from the kit folder
    ap = argparse.ArgumentParser()
    ap.add_argument("--fin", required=True)
    ap.add_argument("--db", required=True)
    a = ap.parse_args()
    fin, dbp = os.path.abspath(a.fin), os.path.abspath(a.db)
    assert dbp.startswith("/tmp/") and fin.startswith("/tmp/"), "the probe runs on scratch copies in /tmp only"
    duties = json.load(open(os.path.join(fin, "aaj_duties.json"), encoding="utf-8"))
    du = next((x for x in duties["extra"] if x.get("id") == DID), None)
    if du is None:
        print("PROBE RED: the placed duties file does not hold %s" % DID)
        return 1
    con = sqlite3.connect("file:%s?mode=ro" % dbp, uri=True)
    n, since = con.execute(du["sql"]).fetchone()
    today = con.execute("SELECT date('now','localtime')").fetchone()[0]
    days = con.execute("SELECT business_date, cash_p, upi_p FROM clinic_physio_day WHERE business_date >= '2026-10-14' AND business_date < ? "
                       "ORDER BY business_date", (today,)).fetchall()
    con.close()
    os.environ.update(FINANCE_DB=dbp, FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_DEV_USER="", FINANCE_DEV_ROLE="",
                      AAJ_DUTIES_JSON=os.path.join(fin, "aaj_duties.json"))
    sys.path.insert(0, fin)
    os.chdir(fin)
    import finance_app as fa                       # noqa: E402
    c = fa.app.test_client(use_cookies=False)
    hd = {"X-Clinic-User": "manoj", "X-Clinic-Role": ""}
    pg = c.get("/finance/aaj?as=bhati", base_url=BASE, headers=hd)
    r = c.get("/finance/aaj/api/list?as=bhati", base_url=BASE, headers=hd)
    try:
        j = json.loads(r.get_data(as_text=True))
    except ValueError:
        j = {}
    rows = [dict(x, section=s["key"]) for s in (j.get("sections") or []) for x in s["rows"]]
    mine = [x for x in rows if x.get("id") == DID]
    print("as manoj: /finance/aaj?as=bhati -> %d (the list page); /finance/aaj/api/list?as=bhati -> %d, %d line(s) on Bhati's list" % (pg.status_code, r.status_code, len(rows)))
    print("the duty's SQL on the live figures (today %s): n = %s, since %s" % (today, n, since or "-"))
    if days:
        print("reception's physio days from 14-Oct before today: %s" % ", ".join("%s (%s)" % (d, "money" if (c_ or 0) + (u or 0) > 0 else "Rs 0") for d, c_, u in days))
    else:
        print("reception's physio days from 14-Oct before today: none yet (today %s is never counted; the first day that can be due is 14-Oct, from 15-Oct)" % today)
    if mine:
        print("SHOWN under '%s': '%s' -> opens %s" % (mine[0]["section"], mine[0]["text"], mine[0]["door"]))
        why = "%s day(s) where reception wrote physio money and his register's cash / UPI do not agree; the oldest %s" % (n, since)
    else:
        why = ("no day from 14-Oct up to yesterday with reception's physio money disagreeing with his register" if not n
               else "NOT SHOWN although the SQL says %s day(s) -- see the list's own state" % n)
        print("NOT SHOWN: %s" % why)
    ok = pg.status_code == 200 and r.status_code == 200 and j.get("ok") and (bool(mine) == bool(n))
    if ok and mine:
        ok = mine[0]["door"] == "/finance/physio/book?day=%s" % since
    print(("PROBE OK: " if ok else "PROBE RED: ") + ("the line shows -- " if mine else "the line does not show -- ") + why)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
