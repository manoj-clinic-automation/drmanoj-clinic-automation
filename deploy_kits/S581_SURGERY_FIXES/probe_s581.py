#!/usr/bin/env python3
"""probe_s581.py -- kit S581 (as S579), the look AS MANOJ and AS SHAVEZ through the REAL finance app, on COPIES only.
    python3 -B probe_s581.py --fin <scratch copy of the /root/finance files to test> --db <a COPY of finance.db> [--expect-red]
The real finance_app is loaded from the scratch copy, on the database copy, with header sign-in for this process only (no live
secret). As manoj: the cases list with the money columns, the vendors page, the hospital payments page. As shavez: the list without
money, the vendors page refused. As bhawna and darpan: refused at the front gate (no row in 'surgery'). Prints 'PROBE OK ...' and
exits 0 when all hold; with --expect-red it prints 'PROBE OK negative control ...' when they do NOT all hold (the old files)."""
import argparse
import os
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fin", required=True)
    ap.add_argument("--db", required=True)
    ap.add_argument("--expect-red", action="store_true")
    a = ap.parse_args()
    fin, dbp = os.path.abspath(a.fin), os.path.abspath(a.db)
    assert fin.startswith("/tmp/") and dbp.startswith("/tmp/"), "the probe runs on scratch copies in /tmp only"
    os.environ.update(FINANCE_DB=dbp, FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_DEV_USER="", FINANCE_DEV_ROLE="",
                      SURGERY_PAPER_DIR="/tmp/s581_probe_papers")
    sys.path.insert(0, fin)
    os.chdir(fin)
    res = []
    try:
        import finance_app as fa                 # noqa: E402
        c = fa.app.test_client(use_cookies=False)

        def get(path, user):
            return c.get(path, headers={"X-Clinic-User": user})
        r = get("/finance/surgery", "manoj")
        res.append(("manoj sees the cases with the money columns", r.status_code == 200 and b"Surgery cases" in r.data and b"Due from hospital" in r.data))
        r = get("/finance/surgery/vendors", "manoj")
        res.append(("manoj opens the vendors' ledgers", r.status_code == 200 and b"Implant vendors" in r.data))
        r = get("/finance/surgery/receipts", "manoj")
        res.append(("manoj opens the hospital payments", r.status_code == 200 and b"Hospital payments" in r.data))
        r = get("/finance/surgery/new", "manoj")
        res.append(("the new-case page lists the four payers", r.status_code == 200 and b"Deendayal" in r.data and b"Ayushman" in r.data))
        r = get("/finance/surgery", "shavez")
        res.append(("shavez sees the cases without money", r.status_code == 200 and b"Due from hospital" not in r.data))
        r = get("/finance/surgery/vendors", "shavez")
        res.append(("shavez is refused the vendors' ledgers", r.status_code == 403))
        for who in ("bhawna", "darpan"):
            r = get("/finance/surgery", who)
            res.append(("%s is refused (no row in 'surgery')" % who, r.status_code in (302, 403)))
        r = get("/finance/healthz", "manoj")
        res.append(("health still answers", r.status_code == 200))
        res.append(("surgery_cases mounted", "surgery_cases" not in [n for n, _w in getattr(fa, "_MOUNT_FAILED", [])]
                    and "surgery_cases" in sys.modules))
    except Exception as e:                       # noqa: BLE001
        res.append(("the finance app loads (%s: %s)" % (type(e).__name__, str(e)[:120]), False))
    for name, ok in res:
        print(("  ok   " if ok else "  RED  ") + name)
    green = sum(1 for _n, ok in res if ok)
    allok = res and green == len(res)
    if a.expect_red:
        if allok:
            print("PROBE RED: the old files passed -- the probe cannot tell old from new")
            return 1
        print("PROBE OK negative control: %d of %d green on the old files" % (green, len(res)))
        return 0
    if allok:
        print("PROBE OK %d of %d" % (green, len(res)))
        return 0
    print("PROBE RED %d of %d" % (green, len(res)))
    return 1


if __name__ == "__main__":
    sys.exit(main())
