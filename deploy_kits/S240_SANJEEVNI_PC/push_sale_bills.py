#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
push_sale_bills.py -- S240 (Sanjeevni plan item 3). Runs on MANOJZ.

Every archived SALE_BILLWISE export (VERIFIED in MargArchive\\index.csv) is read with the same
parser the router uses, and each bill's MONEY row -- gross, discount, tax, dr/cr, net, cash,
credit-note flag -- is sent to the VPS through the purchase machine door as type SALE_BILL.

    python push_sale_bills.py              send what the server has not had yet
    python push_sale_bills.py --dry-run    read and check everything, send nothing
    python push_sale_bills.py --verify     prove the door answers (sends an empty body)
    python push_sale_bills.py --selftest   offline checks

WHAT NEVER LEAVES THIS PC
    The export file itself, and every name, phone and clinic ID in it. Only the money columns
    are sent; the server refuses any other field.

IDEMPOTENT
    The ledger D:\\Downloads\\margsync\\_analysis\\sale_bill_push_state.json remembers what was
    stored; the server is idempotent on md5 anyway. Two exports of one day: the later wins, on
    the server, whatever order they arrive in.

THE TOKEN
    The same pharmacy token push_purchases.py uses (X-Finance-Marg), read the same way: the
    medical share first, the local cache second. Never printed, never logged.
"""
import argparse
import csv
import datetime as dt
import io
import json
import os
import re
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PULL_DIR = r"D:\Downloads\margsync\MargPull"          # the router's own parser and its xlrd
sys.path.insert(0, HERE)
if PULL_DIR not in sys.path:
    sys.path.insert(1, PULL_DIR)

import sale_bill as S                                  # noqa: E402  the S237 rules, pure half only

DEF_ARCHIVE = r"D:\Downloads\margsync\MargArchive"
DEF_ANALYSIS = r"D:\Downloads\margsync\_analysis"
DEF_BASE = "https://followup.dr-manoj.in/finance/purchase/api"
DEF_TOKEN_UNC = r"\\100.119.151.40\DDrive\SendToClinic\token.txt"
DEF_TOKEN_CACHE = r"D:\Downloads\margsync\SendToClinic\token.txt"
LEDGER_NAME = "sale_bill_push_state.json"
LASTRUN_NAME = "push_sale_bills_lastrun.txt"
MONEY_KEYS = ("bill_no", "gross_p", "disc_p", "tax_p", "drcr_p", "net_p", "cash_p",
              "noncash_p", "is_credit_note")
STAMP_RE = re.compile(r"__(\d{8}-\d{6})__")


def now_ist():
    return dt.datetime.utcnow() + dt.timedelta(hours=5, minutes=30)


def read_token(unc=None, cache=None):
    for p in (unc or DEF_TOKEN_UNC, cache or DEF_TOKEN_CACHE):
        try:
            with open(p, "r", encoding="utf-8") as fh:
                t = (fh.read() or "").strip()
            if t:
                return t
        except OSError:
            continue
    return None


def _post(url, body, tok, timeout=90):
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json", "X-Finance-Marg": tok})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8", "replace")


def exports(archive):
    """VERIFIED SALE_BILLWISE rows of index.csv whose file exists, oldest stamp first."""
    out, seen = [], set()
    with io.open(os.path.join(archive, "index.csv"), "r", encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            if r.get("type") != "SALE_BILLWISE" or r.get("verdict") != "VERIFIED":
                continue
            md5 = (r.get("md5") or "").strip().lower()
            p = r.get("archived_path") or ""
            if not md5 or md5 in seen or not os.path.exists(p):
                continue
            seen.add(md5)
            stamp = (STAMP_RE.search(os.path.basename(p)) or [None, r.get("export_stamp") or ""])[1]
            out.append({"md5": md5, "path": p, "stamp": stamp})
    return sorted(out, key=lambda x: (x["stamp"], x["path"]))


def body_for(rep, name, md5, stamp):
    """The parsed report -> the request body, money columns only. Every bill is checked with
    sale_bill's own rule first, so a misread is caught here and never sent."""
    days = []
    for d in rep.get("days") or []:
        bills = []
        for b in d.get("bills") or []:
            m = {k: b[k] for k in MONEY_KEYS if k in b}
            m["is_credit_note"] = bool(m.get("is_credit_note"))
            S.row_from_bill(m, "medical", d.get("date"), name, stamp, md5, "check")
            bills.append(m)
        days.append({"date": d.get("date"), "bills": bills})
    return {"type": "SALE_BILL", "md5": md5, "file": name, "export_stamp": stamp, "days": days}


def load_ledger(path):
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def save_ledger(path, led):
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8") as fh:
        json.dump(led, fh, indent=1, sort_keys=True)
    os.replace(tmp, path)


def run(a):
    import marg_report                                  # the router's parser (MargPull)
    os.makedirs(a.analysis, exist_ok=True)
    lpath = os.path.join(a.analysis, LEDGER_NAME)
    led = load_ledger(lpath)
    todo = [e for e in exports(a.archive)
            if a.retry_refused or e["md5"] not in led]
    tok = None if a.dry_run else read_token()
    if not a.dry_run and not tok:
        print("REFUSING: no token (share or cache) -- nothing sent")
        return 2
    sent = dup = refused = unread = 0
    bills = disc = 0
    for e in todo:
        name = os.path.basename(e["path"])
        try:
            rep = marg_report.read_report(e["path"])
            body = body_for(rep, name, e["md5"], e["stamp"])
        except Exception as ex:                          # noqa: BLE001  parser or rule refusal
            unread += 1
            print("  NOT READ   %s -- %s" % (name[:70], str(ex)[:160]))
            if not a.dry_run:
                led[e["md5"]] = {"at": now_ist().strftime("%Y-%m-%d %H:%M"), "result": "not_read",
                                 "file": name, "why": str(ex)[:200]}
            continue
        nb = sum(len(d["bills"]) for d in body["days"])
        nd = sum(b["disc_p"] for d in body["days"] for b in d["bills"])
        if a.dry_run:
            print("  would send %-62s %3d bills  discount Rs %.2f" % (name[:62], nb, nd / 100.0))
            bills += nb; disc += nd; sent += 1
            continue
        try:
            st, txt = _post(a.base + "/push", body, tok)
            res = json.loads(txt or "{}")
        except urllib.error.HTTPError as ex:
            code = ex.code
            if code in (401, 403, 404):
                print("REFUSING: the server answered %d -- the SALE_BILL door is not open. Stopped." % code)
                save_ledger(lpath, led)
                return 3
            try:
                why = json.loads(ex.read().decode("utf-8", "replace")).get("reason")
            except Exception:                            # noqa: BLE001
                why = "HTTP %d" % code
            if "type must be one of" in str(why or ""):
                # the server has the purchase door but not the SALE_BILL branch yet (kit not
                # installed): stop, record nothing, try again next run
                print("WAITING: the server does not know SALE_BILL yet (S240 VPS kit not installed). Stopped.")
                save_ledger(lpath, led)
                return 3
            refused += 1
            print("  REFUSED    %s -- %s" % (name[:70], why))
            led[e["md5"]] = {"at": now_ist().strftime("%Y-%m-%d %H:%M"), "result": "refused",
                             "file": name, "why": str(why)[:200]}
            continue
        except Exception as ex:                          # noqa: BLE001  network -- try next run
            print("  NETWORK    %s -- %s; will retry next run" % (name[:60], ex.__class__.__name__))
            save_ledger(lpath, led)
            return 4
        if res.get("stored"):
            sent += 1; bills += nb; disc += nd
            print("  stored     %-62s %3d bills  discount Rs %.2f" % (name[:62], nb, nd / 100.0))
        else:
            dup += 1
        led[e["md5"]] = {"at": now_ist().strftime("%Y-%m-%d %H:%M"),
                         "result": "stored" if res.get("stored") else res.get("reason", "?"),
                         "file": name, "bills": nb}
    if not a.dry_run:
        save_ledger(lpath, led)
    line = ("%s  %s: %d new export(s) %s, %d already there, %d refused, %d unreadable; "
            "%d bills, discount Rs %.2f"
            % (now_ist().strftime("%Y-%m-%d %H:%M"), "DRY RUN" if a.dry_run else "push",
               sent, "readable" if a.dry_run else "stored", dup, refused, unread, bills, disc / 100.0))
    print(line)
    if not a.dry_run:
        with io.open(os.path.join(a.analysis, LASTRUN_NAME), "w", encoding="utf-8") as fh:
            fh.write(line + "\n")
    return 0


def verify(base):
    tok = read_token()
    if not tok:
        print("no token available -- cannot verify")
        return 2
    try:
        _post(base + "/push", {"type": "SALE_BILL"}, tok, timeout=30)
        print("UNEXPECTED: the door accepted an empty body")
        return 1
    except urllib.error.HTTPError as ex:
        try:
            why = json.loads(ex.read().decode("utf-8", "replace")).get("reason") or ""
        except Exception:                                # noqa: BLE001
            why = ""
        if ex.code == 400 and "type must be one of" not in why:
            print("DOOR OPEN: the server read the SALE_BILL type and refused the empty body (400). GREEN.")
            return 0
        if ex.code == 400:
            print("DOOR NOT OPEN YET: the server does not know SALE_BILL (the VPS kit is not installed)")
            return 1
        print("DOOR NOT OPEN: HTTP %d" % ex.code)
        return 1
    except Exception as ex:                              # noqa: BLE001
        print("could not reach the server (%s)" % ex.__class__.__name__)
        return 2


def selftest():
    fails = []

    def ck(n, c):
        print(("  ok   " if c else "  FAIL ") + n)
        if not c:
            fails.append(n)
    rep = {"days": [{"date": "2026-09-10", "bills": [
        {"bill_no": "A1", "gross_p": 317000, "disc_p": 87000, "tax_p": 0, "drcr_p": 0, "net_p": 230000,
         "cash_p": 230000, "noncash_p": 0, "is_credit_note": False, "patient_name": "X", "phone": "0",
         "clinic_id": "C", "mode": "CASH", "confidence": "high", "bill_date": "10-09-2026"}]}]}
    b = body_for(rep, "SALE_BILLWISE_DETAIL__2026-09-10__20260911-134142__42798b9c.XLS", "a" * 32,
                 "20260911-134142")
    keys = set(b["days"][0]["bills"][0])
    ck("only money columns leave the PC", keys <= set(MONEY_KEYS) and "patient_name" not in keys
       and "phone" not in keys and "clinic_id" not in keys)
    ck("the fixture keeps 3170 / 870 / 2300", b["days"][0]["bills"][0]["net_p"] == 230000)
    bad = {"days": [{"date": "2026-09-10", "bills": [{"bill_no": "A2", "gross_p": 100000, "disc_p": 0,
           "tax_p": 0, "drcr_p": 0, "net_p": 1000, "cash_p": 1000}]}]}
    try:
        body_for(bad, "x.XLS", "b" * 32, "20260911-000000")
        ck("a bill that does not add up is caught before sending", False)
    except S.SaleBillError:
        ck("a bill that does not add up is caught before sending", True)
    print("push_sale_bills selftest: %d checks, %d failures" % (3, len(fails)))
    return 1 if fails else 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", default=DEF_ARCHIVE)
    ap.add_argument("--analysis", default=DEF_ANALYSIS)
    ap.add_argument("--base", default=DEF_BASE)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--retry-refused", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    if a.selftest:
        return selftest()
    if a.verify:
        return verify(a.base)
    return run(a)


if __name__ == "__main__":
    sys.exit(main())
