#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s407.py -- kit S407_NEFT_MESSAGES. THE REAL finance_app.py (a copy of /root/finance carrying the kit's files) over a
SCRATCH COPY of finance.db, driven through Flask's test client with header identity (walk only). Its own months (2099-05 /
07 / 08 / 09), vendors, numbers, accounts and IFSCs are crafted here -- the digits are built at run time and NEVER printed;
every response to bhati / darpan / amir / a stranger, every page and every audit row is checked for them (the number-leak
gate). It never opens wa.me and never posts to a real phone: the token door is driven from here with the scratch token.

  --app NEW  --old OLD   (copies of /root/finance: the kit's files / the box as it is)
  --db PATH              (the scratch finance.db; PATH.old is made for the old app)
"""
import argparse
import json
import os
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
sys.path.insert(0, a.app)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["FINANCE_DIR"] = a.app
import seed_s407  # noqa: E402
assert seed_s407.seed(a.db) == 0, "seed failed"
print("-- scratch seeded (senders, tolerance, a scratch phone token); old-app scratch copy made")

PROBE = r'''
import json, os, sys, sqlite3, datetime as dt, re, time
from urllib.parse import quote
APP = os.environ["APPDIR"]; sys.path.insert(0, APP); os.chdir(APP)
os.environ["FINANCE_ALLOW_HEADER_AUTH"] = "1"
NEW = os.environ["MODE"] == "new"
import finance_app as fa
c = fa.app.test_client()
H = lambda u: {"X-Clinic-User": u, "X-Clinic-Role": ""}
def G(u, p, **kw):
    r = c.get(p, headers=dict(H(u), **kw.get("h", {}))); j = r.get_json(silent=True)
    return [r.status_code, j if j is not None else r.get_data(as_text=True)]
def P(u, p, b=None, **kw):
    r = c.post(p, json=(b or {}), headers=dict(H(u), **kw.get("h", {}))); return [r.status_code, r.get_json(silent=True)]
db = sqlite3.connect(os.environ["FINANCE_DB"], timeout=30); db.row_factory = sqlite3.Row
q = lambda s, *a: [dict(r) for r in db.execute(s, a).fetchall()]
one = lambda s, *a: db.execute(s, a).fetchone()[0]
has = lambda t: bool(db.execute("SELECT 1 FROM sqlite_master WHERE name=?", (t,)).fetchone())
now = lambda: dt.datetime.now().replace(microsecond=0).isoformat()
import purchase_app as pa
out = {"mounted": "supplier_msg" in fa.app.blueprints}
PH = "9" + "1" * 9;  PH2 = "9" + "2" * 9;  PH3 = "9" + "3" * 9;  ACCT = "5" * 12;  ACCT2 = "6" * 12;  IFSC = "WALK0000407"
LEAK = [PH, PH2, PH3, ACCT, ACCT2, IFSC, "91" + PH, "91" + PH2, "91" + PH3]
LEAK_PH = [PH, PH2, PH3, "91" + PH, "91" + PH2, "91" + PH3]
def leak(text):
    t = str(text or "")
    return [x for x in LEAK if x in t]
def leak_ph(text):
    # the pay page has carried the bank advice annexure (every NEFT vendor's account and IFSC) since S265, by the owner's
    # design -- so a PAGE is gated on phone numbers; every API answer, audit row and the other pages on everything
    t = str(text or "")
    return [x for x in LEAK_PH if x in t]
def craft(month, vendor, amt_p, final, phone=None, acct=None, ifsc=None):
    md = "w407sw" + month.replace("-", "") + vendor[-1]
    db.execute("INSERT OR REPLACE INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows, grand_amount_p) VALUES (?,?,?,?,?,?,?,?,?)",
               (md, "SUPPLIERWISE", "W407_" + month, month + "-01", month + "-28", month.replace("-", "") + "01-000000", now(), 1, amt_p))
    db.execute("INSERT OR IGNORE INTO purchase_vendor_contact (vendor_norm, vendor, phone, updated_at, acct_no, ifsc, bank_status, acct_name) VALUES (?,?,?,?,?,?,?,?)",
               (vendor, vendor, phone, now(), acct, ifsc, "VERIFIED" if acct else "", vendor))
    db.execute("INSERT OR IGNORE INTO purchase_bill (supplier_norm, supplier, bill_no, bill_date, month, amount_p, sw_md5, sw_amount_p) VALUES (?,?,?,?,?,?,?,?)",
               (vendor, vendor, "W407B" + month[-2:] + vendor[-1], month + "-10", month, amt_p, md, amt_p))
    db.execute("INSERT OR REPLACE INTO purchase_month (month, status, finalised_by, finalised_at) VALUES (?,?,?,?)",
               (month, "final" if final else "provisional", "walk" if final else None, now() if final else None))
    db.commit()
craft("2099-08", "W407 VENDOR A", 10100000, True, phone=PH, acct=ACCT, ifsc=IFSC)
craft("2099-08", "W407 VENDOR B", 5050000, True, phone=None, acct=ACCT2, ifsc=IFSC)
craft("2099-08", "W407 CHEQUE VENDOR C", 30300000, True, phone=PH2)
craft("2099-07", "W407 VENDOR D", 20200000, True, phone=PH3, acct=ACCT, ifsc=IFSC)
craft("2099-09", "W407 VENDOR E", 1000000, False, phone=PH, acct=ACCT, ifsc=IFSC)
craft("2099-05", "W407 VENDOR F", 4040000, True, phone=PH, acct=ACCT, ifsc=IFSC)
out["pay_page_old"] = G("manoj", "/finance/purchase/page/pay/2099-08")
out["pay_page_old"] = [out["pay_page_old"][0], "neftcard_s407" in out["pay_page_old"][1], leak_ph(out["pay_page_old"][1]), bool(leak(out["pay_page_old"][1]))]
out["state_old"] = G("manoj", "/finance/purchase/api/neft-state?month=2099-08")[0]
out["amir_old"] = G("amir", "/finance/amir/step/1"); out["amir_old"] = [out["amir_old"][0], "NEFT" in out["amir_old"][1], leak(out["amir_old"][1])]
out["needs_old"] = [l["text"] for l in (G("manoj", "/finance/sanjeevni/api/needs-you")[1] or {}).get("lines", [])]
out["setup_old"] = G("shavez", "/finance/purchase/page/phone-setup")[0]
out["tables_old"] = has("supplier_msg")
if not NEW:
    print("JSON:" + json.dumps(out, default=str)); raise SystemExit
import supplier_msg as sm
TOK = one("SELECT value FROM setting WHERE key='supplier_msg.phone_token'")
T = {"X-Phone-Token": TOK}
S = lambda m, u="manoj": G(u, "/finance/purchase/api/neft-state?month=" + m)
st0 = S("2099-08")[1]
out["state0"] = [st0["status"], st0["final"], st0["neft_p"], st0["vendors"], st0["event"], st0["me"]]
out["done_open"] = P("manoj", "/finance/purchase/api/neft-done", {"month": "2099-09", "date": "2026-09-24"})
out["done_darpan"] = P("darpan", "/finance/purchase/api/neft-done", {"month": "2099-08", "date": "2026-09-24"})[0]
out["done_bad"] = P("manoj", "/finance/purchase/api/neft-done", {"month": "2099-8"})[0]
out["done_future"] = P("manoj", "/finance/purchase/api/neft-done", {"month": "2099-08", "date": "2099-08-01"})[0]
out["done"] = P("manoj", "/finance/purchase/api/neft-done", {"month": "2099-08", "date": "2026-09-24", "utr": "W407UTR1"})
out["done_again"] = P("manoj", "/finance/purchase/api/neft-done", {"month": "2099-08", "date": "2026-09-24"})[1]
out["event"] = q("SELECT month, kind, source, amount_p, sms_date, utr, created_by, confirmed_by, bank_line_id FROM purchase_neft_event WHERE month='2099-08'")
msgs = q("SELECT id, vendor, kind, status, to_number, body, last_error FROM supplier_msg WHERE month='2099-08' ORDER BY id")
A = next((m for m in msgs if m["vendor"] == "W407 VENDOR A"), {}); B = next((m for m in msgs if m["vendor"] == "W407 VENDOR B"), {})
BODY_A = "Sanjeevni Medicos, Bareilly: ₹1,01,000 for August 2099 purchases transferred by NEFT on 24-Sep-2026 to your account %s, IFSC %s. Thank you." % (ACCT, IFSC)
out["msgs"] = [len(msgs), A.get("status"), A.get("to_number") == "91" + PH, A.get("body") == BODY_A, B.get("status"), B.get("last_error"), (ACCT2 in (B.get("body") or ""))]
st1 = S("2099-08")[1]
out["state1"] = [st1["status"], st1["event"]["source"], st1["event"]["created_by"], st1["can_undo"], st1["counts"], leak(json.dumps(st1))]
pg = G("manoj", "/finance/purchase/page/pay/2099-08")[1]
out["page_owner"] = ["neftcard_s407" in pg, "awaiting bank statement" in pg, "Undo (within 24 h)" in pg, "W407 VENDOR A" in pg, leak_ph(pg)]
pgs = G("shavez", "/finance/purchase/page/pay/2099-08")[1]
out["page_shavez"] = ["bank statement ka intezaar" in pgs, "NEFT done (bank SMS received)" in pgs, "phone-setup" in pgs, leak_ph(pgs)]
pgd = G("darpan", "/finance/purchase/page/pay/2099-08")[1]
out["page_darpan"] = [leak_ph(pgd), "neftcard_s407" in pgd]
out["page_bhati"] = G("bhati", "/finance/purchase/page/pay/2099-08")[0]
out["state_gate"] = {u: S("2099-08", u)[0] for u in ("bhati", "amir", "stranger")}
out["state_amir_leak"] = leak(json.dumps(S("2099-08", "amir")[1])) if S("2099-08", "amir")[0] == 200 else []
# --- the phone's door
out["next_bad"] = [G("nobody", "/finance/api/supplier-msg/next", h={"X-Phone-Token": "wrong"})[0], G("nobody", "/finance/api/supplier-msg/next")[0], P("nobody", "/finance/api/supplier-msg/done", {"id": A.get("id"), "ok": True})[0]]
nx = G("nobody", "/finance/api/supplier-msg/next", h=T)
out["next1"] = [nx[0], (nx[1] or {}).get("id") == A.get("id"), (nx[1] or {}).get("to") == "91" + PH, (nx[1] or {}).get("text") == BODY_A]
out["done_fail"] = P("nobody", "/finance/api/supplier-msg/done", {"id": A.get("id"), "ok": False, "error": "send not clicked"}, h=T)
out["row_fail"] = q("SELECT status, attempts, last_error FROM supplier_msg WHERE id=?", A.get("id"))
out["next2"] = G("nobody", "/finance/api/supplier-msg/next", h=T)[1]
db.execute("UPDATE supplier_msg SET last_try_at=? WHERE id=?", ((dt.datetime.now() - dt.timedelta(minutes=31)).replace(microsecond=0).isoformat(), A.get("id"))); db.commit()
out["next3"] = (G("nobody", "/finance/api/supplier-msg/next", h=T)[1] or {}).get("id") == A.get("id")
out["done_ok"] = P("nobody", "/finance/api/supplier-msg/done", {"id": A.get("id"), "ok": True}, h=T)
out["row_ok"] = q("SELECT status, attempts, sent_by, sent_at IS NOT NULL AS has_at FROM supplier_msg WHERE id=?", A.get("id"))
out["next4"] = G("nobody", "/finance/api/supplier-msg/next", h=T)[1]
# --- the cheque supplier: told when the cheque is marked handed
db.execute("INSERT INTO purchase_cheque (month, vendor_norm, vendor, payee, cheque_no, cheque_date, amount_p, created_at, created_by) VALUES (?,?,?,?,?,?,?,?,?)",
           ("2099-08", "W407 CHEQUE VENDOR C", "W407 CHEQUE VENDOR C", "W407 CHEQUE VENDOR C", "W407C1", "2026-09-24", 30300000, now(), "walk")); db.commit()
cid = one("SELECT id FROM purchase_cheque WHERE cheque_no='W407C1'")
S("2099-08"); out["cheque_before"] = q("SELECT COUNT(*) AS n FROM supplier_msg WHERE kind='cheque'")[0]["n"]
db.execute("UPDATE purchase_cheque SET handed_at=?, handed_by='shavez' WHERE id=?", (now(), cid)); db.commit()
S("2099-08")
cm = q("SELECT id, vendor, status, to_number, body, queued_at FROM supplier_msg WHERE kind='cheque' AND ref=?", cid)
BODY_C = "Sanjeevni Medicos, Bareilly: ₹3,03,000 for August 2099 purchases paid by cheque no W407C1 dated 24-Sep-2026. Thank you."
out["cheque_msg"] = [len(cm), cm[0]["status"] if cm else None, (cm[0]["to_number"] == "91" + PH2) if cm else None, (cm[0]["body"] == BODY_C) if cm else None]
# --- the backup Bhejo after 30 minutes; Needs you
db.execute("UPDATE supplier_msg SET queued_at=? WHERE id=?", ((dt.datetime.now() - dt.timedelta(minutes=31)).replace(microsecond=0).isoformat(), cm[0]["id"])); db.commit()
st2 = S("2099-08")[1]
out["pending"] = [[m["vendor"], m["pending"]] for m in st2["messages"] if m["pending"]]
NL = lambda: [l["text"] for l in (G("manoj", "/finance/sanjeevni/api/needs-you")[1] or {}).get("lines", [])]
out["needs_pending"] = [t for t in NL() if "supplier message" in t]
pgs2 = G("shavez", "/finance/purchase/page/pay/2099-08")[1]
out["page_pending"] = ["Pending" in pgs2 and "Bhejo" in pgs2, leak_ph(pgs2)]
out["send_bhati"] = P("bhati", "/finance/purchase/api/supplier-msg/send", {"id": cm[0]["id"]})[0]
out["send_darpan"] = P("darpan", "/finance/purchase/api/supplier-msg/send", {"id": cm[0]["id"]})
out["send_darpan"] = [out["send_darpan"][0], leak(json.dumps(out["send_darpan"][1]))]
sd = P("shavez", "/finance/purchase/api/supplier-msg/send", {"id": cm[0]["id"]})
out["send_shavez"] = [sd[0], (sd[1] or {}).get("wa_url") == "https://wa.me/91%s?text=%s" % (PH2, quote(BODY_C, safe=""))]
out["send_row"] = q("SELECT status, sent_by FROM supplier_msg WHERE id=?", cm[0]["id"])
out["send_again"] = (P("shavez", "/finance/purchase/api/supplier-msg/send", {"id": cm[0]["id"]})[1] or {}).get("already")
out["needs_after_send"] = [t for t in NL() if "supplier message" in t]
# --- the statement confirms 2099-08; contradicts 2099-07
ref = re.sub(r"\D", "", str(pa._pay_config_s265(db, "debit_account", "") or ""))[-4:] or "W407"
db.execute("INSERT OR IGNORE INTO bank_statement_period (account_ref, period_from, period_to, source_file, ingested_at) VALUES (?,?,?,?,?)", (ref, "2026-09-01", "2026-09-30", "W407", now()))
db.execute("INSERT OR IGNORE INTO bank_statement_line (account_ref, txn_date, description, reference, withdrawal_p, deposit_p, source_file, ingested_at) VALUES (?,?,?,?,?,?,?,?)",
           (ref, "2026-09-25", "Multiple Payee-NEFT DR-21-YES-W407A- CMS_W407.TXT", "W407REF1", 15150000, 0, "W407", now())); db.commit()
st3 = S("2099-08")[1]
out["confirmed"] = [st3["status"], (st3["bank_line"] or {}).get("date"), st3["event"]["bank_line_id"] is not None, st3["can_undo"]]
pg3 = G("manoj", "/finance/purchase/page/pay/2099-08")[1]
out["page_confirmed"] = ["Confirmed by bank 25-Sep-2026" in pg3, "awaiting bank statement" in pg3, leak_ph(pg3)]
out["undo_confirmed"] = P("manoj", "/finance/purchase/api/neft-undo", {"month": "2099-08"})
out["done_jul"] = P("manoj", "/finance/purchase/api/neft-done", {"month": "2099-07", "date": "2026-09-20"})
db.execute("INSERT OR IGNORE INTO bank_statement_line (account_ref, txn_date, description, reference, withdrawal_p, deposit_p, source_file, ingested_at) VALUES (?,?,?,?,?,?,?,?)",
           (ref, "2026-09-22", "Multiple Payee-NEFT DR-21-YES-W407D- CMS_W407.TXT", "W407REF2", 20000000, 0, "W407", now())); db.commit()
st4 = S("2099-07")[1]
out["mismatch"] = [st4["status"], st4["diff_p"], (st4["bank_line"] or {}).get("amount_p"), st4["can_undo"]]
out["needs_mismatch"] = [t for t in NL() if t.startswith("NEFT of July 2099")]
pg4 = G("manoj", "/finance/purchase/page/pay/2099-07")[1]
out["page_mismatch"] = ["differs by ₹2,000" in pg4, leak_ph(pg4)]
# --- undo within 24 h; too late; the S405 SMS event confirmed by the tap
out["undo_darpan"] = P("darpan", "/finance/purchase/api/neft-undo", {"month": "2099-07"})[0]
out["undo"] = P("manoj", "/finance/purchase/api/neft-undo", {"month": "2099-07"})
out["after_undo"] = [S("2099-07")[1]["status"], q("SELECT kind, note FROM purchase_neft_event WHERE month='2099-07' ORDER BY id"), q("SELECT status, last_error FROM supplier_msg WHERE month='2099-07'")]
out["done_jul2"] = P("manoj", "/finance/purchase/api/neft-done", {"month": "2099-07", "date": "2026-09-21"})[1]
db.execute("UPDATE purchase_neft_event SET created_at=? WHERE id=?", ((dt.datetime.now() - dt.timedelta(hours=25)).replace(microsecond=0).isoformat(), out["done_jul2"]["event_id"])); db.commit()
out["undo_late"] = P("manoj", "/finance/purchase/api/neft-undo", {"month": "2099-07"})
db.execute("INSERT INTO purchase_neft_event (month, kind, source, amount_p, sms_date, utr, created_at, created_by) VALUES ('2099-05','provisional','sms',4040000,'2026-09-23','W407SMS1',?, 'sms')", (now(),)); db.commit()
out["done_may"] = P("manoj", "/finance/purchase/api/neft-done", {"month": "2099-05", "date": "2026-09-23"})[1]
out["may_events"] = q("SELECT source, kind, confirmed_by, utr FROM purchase_neft_event WHERE month='2099-05'")
out["may_msgs"] = q("SELECT COUNT(*) AS n FROM supplier_msg WHERE month='2099-05'")[0]["n"]
# --- Amir's board, Needs-you gate, the setup page, the audit
am = G("amir", "/finance/amir/step/1")
out["amir"] = [am[0], "NEFT August 2099" in am[1], "ho gaya" in am[1], "bata diya" in am[1], "NEFT July 2099" in am[1], leak(am[1])]
out["needs_gate"] = {u: G(u, "/finance/sanjeevni/api/needs-you")[0] for u in ("bhati", "darpan", "amir")}
db.execute("DELETE FROM setting WHERE key='supplier_msg.token_shown'"); db.commit()      # the shared probe above opened the page once already
sp1 = G("shavez", "/finance/purchase/page/phone-setup"); sp2 = G("shavez", "/finance/purchase/page/phone-setup"); spo = G("manoj", "/finance/purchase/page/phone-setup")
out["setup"] = [sp1[0], TOK in sp1[1], "MacroDroid" in sp1[1], TOK in sp2[1], "ek baar dikha diya" in sp2[1], TOK in spo[1], G("bhati", "/finance/purchase/page/phone-setup")[0], leak(sp1[1])]
out["audit"] = [[r["action"], leak(r["detail"] or "")] for r in q("SELECT action, detail FROM purchase_audit WHERE action IN ('neft_done','neft_undo','supplier_msg_sent') ORDER BY id")]
out["public"] = [fa.PUBLIC_PATHS.count("/finance/api/supplier-msg/next"), fa.PUBLIC_PATHS.count("/finance/api/supplier-msg/done")]
print("JSON:" + json.dumps(out, default=str))
'''


def probe(appdir, mode, dbpath):
    env = dict(os.environ, APPDIR=appdir, MODE=mode, FINANCE_DB=dbpath, FINANCE_UI_DIR=os.path.join(appdir, "finance_ui"), FINANCE_ALLOW_HEADER_AUTH="1")
    p = subprocess.run([sys.executable, "-B", "-c", PROBE], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=appdir)
    O = next((json.loads(x[5:]) for x in p.stdout.splitlines() if x.startswith("JSON:")), None)
    if not O:
        sys.exit("!! the %s app did not answer: %s\n%s" % (mode, p.stderr[-3000:], p.stdout[-800:]))
    return O


O = probe(a.old, "old", a.db + ".old")
N = probe(a.app, "new", a.db)

print("-- 1  the tap: NEFT done on a finalised month, once")
check("supplier_msg is mounted from purchase_app; the two token doors are on the front gate's public list", N["mounted"] and N["public"] == [1, 1], (N["mounted"], N["public"]))
check("before the tap: month 2099-08 final, NEFT portion ₹1,51,500 over two NEFT vendors, no event; the owner reads as 'owner'",
      N["state0"] == ["none", True, 15150000, ["W407 VENDOR A", "W407 VENDOR B"], None, "owner"], N["state0"])
check("an unfinalised month is refused (409); darpan cannot record (403); a bad month 400; a future date 400",
      N["done_open"][0] == 409 and N["done_darpan"] == 403 and N["done_bad"] == 400 and N["done_future"] == 400, (N["done_open"], N["done_darpan"], N["done_bad"], N["done_future"]))
check("the owner's tap writes ONE purchase_neft_event (provisional, source owner, ₹1,51,500, the date, the UTR, confirmed by him); a second tap answers already",
      N["done"][0] == 200 and N["done"][1]["queued"] == 1 and N["done_again"].get("already") is True and N["done_again"].get("within_10min") is True
      and N["event"] == [{"month": "2099-08", "kind": "provisional", "source": "owner", "amount_p": 15150000, "sms_date": "2026-09-24", "utr": "W407UTR1", "created_by": "manoj", "confirmed_by": "manoj", "bank_line_id": None}], (N["done"], N["done_again"], N["event"]))

print("-- 2  the queue: one row per NEFT supplier, the body word for word, the number only in the row")
check("two rows: A queued to the phone book's number with EXACTLY the format (₹1,01,000, August 2099, 24-Sep-2026, the full account, the IFSC); B skipped 'number nahi' (its body still built)",
      N["msgs"] == [2, "queued", True, True, "skipped", "number nahi", True], N["msgs"])
check("the state reads 'awaiting' (amber), by the owner, undo allowed; the JSON carries no number", N["state1"][0] == "awaiting" and N["state1"][1] == "owner" and N["state1"][2] == "manoj" and N["state1"][3] is True and N["state1"][5] == [], N["state1"])
check("the owner's pay page: the card, the amber chip 'awaiting bank statement' on the vendor, the Undo; NO phone number in the page (the S265 advice annexure's accounts are the owner's own design)", N["page_owner"] == [True, True, True, True, []], N["page_owner"])
check("Shavez's page: the same in Hindi ('bank statement ka intezaar'), no NEFT-done button, the setup link; NO phone number", N["page_shavez"] == [True, False, True, []], N["page_shavez"])
check("darpan's page carries no phone number; bhati cannot open the page (302/403); the state API refuses bhati / amir / a stranger or leaks nothing to amir",
      N["page_darpan"][0] == [] and N["page_bhati"] in (302, 403) and all(v in (200, 302, 403) for v in N["state_gate"].values()) and N["state_amir_leak"] == [], (N["page_darpan"], N["page_bhati"], N["state_gate"], N["state_amir_leak"]))

print("-- 3  the reception phone's door (token)")
check("next / done without the token or with a wrong one: 401", N["next_bad"] == [401, 401, 401], N["next_bad"])
check("next with the token returns the oldest queued row: id, the number, the exact text", N["next1"] == [200, True, True, True], N["next1"])
check("done {ok:false} -> failed, attempts 1, the error kept; next is then empty (30 minutes not passed)", N["done_fail"][0] == 200 and N["row_fail"] == [{"status": "failed", "attempts": 1, "last_error": "send not clicked"}] and N["next2"] == {}, (N["done_fail"], N["row_fail"], N["next2"]))
check("after 30 minutes next offers it again; done {ok:true} -> sent by 'reception-phone'; next is empty", N["next3"] is True and N["done_ok"][0] == 200 and N["row_ok"] == [{"status": "sent", "attempts": 2, "sent_by": "reception-phone", "has_at": 1}] and N["next4"] == {}, (N["next3"], N["row_ok"], N["next4"]))

print("-- 4  the cheque supplier, the backup Bhejo, Needs you")
check("a cheque on the register gets no message until it is marked handed; then ONE row to the vendor's number with EXACTLY the cheque format", N["cheque_before"] == 0 and N["cheque_msg"] == [1, "queued", True, True], (N["cheque_before"], N["cheque_msg"]))
check("30 minutes later it is 'Pending — <vendor>' on the state and on Shavez's page with Bhejo; Needs you says '1 supplier message unsent'",
      N["pending"] == [["W407 CHEQUE VENDOR C", True]] and N["page_pending"] == [True, []] and N["needs_pending"] and N["needs_pending"][0].startswith("1 supplier message unsent"), (N["pending"], N["page_pending"], N["needs_pending"]))
check("Bhejo: bhati refused (302/403); darpan refused (403, no number in the answer); shavez gets the wa.me link with the number and the exact text; the row is sent by shavez; again = already; the Needs-you line is gone",
      N["send_bhati"] in (302, 403) and N["send_darpan"] == [403, []] and N["send_shavez"] == [200, True] and N["send_row"] == [{"status": "sent", "sent_by": "shavez"}] and N["send_again"] is True and N["needs_after_send"] == [],
      (N["send_bhati"], N["send_darpan"], N["send_shavez"], N["send_row"], N["send_again"], N["needs_after_send"]))

print("-- 5  the bank: confirmed (green) · a differing debit (red) · undo")
check("a Yes Bank NEFT debit equal to the portion on 25-Sep: the state reads confirmed with the line's date, bank_line_id set, undo no longer offered; the page chip 'Confirmed by bank 25-Sep-2026' replaces the amber; no number",
      N["confirmed"] == ["confirmed", "2026-09-25", True, False] and N["page_confirmed"] == [True, False, []] and N["undo_confirmed"][0] == 409, (N["confirmed"], N["page_confirmed"], N["undo_confirmed"]))
check("July 2099 (₹2,02,000) against a NEFT debit of ₹2,00,000: mismatch, difference −₹2,000 on the state, red on the page, a Needs-you line",
      N["done_jul"][0] == 200 and N["mismatch"] == ["mismatch", -200000, 20000000, True] and N["page_mismatch"] == [True, []] and N["needs_mismatch"] and "differs by ₹2,000" in N["needs_mismatch"][0], (N["mismatch"], N["page_mismatch"], N["needs_mismatch"]))
check("undo: darpan refused; the owner's undo marks the event rejected ('undone by manoj'), cancels its queued message, the state reads none",
      N["undo_darpan"] == 403 and N["undo"][0] == 200 and N["undo"][1]["cancelled"] == 1 and N["after_undo"][0] == "none" and N["after_undo"][1][0]["kind"] == "rejected" and "undone by manoj" in N["after_undo"][1][0]["note"]
      and N["after_undo"][2] == [{"status": "skipped", "last_error": "undone"}], (N["undo"], N["after_undo"]))
check("a fresh tap after the undo makes a new event; 25 hours later the undo is refused (too late)", N["done_jul2"].get("event_id") and N["undo_late"][0] == 409 and N["undo_late"][1]["error"] == "too_late", (N["done_jul2"], N["undo_late"]))
check("S405's pending SMS event for May 2099 is CONFIRMED by the tap (not duplicated): one event, source sms, confirmed by manoj, the queue built",
      N["done_may"].get("confirmed_sms") is True and N["may_events"] == [{"source": "sms", "kind": "provisional", "confirmed_by": "manoj", "utr": "W407SMS1"}] and N["may_msgs"] == 1, (N["done_may"], N["may_events"], N["may_msgs"]))

print("-- 6  Amir's board, the setup page, the audit, the gate")
check("Amir's step page carries 'NEFT August 2099 … ho gaya' with 'bata diya' for the supplier told, and July's 'baaki'; no number", N["amir"] == [200, True, True, True, True, []], N["amir"])
check("the setup page: Shavez sees the steps and the token ONCE; the second load says it was shown; the owner sees it again; bhati refused; no number on the page",
      N["setup"][0] == 200 and N["setup"][1] is True and N["setup"][2] is True and N["setup"][3] is False and N["setup"][4] is True and N["setup"][5] is True and N["setup"][6] in (302, 403) and N["setup"][7] == [], N["setup"][:1] + N["setup"][2:])
check("the audit rows (neft_done / neft_undo / supplier_msg_sent) exist and carry no number", len(N["audit"]) >= 5 and all(x[1] == [] for x in N["audit"]), [x[0] for x in N["audit"]])
check("bhati, darpan and amir cannot read Needs you", all(v in (302, 403) for v in N["needs_gate"].values()), N["needs_gate"])

print("-- 7  NEGATIVE CONTROLS on the box as it is (the unpatched files, the same crafted months)")
check("NEGATIVE: the old pay page has no NEFT card; the old state route is 404; Amir's old page has no NEFT card; no setup page; no supplier_msg table",
      O["pay_page_old"][1] is False and O["state_old"] == 404 and O["amir_old"][1] is False and O["setup_old"] == 404 and O["tables_old"] is False, (O["pay_page_old"], O["state_old"], O["amir_old"], O["setup_old"], O["tables_old"]))
check("NEGATIVE: the old Needs you has no supplier-message line; the old pay page carries no phone number (its S265 annexure already shows the accounts: %s); Amir's old page nothing" % O["pay_page_old"][3],
      not any("supplier message" in t or t.startswith("NEFT of July") for t in O["needs_old"]) and O["pay_page_old"][2] == [] and O["amir_old"][2] == [], (O["needs_old"], O["pay_page_old"]))

print(("WALK_S407 GREEN -- %d/%d" % (n, n)) if not fails else ("WALK_S407 RED -- %d of %d failed" % (len(fails), n)))
sys.exit(1 if fails else 0)
