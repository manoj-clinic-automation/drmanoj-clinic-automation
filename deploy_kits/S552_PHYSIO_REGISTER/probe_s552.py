#!/usr/bin/env python3
"""probe_s552.py -- kit S552_PHYSIO_REGISTER, the after-placing look AS MANOJ (checker). READ-ONLY on a COPY.
    python3 -B probe_s552.py --fin <scratch copy of the PLACED /root/finance files> --db <a fresh COPY of the live finance.db>
The real finance app is loaded from the scratch copy of the files now live, on a copy of the live database taken after the data
step, with header sign-in for this process only (no live secret). It asks, as manoj: the report, Bhati's page, the Physiotherapy
page; as bhati: his page (must be the one 'band hai' line while the switch is 0). Prints 'PROBE OK ...'; exit 1 otherwise."""
import argparse
import os
import sqlite3
import sys

OFF_LINE = "Yeh page abhi band hai — Dr Manoj ke kehne par khulega."


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fin", required=True)
    ap.add_argument("--db", required=True)
    a = ap.parse_args()
    fin, dbp = os.path.abspath(a.fin), os.path.abspath(a.db)
    assert fin.startswith("/tmp/") and dbp.startswith("/tmp/"), "the probe runs on scratch copies in /tmp only"
    con = sqlite3.connect("file:%s?mode=ro" % dbp, uri=True)
    on = con.execute("SELECT value FROM setting WHERE key='physio_book.on'").fetchone()
    roles = sorted(tuple(r) for r in con.execute("SELECT username, role FROM unit_role WHERE unit='physiobook' AND active=1"))
    con.close()
    os.environ.update(FINANCE_DB=dbp, FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_DEV_USER="", FINANCE_DEV_ROLE="")
    sys.path.insert(0, fin)
    os.chdir(fin)
    import finance_app as fa                     # noqa: E402
    c = fa.app.test_client(use_cookies=False)

    def get(u, p):
        r = c.get(p, base_url="https://followup.dr-manoj.in", headers={"X-Clinic-User": u, "X-Clinic-Role": ""})
        return r.status_code, r.get_data(as_text=True)

    rep = get("manoj", "/finance/physio/book/report")
    book = get("manoj", "/finance/physio/book")
    phy = get("manoj", "/finance/physio")
    bh = get("bhati", "/finance/physio/book")
    failed = [n for n, _w in fa._MOUNT_FAILED]
    checks = [
        ("physio_book mounted in the app built from the placed files", "physio_book" in sys.modules and "physio_book" not in failed),
        ("physio_book.on = 0 on the live database (switched off for Bhati)", bool(on) and on[0] == "0"),
        ("physiobook roles: bhati maker, bhawna checker, manoj checker", roles == [("bhati", "maker"), ("bhawna", "checker"), ("manoj", "checker")]),
        ("as manoj: the report loads (200, 'Day-wise', the switch 'Open the register for Bhati')",
         rep[0] == 200 and "Day-wise" in rep[1] and "Open the register for Bhati" in rep[1]),
        ("as manoj: Bhati's page loads (200, the preview with the slip entry)", book[0] == 200 and "Slip likhiye" in book[1] and "Preview" in book[1]),
        ("as manoj: the Physiotherapy page carries 'Physio register ›' and 'Report ›'",
         phy[0] == 200 and "Physio register ›" in phy[1] and "Report ›" in phy[1]),
        ("as bhati: one line, the register is closed", bh[0] == 200 and OFF_LINE in bh[1] and "Slip likhiye" not in bh[1]),
    ]
    bad = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(("  ok   " if ok else "  FAIL ") + n)
    if bad:
        print("PROBE RED: %d of %d (statuses report %s, book %s, physio %s, bhati %s; failed mounts %s)" % (
            len(bad), len(checks), rep[0], book[0], phy[0], bh[0], failed))
        return 1
    print("PROBE OK: as manoj the report and Bhati's page load; physio_book.on = 0; bhati sees the one 'band hai' line")
    return 0


if __name__ == "__main__":
    sys.exit(main())
