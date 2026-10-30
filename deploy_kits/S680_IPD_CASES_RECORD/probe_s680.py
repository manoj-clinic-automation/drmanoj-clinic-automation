#!/usr/bin/env python3
"""probe_s680.py -- kit S680 (IPD cases, the record; as S579/S581), the look AS MANOJ and AS SHAVEZ through the REAL finance app,
on COPIES only.
    python3 -B probe_s680.py --fin <scratch copy of the /root/finance files to test> --db <a COPY of finance.db> [--expect-red]
The real finance_app is loaded from the scratch copy, on the database copy, with header sign-in for this process only (no live
secret). As manoj: IPD cases with its three status filters (S370, D804), the vendors page, the hospital payments page, Settings. As shavez: IPD cases
WITH the hospital money (D801), the vendors page and Settings refused. As bhawna and darpan: refused at the front gate (no row in 'surgery'). Prints 'PROBE OK ...' and
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
                      SURGERY_PAPER_DIR="/tmp/s680_probe_papers",
                      SURGERY_CONSOLE_DB="/tmp/s680_probe_none/console.db", SURGERY_CASE_LEDGER="/tmp/s680_probe_none/case_ledger.csv",
                      SURGERY_CALL_URL="http://127.0.0.1:9/call", SURGERY_WA_ENV="/tmp/s680_probe_none/wa.env",
                      SURGERY_RING_AGENTS="/tmp/s680_probe_none/ring_agents.json")
    sys.path.insert(0, fin)
    os.chdir(fin)
    res = []
    try:
        import finance_app as fa                 # noqa: E402
        c = fa.app.test_client(use_cookies=False)

        def get(path, user):
            return c.get(path, headers={"X-Clinic-User": user})
        r = get("/finance/surgery", "manoj")
        res.append(("manoj sees IPD cases with the three status filters (D804)", r.status_code == 200 and b"<h1>IPD cases" in r.data
                    and b"name=pt" in r.data and b"name=money" in r.data and b"name=imp" in r.data))
        r = get("/finance/surgery/settings", "manoj")
        res.append(("manoj opens Settings (admission, nursing, share, sources)", r.status_code == 200 and b"Admission charge" in r.data
                    and b"Awdhesh" in r.data))
        r = get("/finance/surgery/vendors", "manoj")
        res.append(("manoj opens the vendors' ledgers", r.status_code == 200 and b"Implant vendors" in r.data))
        r = get("/finance/surgery/receipts", "manoj")
        res.append(("manoj opens the hospital payments", r.status_code == 200 and b"Hospital payments" in r.data))
        r = get("/finance/surgery/new", "manoj")
        res.append(("the new-case page lists the five payers, the three types, the sources, UHID, mobile and the TPA drop-down", r.status_code == 200
                    and b"Other scheme" in r.data and b"Cash \xc2\xb7 package" in r.data and b"TPA cashless" in r.data and b"Conservative" in r.data
                    and b"ipd_sources" in r.data and b"name=uhid" in r.data and b"name=mobile" in r.data and b"+ add a name" in r.data))
        r = get("/finance/surgery", "shavez")
        res.append(("shavez sees IPD cases WITH the hospital money (D801) as a status and a filter (D804)", r.status_code == 200
                    and b"<h1>IPD cases" in r.data and b"Hospital money" in r.data and b"name=money" in r.data))
        r = get("/finance/surgery/settings", "shavez")
        res.append(("shavez is refused Settings", r.status_code == 403))
        r = get("/finance/surgery/backfill", "shavez")
        res.append(("shavez opens the backfill page for old cases (from 01-Apr-2025)", r.status_code == 200 and b"01-Apr-2025" in r.data))
        r = get("/finance/surgery/vendors", "shavez")
        res.append(("shavez is refused the vendors' ledgers", r.status_code == 403))
        for who in ("bhawna", "darpan"):
            r = get("/finance/surgery", who)
            res.append(("%s is refused (no row in 'surgery')" % who, r.status_code in (302, 403)))
        r = c.post("/finance/surgery", data={"q": "+91 99999" " 00000"}, headers={"X-Clinic-User": "manoj"})
        res.append(("S370: the list's search is posted through the real app", r.status_code == 200 and b"<h1>IPD cases" in r.data))
        # S370: the IVR call through the real app and its connection -- made-up call list and key, the call service a dead port
        os.makedirs("/tmp/s680_probe_none", exist_ok=True)
        open("/tmp/s680_probe_none/wa.env", "w").write("CALL_API_SECRET=probe\n")
        open("/tmp/s680_probe_none/ring_agents.json", "w").write('{"agents": {"90000' '00009": {"user": "manoj", "name": "PROBE"}}}')
        r = c.post("/finance/surgery/new", data={"patient": "PROBE S680 CALL", "payer": "cash", "source": "Clinic", "mobile": "90000" "00009"},
                   headers={"X-Clinic-User": "manoj"})
        import sqlite3 as _sq
        _c = _sq.connect(dbp)
        pid = _c.execute("SELECT id FROM surg_case WHERE patient='PROBE S680 CALL'").fetchone()
        _c.close()
        r = c.post("/finance/surgery/case/%d/call" % (pid[0] if pid else 0), data={"n": "0"}, headers={"X-Clinic-User": "manoj"}) if pid else None
        _c = _sq.connect(dbp)
        kept = _c.execute("SELECT result, last4 FROM surg_call WHERE case_id=?", (pid[0] if pid else 0,)).fetchall()
        _c.close()
        res.append(("S370: the IVR call through the real app ends 'did not answer' at a dead port, kept with the last 4 digits only",
                    r is not None and r.status_code == 302 and "err=calldown" in r.headers.get("Location", "") and kept == [("error", "0009")]))
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
