#!/usr/bin/env python3
"""walk_s295.py -- the live-shape walk of S295 part B: THE REAL finance_app.py over a SCRATCH COPY of the
real finance.db, with the patched clinic_money.py, darpan_app.py and darpan_card.html beside it.
The bank's MPR state for one day is forced to "waiting" (the case this part exists for) by replacing
bank_mpr_status.mpr_state in memory only; the SMS is posted through the real S290 door with a made-up
balance. Nothing live is touched.
Usage: FINANCE_DB=<copy> FINANCE_ALLOW_HEADER_AUTH=1 BANK_SMS_KEY_FILE=<tmp key> python3 walk_s295.py <app dir>
"""
import datetime as dt
import os
import re
import sqlite3
import sys

N = [0]


def check(name, cond):
    N[0] += 1
    if not cond:
        print("FAIL %d: %s" % (N[0], name))
        sys.exit(1)


def main():
    sys.path.insert(0, sys.argv[1])
    os.chdir(sys.argv[1])
    dbp = os.environ["FINANCE_DB"]
    assert "walk" in dbp or dbp.startswith("/tmp"), "refusing a non-scratch database"
    key = open(os.environ["BANK_SMS_KEY_FILE"]).read().strip()
    import finance_app as fa
    import bank_mpr_status
    import clinic_money
    check("bank_sms mounted", "bank_sms" in fa.app.blueprints)
    c = fa.app.test_client()
    con = sqlite3.connect(dbp)
    con.row_factory = sqlite3.Row
    mids = {r["code"]: str(r["merchant_id"])[-6:] for r in con.execute("SELECT code, merchant_id FROM business_unit WHERE merchant_id IS NOT NULL")}
    d = con.execute("SELECT MAX(business_date) d FROM clinic_register_day").fetchone()["d"]
    md = con.execute("SELECT MAX(business_date) d FROM day_entry WHERE unit='medical'").fetchone()["d"]
    check("the copy has a register day and a pharmacy day", bool(d) and bool(md))
    H = {"X-Clinic-User": "manoj", "X-Clinic-Role": ""}
    real_state = bank_mpr_status.mpr_state

    def waiting(con_, day, unit="clinic"):
        return {"ok": True, "state": "waiting", "date": day, "unit": unit}
    # ---- the morning match, MPR not arrived, no SMS yet -> the old words
    bank_mpr_status.mpr_state = waiting
    con.execute("DELETE FROM upi_txn WHERE unit='clinic' AND txn_date=?", (d,))
    con.commit()
    t = c.get("/finance/clinic/match/" + d, headers=H).get_data(as_text=True)
    check("match page 200 and waiting words without an SMS", "has not arrived yet" in t and "Bank SMS this morning" not in t)
    # ---- the SMS arrives through the real door
    credit = (dt.date.fromisoformat(d) + dt.timedelta(days=1)).strftime("%d-%b-%y")
    txt = "ICICI Bank Account XX000 credited:Rs. 4,321.00 on %s. Info EZY*ICICIPOS_SET_10XX%s_. Available Balance is Rs. 1,00,000.00." % (credit, mids["clinic"])
    r = c.post("/finance/api/bank-sms", data={"text": txt}, headers={"X-Bank-Sms-Key": key})
    check("SMS stored for the clinic day", (r.get_json() or {}).get("business_date") == d)
    t = c.get("/finance/clinic/match/" + d, headers=H).get_data(as_text=True)
    check("match page shows the SMS figure while the MPR waits", "Bank SMS this morning: ₹4,321 credited" in t)
    check("and still says the match waits for the MPR", "has not arrived yet, so the match waits for it" in t)
    # ---- once the MPR is known, the SMS words go away
    bank_mpr_status.mpr_state = real_state
    t = c.get("/finance/clinic/match/" + d, headers=H).get_data(as_text=True)
    check("with the MPR state back, no SMS words", "Bank SMS this morning" not in t)
    # ---- Darpan's card
    md_credit = (dt.date.fromisoformat(md) + dt.timedelta(days=1)).strftime("%d-%b-%y")
    txt2 = "ICICI Bank Account XX000 credited:Rs. 1,234.00 on %s. Info FT-ICICIPOS SET 10XX%s 1. Available Balance is Rs. 1,00,000.00." % (md_credit, mids["medical"])
    c.post("/finance/api/bank-sms", data={"text": txt2}, headers={"X-Bank-Sms-Key": key})
    D = {"X-Clinic-User": "darpan", "X-Clinic-Role": ""}
    j = c.get("/finance/darpan/api/card?date=" + md, headers=D).get_json()
    check("card API carries sms_p", j and j["bank"].get("sms_p") == 123400)
    j2 = c.get("/finance/darpan/api/card?date=2020-01-01", headers=D).get_json()
    check("a day with no SMS carries None, never 0", j2 and j2["bank"].get("sms_p") is None)
    page = c.get("/finance/darpan", headers=D).get_data(as_text=True)
    check("the card page carries the 5a line", "5a · Bank ka SMS" in page and "j.bank.sms_p" in page)
    check("the old section 5 is still there", "5 · Bank (MPR)" in page)
    # ---- nothing else moved
    for path, user in (("/finance/healthz", "manoj"), ("/finance/clinic/money", "manoj"), ("/finance/physio", "manoj"),
                       ("/finance/petty", "manoj"), ("/finance/bank-sms", "manoj")):
        check("still 200: " + path, c.get(path, headers={"X-Clinic-User": user, "X-Clinic-Role": ""}).status_code == 200)
    print("WALK OK — %d checks (SMS figure on the morning match and Darpan's card, over a scratch copy)" % N[0])


if __name__ == "__main__":
    main()
