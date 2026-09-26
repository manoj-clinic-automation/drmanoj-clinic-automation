#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s405.py -- kit S405_BANK_SMS_DOOR. THE REAL finance_app.py (a copy of /root/finance carrying the kit's three
files) over a SCRATCH COPY of finance.db, driven through Flask's test client: the phone's door with its own key file
(never the live key), header identity for the owner's routes (walk only). Every SMS text is crafted here and never
printed; the merchant id it needs is read from the scratch copy and never printed either. Its own rows are keyed W405*.
Nothing is posted to the live door.

  --app NEW  --old OLD   (copies of /root/finance: the kit's files / the box as it is)
  --db PATH              (the scratch finance.db; PATH.old is made for the old app)
"""
import argparse
import io
import json
import os
import re
import sqlite3
import subprocess
import sys

ap = argparse.ArgumentParser()
for k in ("--app", "--old", "--db"):
    ap.add_argument(k, required=True)
a = ap.parse_args()
assert "walk" in a.db or "scratch" in a.db or a.db.startswith("/tmp"), "refusing a non-scratch database"
n, fails = 0, []


def check(label, cond, got=None):
    global n
    n += 1
    print(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got)[:400] + "]") if got is not None else ""))
    if not cond:
        fails.append(label)


def copydb(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


copydb(a.db, a.db + ".old")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seed_s405  # noqa: E402
assert seed_s405.seed(a.db) == 0, "seed failed"
KEYF = os.path.join(os.path.dirname(os.path.abspath(a.db)), "w405_door.key")
with io.open(KEYF, "w", encoding="utf-8") as fh:
    fh.write("walk-key-W405-not-a-secret\n")
print("-- scratch seeded (neft.sms_tolerance_p); old-app scratch copy made; the walk's own door key written")

PROBE = r'''
import json, os, sys, sqlite3, datetime as dt, re
APP = os.environ["APPDIR"]; sys.path.insert(0, APP); os.chdir(APP)
os.environ["FINANCE_ALLOW_HEADER_AUTH"] = "1"
NEW = os.environ["MODE"] == "new"
KEY = open(os.environ["BANK_SMS_KEY_FILE"]).read().strip()
import finance_app as fa
c = fa.app.test_client()
H = lambda u: {"X-Clinic-User": u, "X-Clinic-Role": ""}
def G(u, p):
    r = c.get(p, headers=H(u)); j = r.get_json(silent=True)
    return [r.status_code, j if j is not None else r.get_data(as_text=True)]
def P(u, p, b=None):
    r = c.post(p, json=(b or {}), headers=H(u)); return [r.status_code, r.get_json(silent=True)]
def door(text, key=KEY, sender="WALK-SENDER", how="form"):
    if how == "json":
        r = c.post("/finance/api/bank-sms", json={"text": text, "sender": sender}, headers={"X-Bank-Sms-Key": key})
    else:
        r = c.post("/finance/api/bank-sms", data={"text": text, "sender": sender}, headers={"X-Bank-Sms-Key": key})
    return [r.status_code, r.get_json(silent=True)]
db = sqlite3.connect(os.environ["FINANCE_DB"], timeout=30); db.row_factory = sqlite3.Row
q = lambda s, *a: [dict(r) for r in db.execute(s, a).fetchall()]
one = lambda s, *a: db.execute(s, a).fetchone()[0]
has = lambda t: bool(db.execute("SELECT 1 FROM sqlite_master WHERE name=?", (t,)).fetchone())
now = lambda: dt.datetime.now().replace(microsecond=0).isoformat()
import bank_sms as bs
out = {"version": bs.APP_VERSION}
tail6 = str(one("SELECT merchant_id FROM business_unit WHERE code='medical'"))[-6:]
# the texts: built here, never printed (the merchant id is real; every other figure is crafted)
STRICT = "ICICI Bank Account XX123 credited:Rs. 1,234.00 on 25-Sep-26. Info EZY*ICICIPOS_SET_10XX%s_. Available Balance is Rs. 1,00,000.00." % tail6
V1 = "ICICI Bank Acct XX123 credited with Rs 2,345.00 on 25-Sep-26. Info: EZY*ICICIPOS SET 10XX%s. Avl Bal Rs 1,00,000.00" % tail6
V2 = "icici bank account xx123 credited: INR 3456 on 25/09/26.\nInfo ICICIPOS_SET_10XX%s_.\nAvailable balance is INR 99,000.50 - ICICI Bank" % tail6
V3 = "ICICI Bank Account XX123 credited:Rs. 4,567.89 on 25-09-2026. Info EZY*ICICIPOS_SET_10XX%s_." % tail6
SAMPLE = "ICICI Bank Account XX000 credited:Rs. 1,234.00 on 17-Sep-26. Info EZY*ICICIPOS_SET_10XX123456_. Available Balance is Rs. 1,00,000.00."
RANDOM = "Your OTP is 482913 for a payment of Rs 999.00 at SOME STORE. Do not share it. Ref W405R1."
Y_NEFT = "INR 4,05,000.00 debited from YES BANK A/c XX4405 on 24-SEP-2026 towards NEFT. UTR YESBN5W405A1B2C3. Avl Bal INR 12,345.67 -YES BANK"
Y_NEFT_OFF = "INR 3,03,010.00 debited from YES BANK A/c XX4405 on 24-Sep-26 by NEFT. Ref No YESBW405OFF1. Avl Bal INR 9,000.00"
Y_NEFT_TOL = "Rs 3,03,005 debited from Yes Bank A/c XX4405 on 24-Sep-26 via NEFT. Ref No YESBW405TOL1"
Y_NEFT_TOL2 = "Rs 3,03,005 debited from Yes Bank A/c XX4405 on 25-Sep-26 via NEFT. Ref No YESBW405TOL2"
Y_NEFT_OPEN = "INR 2,02,000.00 debited from YES BANK A/c XX4405 on 24-SEP-2026 towards NEFT. UTR YESBW405OPEN1"
Y_CASH = "Your YES BANK A/c XX4405 has been credited with INR 85,000.00 on 24-Sep-26 by CASH DEPOSIT at BAREILLY. Avl Bal INR 5,00,000.00"
Y_UPI = "Rs 1,200.00 debited from A/c XX4405 on 24-09-26 for UPI to shop@upi. UPI Ref W405UPI1. -YES BANK"
Y_OTP = "YES BANK: Your OTP for net banking login is 123456. Valid for 10 min. Do not share."
def cnt(t):
    return one("SELECT COUNT(*) FROM %s" % t) if has(t) else None
out["before"] = {"settle": cnt("bank_sms_settlement"), "ign": cnt("bank_sms_ignored"), "yes": cnt("bank_sms_yes"), "ev": cnt("purchase_neft_event")}
out["bad_key"] = door(STRICT, key="not-the-key")
out["after_bad_key"] = {"settle": cnt("bank_sms_settlement"), "ign": cnt("bank_sms_ignored")}
r = door(STRICT); out["strict"] = [r[0], (r[1] or {}).get("stored"), (r[1] or {}).get("unit"), (r[1] or {}).get("business_date"), (r[1] or {}).get("parse_grade")]
out["needs0"] = [l["text"] for l in (G("manoj", "/finance/sanjeevni/api/needs-you")[1] or {}).get("lines", [])]
out["page0"] = G("manoj", "/finance/bank-sms")
out["page0"] = [out["page0"][0], "Ignored (" in out["page0"][1], "Last Yes Bank SMS" in out["page0"][1], "Last SMS received: <b>none yet" in out["page0"][1]]
out["approvals_html"] = "neftEvent(" in G("manoj", "/finance/approvals")[1]
out["variants"] = []
for i, (V, how) in enumerate(((V1, "form"), (V2, "form"), (V3, "json"))):
    r = door(V, how=how); j = r[1] or {}
    out["variants"].append([r[0], j.get("stored"), j.get("parse_grade"), j.get("business_date"), j.get("amount")])
r = door(RANDOM); out["random"] = [r[0], (r[1] or {}).get("stored"), (r[1] or {}).get("ignored")]
r = door(Y_NEFT_OPEN); out["yes_neft_old"] = [r[0], (r[1] or {}).get("stored"), (r[1] or {}).get("ignored")]
out["tables"] = {t: has(t) for t in ("bank_sms_ignored", "bank_sms_yes", "purchase_neft_event")}
if not NEW:
    out["settle_rows"] = q("SELECT unit, credit_date, business_date, amount_p FROM bank_sms_settlement WHERE phone_sender='WALK-SENDER' ORDER BY id")
    print("JSON:" + json.dumps(out, default=str)); raise SystemExit
out["settle_rows"] = q("SELECT unit, credit_date, business_date, amount_p, parse_grade, acct_tail FROM bank_sms_settlement WHERE phone_sender='WALK-SENDER' ORDER BY id")
out["sample_parse"] = (bs.parse(SAMPLE) or {}).get("parse_grade")
r = door(SAMPLE); out["sample_door"] = [r[0], (r[1] or {}).get("stored"), (r[1] or {}).get("why")]
out["sample_ign"] = q("SELECT bank_guess, reason FROM bank_sms_ignored WHERE phone_sender='WALK-SENDER' AND reason LIKE 'unknown merchant%' ORDER BY id DESC LIMIT 1")
ri = q("SELECT bank_guess, reason, masked_text FROM bank_sms_ignored WHERE phone_sender='WALK-SENDER' AND bank_guess='UNKNOWN' ORDER BY id DESC LIMIT 1")
mt = ri[0]["masked_text"] if ri else ""
out["random_ign"] = [ri[0]["bank_guess"] if ri else None, ri[0]["reason"] if ri else None, bool(re.search(r"\d{5,}", mt)), "999.00" in mt, "482913" in mt, "Rs ####" in mt, mt[:60]]
# --- the crafted pay months: 2099-08 final (NEFT 4,05,000 + a cheque vendor 1,00,000) · 2099-07 final (NEFT 3,03,000) · 2099-09 open (NEFT 2,02,000)
def craft(month, vendor, amt_p, final, cheque_p=None):
    md = "w405sw" + month.replace("-", "")
    db.execute("INSERT OR REPLACE INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows, grand_amount_p) VALUES (?,?,?,?,?,?,?,?,?)",
               (md, "SUPPLIERWISE", "W405_" + month, month + "-01", month + "-28", month.replace("-", "") + "01-000000", now(), 1, amt_p))
    db.execute("INSERT OR IGNORE INTO purchase_vendor_contact (vendor_norm, vendor, phone, updated_at, acct_no, ifsc, bank_status) VALUES (?,?,?,?,?,?,?)",
               (vendor, vendor, None, now(), "W405ACCT" + month[-2:], "WALK0W405", "VERIFIED"))
    db.execute("INSERT OR IGNORE INTO purchase_bill (supplier_norm, supplier, bill_no, bill_date, month, amount_p, sw_md5, sw_amount_p) VALUES (?,?,?,?,?,?,?,?)",
               (vendor, vendor, "W405B" + month[-2:], month + "-10", month, amt_p, md, amt_p))
    if cheque_p:
        db.execute("INSERT OR IGNORE INTO purchase_bill (supplier_norm, supplier, bill_no, bill_date, month, amount_p, sw_md5, sw_amount_p) VALUES (?,?,?,?,?,?,?,?)",
                   ("W405 CHEQUE VENDOR", "W405 CHEQUE VENDOR", "W405C" + month[-2:], month + "-12", month, cheque_p, md, cheque_p))
    db.execute("INSERT OR REPLACE INTO purchase_month (month, status, finalised_by, finalised_at) VALUES (?,?,?,?)",
               (month, "final" if final else "provisional", "walk" if final else None, now() if final else None))
    db.commit()
craft("2099-08", "W405 VENDOR AUG", 40500000, True, cheque_p=10000000)
craft("2099-07", "W405 VENDOR JUL", 30300000, True)
craft("2099-09", "W405 VENDOR SEP", 20200000, False)
out["portion"] = [bs.neft_portion_p(db, "2099-08"), bs.neft_portion_p(db, "2099-07"), bs.neft_portion_p(db, "2099-09"), bs.finalised_months(db)[:3]]
aug = bs.neft_portion_p(db, "2026-08")
stmt = [r["withdrawal_p"] for r in q("SELECT withdrawal_p FROM bank_statement_line WHERE withdrawal_p>0 AND description LIKE '%NEFT%'")]
out["aug"] = [aug is not None and aug > 0, (aug in stmt) if aug else None, (min(abs(aug - w) for w in stmt) // 100) if (aug and stmt) else None]
# --- the Yes Bank shapes
r = door(Y_CASH); out["y_cash"] = [r[0], (r[1] or {}).get("stored"), (r[1] or {}).get("kind"), (r[1] or {}).get("sms_date"), (r[1] or {}).get("amount")]
r = door(Y_UPI); out["y_upi"] = [r[0], (r[1] or {}).get("stored"), (r[1] or {}).get("kind"), (r[1] or {}).get("sms_date")]
r = door(Y_OTP); out["y_otp"] = [r[0], (r[1] or {}).get("stored"), (r[1] or {}).get("ignored")]
out["y_otp_ign"] = q("SELECT bank_guess, reason FROM bank_sms_ignored WHERE phone_sender='WALK-SENDER' AND bank_guess='YESBANK' ORDER BY id DESC LIMIT 1")
ev0 = cnt("purchase_neft_event")
r = door(Y_NEFT); out["y_neft"] = [r[0], (r[1] or {}).get("stored"), (r[1] or {}).get("kind"), (r[1] or {}).get("sms_date"), (r[1] or {}).get("amount"), (r[1] or {}).get("matched_month")]
out["y_neft_row"] = q("SELECT kind, sms_date, amount_p, acct_tail, ref, balance_p, seen, masked_text FROM bank_sms_yes WHERE kind='neft_debit' AND amount_p=40500000")
yr = out["y_neft_row"][0] if out["y_neft_row"] else {}
out["y_neft_mask"] = [("XX4405" in (yr.get("masked_text") or "")), ("4,05,000" in (yr.get("masked_text") or "")), bool(re.search(r"\d{5,}", yr.get("masked_text") or ""))]
out["y_neft_row"] = [[x["kind"], x["sms_date"], x["amount_p"], x["acct_tail"], x["ref"], x["balance_p"], x["seen"]] for x in out["y_neft_row"]]
out["ev1"] = q("SELECT month, kind, source, amount_p, sms_date, utr, confirmed_by, created_by FROM purchase_neft_event WHERE month LIKE '2099-%' ORDER BY id")
out["ev1_n"] = cnt("purchase_neft_event") - ev0
r = door(Y_NEFT); out["y_neft_repeat"] = [r[0], (r[1] or {}).get("matched_month"), one("SELECT seen FROM bank_sms_yes WHERE kind='neft_debit' AND amount_p=40500000"), cnt("purchase_neft_event") - ev0]
r = door(Y_NEFT_OFF); out["y_off"] = [r[0], (r[1] or {}).get("kind"), (r[1] or {}).get("matched_month"), cnt("purchase_neft_event") - ev0]
db.execute("UPDATE setting SET value='1000' WHERE key='neft.sms_tolerance_p'"); db.commit()
r = door(Y_NEFT_TOL); out["y_tol"] = [r[0], (r[1] or {}).get("kind"), (r[1] or {}).get("matched_month"), cnt("purchase_neft_event") - ev0]
r = door(Y_NEFT_OPEN); out["y_open"] = [r[0], (r[1] or {}).get("kind"), (r[1] or {}).get("matched_month"), cnt("purchase_neft_event") - ev0]
out["ev2"] = q("SELECT id, month, kind, amount_p, confirmed_by FROM purchase_neft_event WHERE month LIKE '2099-%' ORDER BY id")
# --- Needs you and the two taps
nd = G("manoj", "/finance/sanjeevni/api/needs-you")
out["needs1"] = [[l["text"], l.get("neft_event"), l.get("target"), l.get("cls")] for l in (nd[1] or {}).get("lines", []) if l.get("neft_event")]
out["needs_gate"] = {u: G(u, "/finance/sanjeevni/api/needs-you")[0] for u in ("bhati", "darpan", "amir")}
e1 = next((e["id"] for e in out["ev2"] if e["month"] == "2099-08"), 0); e2 = next((e["id"] for e in out["ev2"] if e["month"] == "2099-07"), 0)
out["ok_darpan"] = P("darpan", "/finance/sanjeevni/api/neft-event/ok", {"id": e1})[0]
out["ok_bad"] = P("manoj", "/finance/sanjeevni/api/neft-event/ok", {"id": 0})[0]
out["ok_none"] = P("manoj", "/finance/sanjeevni/api/neft-event/ok", {"id": 99999999})[0]
out["ok"] = P("manoj", "/finance/sanjeevni/api/neft-event/ok", {"id": e1})
out["ok_again"] = (P("manoj", "/finance/sanjeevni/api/neft-event/ok", {"id": e1})[1] or {}).get("already")
out["reject"] = P("manoj", "/finance/sanjeevni/api/neft-event/reject", {"id": e2})
out["ev3"] = q("SELECT month, kind, confirmed_by, confirmed_at IS NOT NULL AS has_at, note FROM purchase_neft_event WHERE month LIKE '2099-%' ORDER BY id")
out["needs2"] = [l["text"] for l in (G("manoj", "/finance/sanjeevni/api/needs-you")[1] or {}).get("lines", []) if l.get("neft_event")]
# a genuine later SMS after 'Not this' may still match the month (the rejected event does not block it)
r = door(Y_NEFT_TOL2); out["y_tol2"] = [r[0], (r[1] or {}).get("matched_month"), cnt("purchase_neft_event") - ev0]
# --- the owner's page
pg = G("manoj", "/finance/bank-sms")
out["page1"] = [pg[0], "Ignored (" in pg[1], "Last Yes Bank SMS" in pg[1], "NEFT / IMPS / RTGS out" in pg[1], "cash deposit in" in pg[1], "Bank SMS 2 (Yes Bank)" in pg[1],
                "August 2099" in pg[1], "confirmed by manoj" in pg[1], "not this (rejected)" in pg[1], bool(re.search(r"\d{10,}", pg[1])), G("bhati", "/finance/bank-sms")[0], G("darpan", "/finance/bank-sms")[0]]
out["ign_all"] = q("SELECT bank_guess, reason FROM bank_sms_ignored WHERE phone_sender='WALK-SENDER' ORDER BY id")
out["after"] = {"settle": cnt("bank_sms_settlement"), "ign": cnt("bank_sms_ignored"), "yes": cnt("bank_sms_yes"), "ev": cnt("purchase_neft_event")}
print("JSON:" + json.dumps(out, default=str))
'''


def probe(appdir, mode, dbpath):
    env = dict(os.environ, APPDIR=appdir, MODE=mode, FINANCE_DB=dbpath, FINANCE_UI_DIR=os.path.join(appdir, "finance_ui"),
               FINANCE_ALLOW_HEADER_AUTH="1", BANK_SMS_KEY_FILE=KEYF)
    p = subprocess.run([sys.executable, "-B", "-c", PROBE], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=appdir)
    O = next((json.loads(x[5:]) for x in p.stdout.splitlines() if x.startswith("JSON:")), None)
    if not O:
        sys.exit("!! the %s app did not answer: %s\n%s" % (mode, p.stderr[-3000:], p.stdout[-800:]))
    return O


O = probe(a.old, "old", a.db + ".old")
N = probe(a.app, "new", a.db)

print("-- 1  the door: the key, the strict text, the tolerant rungs, nothing silent")
check("a wrong key is still 401 and writes nothing (settlement and ignored counts unchanged)", N["bad_key"][0] == 401 and N["after_bad_key"] == {"settle": N["before"]["settle"], "ign": N["before"]["ign"]}, (N["bad_key"], N["before"], N["after_bad_key"]))
check("the strict ICICI text stores as before: unit medical, business date = credit date - 1 (2026-09-24), parse_grade strict",
      N["strict"] == [200, True, "medical", "2026-09-24", "strict"], N["strict"])
check("three wording variants ('credited with Rs', lower case + INR + dd/mm/yy + newlines, dd-mm-yyyy with no balance; one posted as JSON) store via the tolerant rung",
      all(v[0] == 200 and v[1] is True and v[2] == "tolerant" and v[3] == "2026-09-24" for v in N["variants"]) and [v[4] for v in N["variants"]] == [2345, 3456, 4567], N["variants"])
check("the four stored rows carry their grade (strict, tolerant ×3) and the right paise", [r["parse_grade"] for r in N["settle_rows"]] == ["strict", "tolerant", "tolerant", "tolerant"]
      and [r["amount_p"] for r in N["settle_rows"]] == [123400, 234500, 345600, 456789], N["settle_rows"])
check("a random text (an OTP) answers 200/ignored and lands in the ignored table, bank UNKNOWN, MASKED: no 5+ digit run, the amount reads 'Rs ####', the OTP digits are gone",
      N["random"] == [200, False, True] and N["random_ign"][0] == "UNKNOWN" and N["random_ign"][2] is False and N["random_ign"][3] is False and N["random_ign"][4] is False and N["random_ign"][5] is True, N["random_ign"])
check("the sample ICICIPOS text in bank_sms.py's own docstring: parsed STRICT, then ignored as 'unknown merchant' (its merchant id is an illustration) -- and now the ignored table says so",
      N["sample_parse"] == "strict" and N["sample_door"] == [200, False, "unknown merchant"] and N["sample_ign"] and N["sample_ign"][0]["bank_guess"] == "ICICI", (N["sample_parse"], N["sample_door"], N["sample_ign"]))

print("-- 2  Yes Bank: the NEFT debit, the cash deposit, an unknown Yes Bank text")
check("a Yes Bank NEFT debit -> bank_sms_yes kind neft_debit with the amount (₹4,05,000), the SMS date (24-Sep-2026), the UTR, the account tail, the balance",
      N["y_neft"][:5] == [200, True, "neft_debit", "2026-09-24", 405000] and N["y_neft_row"] and N["y_neft_row"][0][:6] == ["neft_debit", "2026-09-24", 40500000, "4405", "YESBN5W405A1B2C3", 1234567], (N["y_neft"], N["y_neft_row"]))
check("its masked copy keeps the tail 'XX4405', hides the amount and every 5+ digit run", N["y_neft_mask"] == [True, False, False], N["y_neft_mask"])
check("a cash deposit credit -> cash_credit ₹85,000 on 24-Sep-2026; a UPI debit -> other_debit (dd-mm-yy read)", N["y_cash"] == [200, True, "cash_credit", "2026-09-24", 85000] and N["y_upi"] == [200, True, "other_debit", "2026-09-24"], (N["y_cash"], N["y_upi"]))
check("an unknown Yes Bank text (an OTP) -> 200/ignored, ignored table with bank_guess YESBANK and a reason", N["y_otp"] == [200, False, True] and N["y_otp_ign"] and N["y_otp_ign"][0]["bank_guess"] == "YESBANK" and "debit or credit" in N["y_otp_ign"][0]["reason"], (N["y_otp"], N["y_otp_ign"]))

print("-- 3  the NEFT provisional: a finalised month whose NEFT portion equals the debit -> ONE event; repeat, tolerance, an open month")
check("the crafted months read through purchase_app's own sheet: 2099-08 NEFT portion ₹4,05,000 (the cheque vendor excluded), 2099-07 ₹3,03,000, 2099-09 ₹2,02,000; 2099-08 and 2099-07 are final",
      N["portion"][:3] == [40500000, 30300000, 20200000] and N["portion"][3][:2] == ["2099-08", "2099-07"], N["portion"])
check("the real August 2026 sheet has a NEFT portion (%s); it %s a NEFT debit on the Yes Bank statement%s" % (N["aug"][0], "equals" if N["aug"][1] else "does not equal", "" if N["aug"][1] else (" (nearest differs by ₹%s)" % N["aug"][2])), N["aug"][0] is True, N["aug"])
check("the ₹4,05,000 debit writes exactly ONE purchase_neft_event: month 2099-08, provisional, source sms, the UTR, nobody has confirmed it",
      N["y_neft"][5] == "2099-08" and N["ev1_n"] == 1 and N["ev1"] == [{"month": "2099-08", "kind": "provisional", "source": "sms", "amount_p": 40500000, "sms_date": "2026-09-24", "utr": "YESBN5W405A1B2C3", "confirmed_by": None, "created_by": "sms"}], N["ev1"])
check("the same SMS again: seen 2, no second event", N["y_neft_repeat"] == [200, None, 2, 1], N["y_neft_repeat"])
check("₹3,03,010 against a month of ₹3,03,000 with tolerance 0: stored as neft_debit, NO event", N["y_off"] == [200, "neft_debit", None, 1], N["y_off"])
check("with neft.sms_tolerance_p = 1000 paise, ₹3,03,005 matches 2099-07 (a second event); ₹2,02,000 against the UNFINALISED 2099-09: no event",
      N["y_tol"] == [200, "neft_debit", "2099-07", 2] and N["y_open"] == [200, "neft_debit", None, 2], (N["y_tol"], N["y_open"]))

print("-- 4  Needs you: the line, the gate, OK / Not this")
t1 = [x for x in N["needs1"] if x[0].startswith("NEFT of ₹4,05,000 seen on 24-Sep-2026")]
check("the owner's Needs you carries 'NEFT of ₹4,05,000 seen on 24-Sep-2026 — matched to August 2099. OK?' (target bank) and the 2099-07 line; each names its event",
      len(N["needs1"]) == 2 and t1 and t1[0][0].endswith("matched to August 2099. OK?") and t1[0][2] == "bank" and all(x[1] for x in N["needs1"]), N["needs1"])
check("bhati, darpan and amir cannot read Needs you (302/403)", all(v in (302, 403) for v in N["needs_gate"].values()), N["needs_gate"])
check("darpan cannot tap OK (302/403); a missing id is 400; an unknown event 404", N["ok_darpan"] in (302, 403) and N["ok_bad"] == 400 and N["ok_none"] == 404, (N["ok_darpan"], N["ok_bad"], N["ok_none"]))
check("OK on the August-2099 event sets confirmed_by manoj (with a time); a second OK answers already", N["ok"][0] == 200 and N["ok"][1]["confirmed_by"] == "manoj" and N["ok_again"] is True
      and N["ev3"][0]["month"] == "2099-08" and N["ev3"][0]["confirmed_by"] == "manoj" and N["ev3"][0]["has_at"] == 1, (N["ok"], N["ev3"]))
check("Not this on the July-2099 event marks it rejected (who and when in the note); both lines leave Needs you", N["reject"][0] == 200 and N["reject"][1]["kind"] == "rejected"
      and N["ev3"][1]["kind"] == "rejected" and "manoj" in (N["ev3"][1]["note"] or "") and N["needs2"] == [], (N["reject"], N["ev3"], N["needs2"]))
check("a genuine later SMS for the rejected month still matches it (a rejection never blocks the next SMS)", N["y_tol2"] == [200, "2099-07", 3], N["y_tol2"])

print("-- 5  the owner's Bank SMS page")
p1 = N["page1"]
check("the page reads 200 for the owner with 'Last Yes Bank SMS', the Yes Bank table (NEFT out, cash deposit in), the events (August 2099 confirmed by manoj, July rejected), the Ignored card, the macro-2 line; no 10-digit number; bhati and darpan refused",
      p1[0] == 200 and all(p1[1:9]) and p1[9] is False and p1[10] in (302, 403) and p1[11] in (302, 403), p1)
check("the approvals page carries the OK / Not this renderer", N["approvals_html"] is True)
check("the door kept a reason for every miss: %d ignored rows, each with a bank guess" % len(N["ign_all"]), len(N["ign_all"]) == 3 and all(r["bank_guess"] in ("ICICI", "YESBANK", "UNKNOWN") and r["reason"] for r in N["ign_all"]), N["ign_all"])

print("-- 6  NEGATIVE CONTROLS on the box as it is (the unpatched files)")
check("NEGATIVE: the old door stores the strict text too (%s) but IGNORES all three tolerant variants" % O["strict"][1], O["strict"][1] is True and all(v[1] is False for v in O["variants"]), O["variants"])
check("NEGATIVE: the old door answers 200/ignored to the random text and to the Yes Bank NEFT and keeps NOTHING (no ignored table, no Yes Bank table, no event table)",
      O["random"][0] == 200 and O["yes_neft_old"][0] == 200 and not any(O["tables"].values()), (O["random"], O["yes_neft_old"], O["tables"]))
check("NEGATIVE: the old page has no 'Ignored' card and no 'Last Yes Bank SMS'; the old approvals page has no OK / Not this renderer; the old Needs you has no NEFT line",
      O["page0"][0] == 200 and O["page0"][1] is False and O["page0"][2] is False and O["approvals_html"] is False and not any(t.startswith("NEFT of") for t in O["needs0"]), (O["page0"], O["approvals_html"]))
check("NEGATIVE: the old APP_VERSION is S290's, the new is S405's", O["version"] == "S290-BANK-SMS-1.0" and N["version"] == "S405-BANK-SMS-2.0", (O["version"], N["version"]))

print(("WALK_S405 GREEN -- %d/%d" % (n, n)) if not fails else ("WALK_S405 RED -- %d of %d failed" % (len(fails), n)))
sys.exit(1 if fails else 0)
