#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sale_bill_door.py -- S240, Sanjeevni plan item 3 (Rung 1: every sale bill's own money row)

WHY THIS EXISTS
  `sale_bill.py` (S237) knows how to keep each bill's GROSS / DISCOUNT / TAX / DR-CR / NET / CASH --
  the discount that the old ingest drops (F-385). It was installed at S237 and has never run,
  because the sale exports live on the clinic PC and the VPS keeps none (the S186 rule).

  This is the door that closes that gap WITHOUT moving any export file:
    * manojz reads each archived SALE_BILLWISE export with the same parser and keeps only the
      money columns -- no patient name, no phone, no clinic ID leaves the PC;
    * it POSTs those rows to the purchase machine door that already exists
      (/finance/purchase/api/push, header X-Finance-Marg), as type "SALE_BILL";
    * this module re-checks every bill with sale_bill.py's own rules and stores it.

  S239 had proposed pushing the export FILES through /finance/api/marg-push. Reading that
  handler at S240 showed why not: it re-stages the item lines for the books and refuses a file
  it has seen, so a history push would either be refused or re-queue days already applied. The
  purchase door already carries parsed rows, never files, and the gate already opens it to the
  pharmacy's token -- so no gate change and no finance_app.py change is needed.

WHAT IT REFUSES
  * any bill field outside the money columns (so a name can never ride along);
  * a bill that does not add up within Marg's one-rupee rounding (sale_bill.MAX_ROUND_P);
  * a malformed date, md5 or stamp.
  A refusal refuses the WHOLE export: no half-stored file.

IDEMPOTENT
  The same export twice -> "duplicate", nothing written. Two exports of the same day -> the later
  export stamp wins, whatever order they arrive in (sale_bill.upsert / wins).
"""
import json
import re

import sale_bill as S

MD5_RE = re.compile(r"^[0-9a-f]{32}$")
STAMP_RE = re.compile(r"^\d{8}-\d{6}$")
ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MONEY_KEYS = ("bill_no", "gross_p", "disc_p", "tax_p", "drcr_p", "net_p", "cash_p",
              "noncash_p", "is_credit_note")
MAX_BILLS = 5000

LEDGER = """
CREATE TABLE IF NOT EXISTS sale_bill_push (
    md5          TEXT PRIMARY KEY,
    file         TEXT NOT NULL,
    export_stamp TEXT NOT NULL,
    received_at  TEXT NOT NULL,
    days_json    TEXT NOT NULL,
    bills        INTEGER NOT NULL,
    inserted     INTEGER NOT NULL,
    updated      INTEGER NOT NULL,
    kept_newer   INTEGER NOT NULL
);
"""


class Refused(Exception):
    pass


def _clean_bill(b):
    if not isinstance(b, dict):
        raise Refused("a bill is not an object")
    extra = sorted(set(b) - set(MONEY_KEYS))
    if extra:
        raise Refused("a bill carries fields this door does not accept: %s -- money columns only"
                      % ", ".join(extra))
    out = {}
    for k in MONEY_KEYS:
        if k not in b:
            continue
        v = b[k]
        if k == "bill_no":
            v = str(v or "").strip()
            if not v or len(v) > 40:
                raise Refused("a bill has no usable bill number")
        elif k == "is_credit_note":
            v = 1 if v else 0
        else:
            if isinstance(v, bool) or not isinstance(v, int):
                raise Refused("bill %s: %s must be whole paise" % (b.get("bill_no"), k))
        out[k] = v
    return out


def rows_from_body(b, unit, now_iso):
    """The request body -> sale_bill rows. Pure; raises Refused / S.SaleBillError."""
    md5 = str(b.get("md5") or "").lower()
    name = str(b.get("file") or "")[:200]
    stamp = str(b.get("export_stamp") or "")
    days = b.get("days")
    if not MD5_RE.match(md5):
        raise Refused("md5 must be 32 hex")
    if not name:
        raise Refused("file name missing")
    if not STAMP_RE.match(stamp):
        raise Refused("export_stamp must be YYYYMMDD-HHMMSS")
    if S.stamp_from_name(name) and S.stamp_from_name(name) != stamp:
        raise Refused("export_stamp does not match the stamp in the file name")
    if not isinstance(days, list) or not days:
        raise Refused("days must be a non-empty list")
    rows, n = [], 0
    for d in days:
        if not isinstance(d, dict) or not ISO_RE.match(str(d.get("date") or "")):
            raise Refused("every day needs an ISO date")
        bills = d.get("bills")
        if not isinstance(bills, list):
            raise Refused("day %s: bills must be a list" % d.get("date"))
        n += len(bills)
        if n > MAX_BILLS:
            raise Refused("more than %d bills in one export" % MAX_BILLS)
        for bill in bills:
            rows.append(S.row_from_bill(_clean_bill(bill), unit, d["date"], name, stamp, md5, now_iso))
    return md5, name, stamp, rows


def handle(con, b, unit, now_iso):
    """(json_dict, http_code). Called from purchase_app.api_push for type SALE_BILL."""
    try:
        md5, name, stamp, rows = rows_from_body(b, unit, now_iso)
    except (Refused, S.SaleBillError) as e:
        return {"ok": False, "error": "malformed", "reason": str(e)}, 400
    con.executescript(LEDGER)
    S.ensure_schema(con)
    if con.execute("SELECT 1 FROM sale_bill_push WHERE md5=?", (md5,)).fetchone():
        return {"ok": True, "stored": False, "reason": "duplicate"}, 200
    res = S.upsert(con, rows)
    days = sorted({r["business_date"] for r in rows})
    con.execute("INSERT INTO sale_bill_push (md5,file,export_stamp,received_at,days_json,bills,"
                "inserted,updated,kept_newer) VALUES (?,?,?,?,?,?,?,?,?)",
                (md5, name, stamp, now_iso, json.dumps(days), len(rows),
                 res["inserted"], res["updated"], res["kept_newer"]))
    con.commit()
    s = S.summarise(rows)
    return {"ok": True, "stored": True, "reason": "new", "bills": len(rows), "days": days,
            "discount_p": s["disc_p"], "net_p": s["net_p"], **res}, 200


# --------------------------------------------------------------------------- selftest
def selftest():
    import sqlite3
    fails = []

    def ck(name, cond):
        print(("  ok   " if cond else "  FAIL ") + name)
        if not cond:
            fails.append(name)

    def body(md5="a" * 32, stamp="20260911-134142", bills=None, date="2026-09-10"):
        return {"type": "SALE_BILL", "md5": md5,
                "file": "SALE_BILLWISE_DETAIL__%s__%s__%s.XLS" % (date, stamp, md5[:8]),
                "export_stamp": stamp,
                "days": [{"date": date, "bills": bills if bills is not None else [
                    {"bill_no": "A001", "gross_p": 317000, "disc_p": 87000, "tax_p": 0,
                     "drcr_p": 0, "net_p": 230000, "cash_p": 230000}]}]}
    con = sqlite3.connect(":memory:")
    r, c = handle(con, body(), "medical", "2026-09-11T15:00:00")
    ck("stores a new export", c == 200 and r["stored"] and r["inserted"] == 1)
    row = con.execute("SELECT gross_p, disc_p, net_p, round_p FROM sale_bill").fetchone()
    ck("A003495 shape kept to the paisa (3170 / 870 / 2300)", row == (317000, 87000, 230000, 0))
    r, c = handle(con, body(), "medical", "2026-09-11T15:01:00")
    ck("same export twice -> duplicate, nothing written", r["reason"] == "duplicate"
       and con.execute("SELECT COUNT(*) FROM sale_bill").fetchone()[0] == 1)
    newer = body(md5="b" * 32, stamp="20260911-200000", bills=[
        {"bill_no": "A001", "gross_p": 317000, "disc_p": 90000, "tax_p": 0, "drcr_p": 0,
         "net_p": 227000, "cash_p": 227000}])
    r, c = handle(con, newer, "medical", "2026-09-11T15:02:00")
    ck("a later export of the same day wins", r["updated"] == 1 and
       con.execute("SELECT disc_p FROM sale_bill").fetchone()[0] == 90000)
    older = body(md5="c" * 32, stamp="20260911-100000")
    r, c = handle(con, older, "medical", "2026-09-11T15:03:00")
    ck("an earlier export never overwrites a later one", r["kept_newer"] == 1 and
       con.execute("SELECT disc_p FROM sale_bill").fetchone()[0] == 90000)
    r, c = handle(con, body(md5="d" * 32, bills=[{"bill_no": "A9", "gross_p": 100, "disc_p": 0,
                  "net_p": 100, "cash_p": 100, "party": "SOMEONE"}]), "medical", "x")
    ck("a name field is refused (money columns only)", c == 400 and "party" in r["reason"])
    r, c = handle(con, body(md5="e" * 32, bills=[{"bill_no": "A9", "gross_p": 100000, "disc_p": 0,
                  "tax_p": 0, "drcr_p": 0, "net_p": 50000, "cash_p": 0}]), "medical", "x")
    ck("a bill that does not add up is refused whole", c == 400 and
       con.execute("SELECT COUNT(*) FROM sale_bill_push WHERE md5=?", ("e" * 32,)).fetchone()[0] == 0)
    r, c = handle(con, body(md5="f" * 32, bills=[{"bill_no": "A9", "gross_p": 1.5, "disc_p": 0,
                  "net_p": 1, "cash_p": 1}]), "medical", "x")
    ck("non-integer paise refused", c == 400)
    bad = body(md5="1" * 32); bad["export_stamp"] = "20260101-000000"
    r, c = handle(con, bad, "medical", "x")
    ck("stamp must match the file name", c == 400)
    r, c = handle(con, {"md5": "zz"}, "medical", "x")
    ck("malformed body refused", c == 400)
    cn = body(md5="2" * 32, stamp="20260912-090000", date="2026-09-11", bills=[
        {"bill_no": "CN1", "gross_p": -50000, "disc_p": 0, "tax_p": 0, "drcr_p": 0,
         "net_p": -50000, "cash_p": -50000, "is_credit_note": True}])
    r, c = handle(con, cn, "medical", "x")
    ck("a credit note is stored negative and flagged", c == 200 and
       con.execute("SELECT net_p, is_credit_note FROM sale_bill WHERE bill_no='CN1'").fetchone() == (-50000, 1))
    print("sale_bill_door selftest: %d checks, %d failures" % (11, len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    print(__doc__)
