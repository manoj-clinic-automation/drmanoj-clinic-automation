#!/usr/bin/env python3
"""probe_s682.py -- kit S682 (IPD kit 4; S681's probe carried, the implant bills desk added), the look AS MANOJ and AS SHAVEZ through the REAL finance app,
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
                      SURGERY_PAPER_DIR="/tmp/s682_probe_papers",
                      SURGERY_CONSOLE_DB="/tmp/s682_probe_none/console.db", SURGERY_CASE_LEDGER="/tmp/s682_probe_none/case_ledger.csv",
                      SURGERY_CALL_URL="http://127.0.0.1:9/call", SURGERY_WA_ENV="/tmp/s682_probe_none/wa.env",
                      SURGERY_RING_AGENTS="/tmp/s682_probe_none/ring_agents.json")
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
        res.append(("manoj opens the suppliers' ledgers (the word supplier, the address unchanged)", r.status_code == 200 and b"Implant suppliers" in r.data))
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
        os.makedirs("/tmp/s682_probe_none", exist_ok=True)
        open("/tmp/s682_probe_none/wa.env", "w").write("CALL_API_SECRET=probe\n")
        open("/tmp/s682_probe_none/ring_agents.json", "w").write('{"agents": {"90000' '00009": {"user": "manoj", "name": "PROBE"}}}')
        r = c.post("/finance/surgery/new", data={"patient": "PROBE S681 CALL", "payer": "cash", "source": "Clinic", "mobile": "90000" "00009"},
                   headers={"X-Clinic-User": "manoj"})
        import sqlite3 as _sq
        _c = _sq.connect(dbp)
        pid = _c.execute("SELECT id FROM surg_case WHERE patient='PROBE S681 CALL'").fetchone()
        _c.close()
        r = c.post("/finance/surgery/case/%d/call" % (pid[0] if pid else 0), data={"n": "0"}, headers={"X-Clinic-User": "manoj"}) if pid else None
        _c = _sq.connect(dbp)
        kept = _c.execute("SELECT result, last4 FROM surg_call WHERE case_id=?", (pid[0] if pid else 0,)).fetchall()
        _c.close()
        res.append(("S370: the IVR call through the real app ends 'did not answer' at a dead port, kept with the last 4 digits only",
                    r is not None and r.status_code == 302 and "err=calldown" in r.headers.get("Location", "") and kept == [("error", "0009")]))
        # S681: the bill and the share through the real app (on the probe's own case)
        if pid:
            r = c.post("/finance/surgery/case/%d/bill" % pid[0], data={"b_visit": "1000", "b_misc": "340", "b_bed": "3100", "b_total": "9000"},
                       headers={"X-Clinic-User": "shavez"})
            r2 = get("/finance/surgery/case/%d" % pid[0], "shavez")
            res.append(("S681: Shavez saves a hospital bill through the real app; the case shows the hospital's way (4,440 -> 2,220)",
                        r.status_code == 302 and "msg=bill" in r.headers.get("Location", "") and b"\xe2\x82\xb9 2,220" in r2.data
                        and b"Your share" in r2.data))
            r = c.post("/finance/surgery/case/%d/assistant" % pid[0], data={"role": "assisting", "name": "PROBE DR", "pay": "700"},
                       headers={"X-Clinic-User": "shavez"})
            _c = _sq.connect(dbp)
            asr = _c.execute("SELECT pay_p FROM surg_assistant WHERE case_id=?", (pid[0],)).fetchall()
            _c.close()
            res.append(("S681: an assistant written by Shavez through the real app, his pay never taken", r.status_code == 302 and asr == [(None,)]))
        else:
            res.append(("S681: the probe's case was made", False))
        # S682: the implant bills desk through the real app
        r = get("/finance/surgery/implants", "shavez")
        res.append(("S682: Shavez opens the implant bills desk through the real app (the owner's step words; a cheque on its own)", r.status_code == 200
                    and b"<h1>Implant bills" in r.data and b"the dealer has not sent the bill" in r.data and b"/finance/surgery/implants/cheque" in r.data
                    and b"vendor" not in __import__("re").sub(rb"<[^>]+>", b" ", r.data).lower()))
        r = get("/finance/surgery/implants", "manoj")
        res.append(("S682: Dr Manoj opens the desk too", r.status_code == 200 and b"<h1>Implant bills" in r.data))
        r = get("/finance/surgery/implants", "bhawna")
        res.append(("S682: a login with no row on the unit is refused the desk", r.status_code in (302, 403)))
        if pid:
            r = c.post("/finance/surgery/case/%d/implant" % pid[0], data={"vendor_new": "PROBE S682 SUPPLIER", "item": "PROBE NAIL", "qty": "1", "bill": "5000", "bill_to": "doctor"},
                       headers={"X-Clinic-User": "shavez"})
            _c = _sq.connect(dbp)
            iid = _c.execute("SELECT id FROM surg_implant WHERE case_id=? AND item='PROBE NAIL'", (pid[0],)).fetchone()
            _c.close()
            r = c.post("/finance/surgery/implant/%d/bill" % (iid[0] if iid else 0), data={"bill_no": "PROBE/1", "bill_day": "2026-01-01", "amount": "5200", "bill_to": "doctor"},
                       headers={"X-Clinic-User": "shavez"}) if iid else None
            _c = _sq.connect(dbp)
            try:
                st = _c.execute("SELECT pay_status, bill_p, estimate_p FROM surg_implant WHERE id=?", (iid[0] if iid else 0,)).fetchone()
            except _sq.OperationalError:         # the old file: no such column -- a red, not a crash
                st = None
            _c.close()
            res.append(("S682: Shavez enters a supplier's bill on the desk through the real app: Bill raised, the estimate kept",
                        r is not None and r.status_code == 302 and "msg=ibill" in r.headers.get("Location", "") and st == ("raised", 520000, 500000)))
            r2 = get("/finance/surgery/case/%d" % pid[0], "shavez")
            res.append(("S682: section 6 on the case shows the bill and opens the desk", b"bill PROBE/1" in r2.data and ("/finance/surgery/implants?case=%d" % pid[0]).encode() in r2.data))
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
