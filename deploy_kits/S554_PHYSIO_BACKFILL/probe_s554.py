#!/usr/bin/env python3
"""probe_s554.py -- kit S554_PHYSIO_BACKFILL, the look AFTER placing. Runs the REAL finance app from a scratch copy of the PLACED
/root/finance on a backup-API copy of the live database (header sign-in for this process only) and, signed in as manoj, reads:
  the register's clinic tab (does it offer 01-Oct?), the report for October 2026 (is every October reception day matched, none
  'before the register'?), and /finance/aaj?as=bhati with its list (does Bhati's duty line show, opening the oldest day?).
Dates and counts only -- no name, no number of any person, no rupee figure.
    python3 -B probe_s554.py --fin <scratch copy of the placed /root/finance> --db <copy of finance.db>
Prints 'PROBE OK ...' when all three agree with the floor and with the duty's own SQL; exit 1 otherwise."""
import argparse
import datetime as dt
import json
import os
import re
import sqlite3
import sys

DID = "bhati.physio_register"
BASE = "https://followup.dr-manoj.in"


def text(h):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h or "")).strip()


def report_row(h, day):
    m = re.search(r"<tr><td class='d'>%s</td>(.*?)</tr>" % re.escape(dt.date.fromisoformat(day).strftime("%a %d-%b")), h or "")
    return text(m.group(1)) if m else None


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
    fl = (con.execute("SELECT value FROM setting WHERE key='physio_book.from'").fetchone() or [None])[0]
    oct_days = [r[0] for r in con.execute("SELECT business_date FROM clinic_physio_day WHERE business_date BETWEEN '2026-10-01' AND ? "
                                          "AND business_date <= '2026-10-31' ORDER BY business_date", (today,))]
    con.close()
    os.environ.update(FINANCE_DB=dbp, FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_DEV_USER="", FINANCE_DEV_ROLE="",
                      AAJ_DUTIES_JSON=os.path.join(fin, "aaj_duties.json"))
    os.environ.pop("PHYSIO_BOOK_NOW", None)
    sys.path.insert(0, fin)
    os.chdir(fin)
    import finance_app as fa                       # noqa: E402
    c = fa.app.test_client(use_cookies=False)
    hd = {"X-Clinic-User": "manoj", "X-Clinic-Role": ""}
    ok = True

    print("the setting physio_book.from on the live copy: %s" % (fl or "absent"))
    ok = ok and fl == "2026-10-01"
    r = c.get("/finance/physio/book", base_url=BASE, headers=hd)
    h = r.get_data(as_text=True)
    offers = "value='2026-10-01'" in h and "value='2026-09-30'" not in h
    print("as manoj: /finance/physio/book -> %d; the clinic tab offers 01-Oct: %s (30-Sep not offered)" % (r.status_code, "yes" if offers else "NO"))
    ok = ok and r.status_code == 200 and offers

    r = c.get("/finance/physio/book/report?m=2026-10", base_url=BASE, headers=hd)
    h = r.get_data(as_text=True)
    said = "Days are matched from 01-Oct-2026" in text(h)
    tally = {"tick": 0, "differs": 0, "reception not written": 0, "before the register": 0, "no row": 0}
    for d in oct_days:
        row = report_row(h, d)
        if row is None:
            tally["no row"] += 1
        elif "before the register" in row:
            tally["before the register"] += 1
        elif "reception not written" in row:
            tally["reception not written"] += 1
        elif "✓" in row:
            tally["tick"] += 1
        else:
            tally["differs"] += 1
    print("as manoj: /finance/physio/book/report?m=2026-10 -> %d; 'Days are matched from 01-Oct-2026': %s; October's %d reception days: "
          "%d agree, %d differ, %d before the register, %d without a row" % (r.status_code, "yes" if said else "NO", len(oct_days), tally["tick"],
                                                                             tally["differs"], tally["before the register"], tally["no row"]))
    ok = ok and r.status_code == 200 and said and tally["before the register"] == 0 and tally["no row"] == 0

    pg = c.get("/finance/aaj?as=bhati", base_url=BASE, headers=hd)
    r = c.get("/finance/aaj/api/list?as=bhati", base_url=BASE, headers=hd)
    try:
        j = json.loads(r.get_data(as_text=True))
    except ValueError:
        j = {}
    rows = [dict(x, section=s["key"]) for s in (j.get("sections") or []) for x in s["rows"]]
    mine = [x for x in rows if x.get("id") == DID]
    print("as manoj: /finance/aaj?as=bhati -> %d; /finance/aaj/api/list?as=bhati -> %d, %d line(s) on Bhati's list" % (pg.status_code, r.status_code, len(rows)))
    print("the duty's SQL on the live figures (today %s): n = %s, since %s" % (today, n, since or "-"))
    if mine:
        print("SHOWN under '%s': '%s' -> opens %s" % (mine[0]["section"], mine[0]["text"], mine[0]["door"]))
    else:
        print("NOT SHOWN")
    ok = ok and pg.status_code == 200 and r.status_code == 200 and bool(j.get("ok")) and (bool(mine) == bool(n))
    if ok and mine:
        ok = mine[0]["door"] == "/finance/physio/book?day=%s" % since
    print(("PROBE OK: " if ok else "PROBE RED: ") + "the register offers 01-Oct, the report matches October from 01-Oct, and Bhati's line "
          + ("shows %s day(s) from %s" % (n, since) if mine else "does not show (the SQL reads %s)" % n))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
