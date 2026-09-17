#!/usr/bin/env python3
"""walk_s290.py -- the live-shape walk of the bank-SMS door and page: THE REAL finance_app.py (patched)
over a SCRATCH COPY of the real finance.db. The SMS texts are built at run time from the copy's own
latest MPR day, in ICICI's exact wording, with a made-up balance -- no real figure lives in this file.
Usage: FINANCE_DB=<copy> FINANCE_ALLOW_HEADER_AUTH=1 BANK_SMS_KEY_FILE=<tmp key> python3 walk_s290.py <app dir>
"""
import datetime as dt
import os
import sqlite3
import sys

N = [0]


def check(name, cond):
    N[0] += 1
    if not cond:
        print("FAIL %d: %s" % (N[0], name))
        sys.exit(1)


def sms(amount_p, credit_date, mid_tail, kind="EZY"):
    info = ("EZY*ICICIPOS_SET_10XX%s_" % mid_tail) if kind == "EZY" else ("FT-ICICIPOS SET 10XX%s 1" % mid_tail)
    return ("ICICI Bank Account XX000 credited:Rs. {:,.2f} on {}. Info {}. Available Balance is Rs. 1,00,000.00."
            .format(amount_p / 100.0, credit_date.strftime("%d-%b-%y"), info))


def main():
    sys.path.insert(0, sys.argv[1])
    os.chdir(sys.argv[1])
    dbp = os.environ["FINANCE_DB"]
    assert "walk" in dbp or dbp.startswith("/tmp"), "refusing a non-scratch database"
    key = open(os.environ["BANK_SMS_KEY_FILE"]).read().strip()
    import finance_app as fa
    check("bank_sms mounted", "bank_sms" in fa.app.blueprints)
    c = fa.app.test_client()
    con = sqlite3.connect(dbp)
    con.row_factory = sqlite3.Row
    mids = {r["code"]: str(r["merchant_id"])[-6:] for r in con.execute("SELECT code, merchant_id FROM business_unit WHERE merchant_id IS NOT NULL")}
    last = {}
    for unit in ("medical", "clinic"):
        r = con.execute("SELECT txn_date, SUM(amount_p) s FROM upi_txn WHERE unit=? GROUP BY txn_date ORDER BY txn_date DESC LIMIT 1", (unit,)).fetchone()
        check("the copy has an MPR day for " + unit, r is not None)
        last[unit] = (r["txn_date"], int(r["s"]))
    url = "/finance/api/bank-sms"
    md, mp = last["medical"]
    text_m = sms(mp, dt.date.fromisoformat(md) + dt.timedelta(days=1), mids["medical"])
    # ---- the door ---------------------------------------------------------------------------
    r = c.post(url, data={"text": text_m})
    check("no key -> 401", r.status_code == 401)
    r = c.post(url, data={"text": text_m}, headers={"X-Bank-Sms-Key": "wrong-key"})
    check("wrong key -> 401", r.status_code == 401)
    check("nothing stored without the key", con.execute("SELECT name FROM sqlite_master WHERE name='bank_sms_settlement'").fetchone() is None
          or con.execute("SELECT COUNT(*) FROM bank_sms_settlement").fetchone()[0] == 0)
    H = {"X-Bank-Sms-Key": key}
    r = c.post(url, data={"text": text_m, "sender": "AX-ICICIT"}, headers=H)
    j = r.get_json()
    check("settlement stored", r.status_code == 200 and j["stored"] and j["unit"] == "medical" and j["business_date"] == md)
    r = c.post(url, data={"text": text_m}, headers=H)
    check("the same SMS twice is one row", con.execute("SELECT COUNT(*), MAX(seen) FROM bank_sms_settlement").fetchone()[:] == (1, 2))
    for neg in ("Your OTP is 000000. Do not share.",
                "ICICI Bank Account XX000 debited:Rs. 500.00 on 17-Sep-26. Info UPI/x. Available Balance is Rs. 1,00,000.00.",
                "ICICI Bank Account XX000 credited:Rs. 500.00 on 17-Sep-26. Info UPI/ABC/a person. Available Balance is Rs. 1,00,000.00."):
        r = c.post(url, data={"text": neg}, headers=H)
        check("ignored and not stored: " + neg[:20], r.get_json().get("ignored") is True)
    check("only the settlement row exists", con.execute("SELECT COUNT(*) FROM bank_sms_settlement").fetchone()[0] == 1)
    r = c.post(url, data={"text": sms(1000, dt.date(2026, 9, 17), "999999")}, headers=H)
    check("unknown merchant ignored", r.get_json().get("ignored") is True)
    cd, cp = last["clinic"]
    r = c.post(url, data={"text": sms(cp + 100, dt.date.fromisoformat(cd) + dt.timedelta(days=1), mids["clinic"], "FT")}, headers=H)
    check("FT- variant stored for clinic", r.get_json().get("unit") == "clinic")
    check("no audit or log of the ignored texts", con.execute("SELECT COUNT(*) FROM bank_sms_settlement WHERE sms_text LIKE '%OTP%' OR sms_text LIKE '%debited%'").fetchone()[0] == 0)
    # ---- the page ---------------------------------------------------------------------------
    def get(user, path):
        return c.get(path, headers={"X-Clinic-User": user, "X-Clinic-Role": ""})
    os.environ["BANK_SMS_NOW"] = (dt.date.fromisoformat(max(md, cd)) + dt.timedelta(days=1)).isoformat() + "T08:00:00"
    r = get("manoj", "/finance/bank-sms")
    t = r.get_data(as_text=True)
    check("page 200 for the doctor", r.status_code == 200)
    check("medical day matches MPR", "matches MPR" in t)
    check("clinic day differs by 1", "differs by ₹ 1" in t)
    check("the key is on the doctor's page", key in t)
    check("setup steps shown", "ICICIPOS" in t and "[sms_message]" in t)
    r = get("bhawna", "/finance/bank-sms")
    check("Dr Bhawna (clinic checker) sees the page", r.status_code == 200)
    r = get("darpan", "/finance/bank-sms")
    check("darpan refused (no key leak)", r.status_code in (302, 403) and key not in r.get_data(as_text=True))
    r = get("alisha", "/finance/bank-sms")
    check("reception refused (no key leak)", r.status_code in (302, 403) and key not in r.get_data(as_text=True))
    os.environ["BANK_SMS_NOW"] = "2030-01-01T11:00:00"
    r = get("manoj", "/finance/bank-sms")
    check("past 10:00 with no SMS today -> the warning", "past 10:00" in r.get_data(as_text=True))
    import bank_sms
    check("sms_total_p for other screens", bank_sms.sms_total_p(con, "medical", md) == mp)
    check("no SMS reads None, never 0", bank_sms.sms_total_p(con, "lab", md) is None)
    for path, user in (("/finance/healthz", "manoj"), ("/finance/petty", "manoj"), ("/finance/clinic/day", "manoj")):
        check("still 200: " + path, get(user, path).status_code == 200)
    print("WALK OK — %d checks (bank-SMS door and page over a scratch copy of the real finance.db)" % N[0])


if __name__ == "__main__":
    main()
