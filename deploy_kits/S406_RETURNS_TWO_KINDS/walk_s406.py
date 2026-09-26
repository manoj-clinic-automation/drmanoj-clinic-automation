#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s406.py -- kit S406_RETURNS_TWO_KINDS. THE REAL finance_app.py (a copy of /root/finance carrying the kit's files)
over a SCRATCH COPY of finance.db, driven through Flask's test client with header identity (walk only). The real
September is read first, read-only (CN00208 classes noncash; the Need-your-OK count); then its own credit notes, keyed
W406*, are crafted on the scratch copy in the current month -- a home-medicine text, a rounding discount, a real
discount, a never-bought, an orphan with a kept name, an over-refund inside and outside the rounding line, a return
against the patient's own home bill -- and every rule is proved on them. Patient names it prints are its own crafted ones.

  --app NEW  --old OLD   (copies of /root/finance: the kit's files / the box as it is)
  --db PATH              (the scratch finance.db; PATH.old is made for the old app)
"""
import argparse
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
import seed_s406  # noqa: E402
assert seed_s406.seed(a.db) == 0, "seed failed"
print("-- scratch seeded (the three settings); old-app scratch copy made")

PROBE = r'''
import json, os, sys, sqlite3, datetime as dt, re, time
APP = os.environ["APPDIR"]; sys.path.insert(0, APP); os.chdir(APP)
os.environ["FINANCE_ALLOW_HEADER_AUTH"] = "1"
NEW = os.environ["MODE"] == "new"
import finance_app as fa
c = fa.app.test_client()
H = lambda u: {"X-Clinic-User": u, "X-Clinic-Role": ""}
def G(u, p):
    r = c.get(p, headers=H(u)); j = r.get_json(silent=True)
    return [r.status_code, j if j is not None else r.get_data(as_text=True)]
def P(u, p, b=None):
    r = c.post(p, json=(b or {}), headers=H(u)); return [r.status_code, r.get_json(silent=True)]
db = sqlite3.connect(os.environ["FINANCE_DB"], timeout=30); db.row_factory = sqlite3.Row
q = lambda s, *a: [dict(r) for r in db.execute(s, a).fetchall()]
one = lambda s, *a: db.execute(s, a).fetchone()[0]
has = lambda t: bool(db.execute("SELECT 1 FROM sqlite_master WHERE name=?", (t,)).fetchone())
now = lambda: dt.datetime.now().replace(microsecond=0).isoformat()
M = dt.date.today().strftime("%Y-%m")
out = {"month": M}
def cn(month=M):
    t0 = time.time(); r = G("manoj", "/finance/darpan/api/cn-detail?month=" + month); out.setdefault("ms", []).append(("cn", int((time.time() - t0) * 1000))); return r[1]
def needs_line():
    t0 = time.time(); j = G("manoj", "/finance/sanjeevni/api/needs-you")[1]; out.setdefault("ms", []).append(("needs", int((time.time() - t0) * 1000)))
    for l in (j or {}).get("lines", []):
        m = re.match(r"^(\d+) returns? of ₹?([\d,]+) need", l["text"])
        if m: return [int(m.group(1)), int(m.group(2).replace(",", ""))]
    return [0, 0]
# --- 1  the real month, read-only
j0 = cn()
out["real0"] = [j0.get("count"), j0.get("total_p"), j0.get("pending_old"), j0.get("pending_approval"), (j0.get("kinds") or {}).get("counter"), (j0.get("kinds") or {}).get("noncash"), "kinds" in j0]
cn208 = next((x for x in j0.get("notes", []) if x.get("bill") == "CN00208"), None)
out["cn208"] = [cn208.get("kind"), cn208.get("kind_why"), cn208.get("status"), cn208.get("amount_p")] if cn208 else None
out["real_words"] = sorted(set(x.get("status") for x in j0.get("notes", []) if x.get("status")))
out["needs0"] = needs_line()
page = G("manoj", "/finance/approvals")[1]
out["page"] = ["loadCNOld" in page, "cn-kind" in page, "Counter returns —" in page, 'class="num">returns</th>' in page]
mo = G("manoj", "/finance/sanjeevni/api/months")[1]
out["months0"] = [[m["ym"], m.get("counter_returns_pct"), m.get("counter_returns_p"), "counter_returns_pct" in m] for m in (mo or {}).get("months", [])]
# --- 2  the crafted credit notes, this month, on the scratch copy
D = q("SELECT id, business_date FROM day_entry WHERE unit='medical' AND substr(business_date,1,7)=? AND status IN ('submitted','draft') ORDER BY business_date DESC LIMIT 1", M)
DP = q("SELECT id, business_date FROM day_entry WHERE unit='medical' AND substr(business_date,1,7)=? AND business_date < ? ORDER BY business_date DESC LIMIT 1", M, D[0]["business_date"]) if D else []
out["days"] = [D[0]["business_date"] if D else None, DP[0]["business_date"] if DP else None]
eid, d = D[0]["id"], D[0]["business_date"]; eidp, dp = DP[0]["id"], DP[0]["business_date"]
db.execute("DELETE FROM sale_line_item WHERE unit='medical' AND bill_no LIKE 'W406%'"); db.execute("DELETE FROM sale_item WHERE source_ref LIKE 'W406%'")
db.execute("INSERT INTO patient_ref (clinic_id, name, first_seen) VALUES ('W406A','W406 PATIENT',?)", (dp,)); pid = one("SELECT id FROM patient_ref WHERE clinic_id='W406A'")
db.execute("INSERT INTO patient_ref (clinic_id, name, first_seen) VALUES ('W406B','W406 HOME PATIENT',?)", (dp,)); pid2 = one("SELECT id FROM patient_ref WHERE clinic_id='W406B'")
def item(eid_, unit, pid_, svc, desc, amt, ref):
    db.execute("INSERT INTO sale_item (day_entry_id, unit, patient_ref_id, service, description, amount_p, mode, source, source_ref, confidence) VALUES (?,?,?,?,?,?,?,?,?,?)", (eid_, unit, pid_, svc, desc, amt, "cash", "manual", ref, 1.0))
def line(eid_, date_, bill, ret, seq, key, rate):
    db.execute("INSERT INTO sale_line_item (day_entry_id, unit, business_date, bill_no, is_return, seq, item_name, item_key, pack, qty_raw, amount_p) VALUES (?,?,?,?,?,?,?,?,?,?,?)", (eid_, "medical", date_, bill, ret, seq, key.replace("W406", "W406 "), key, "1*1", "1", rate))
item(eidp, "medical", pid, "pharmacy", "W406 sale", 211200, "W406S1"); line(eidp, dp, "W406S1", 0, 1, "W406ITEM", 150000); line(eidp, dp, "W406S1", 0, 2, "W406ITEMB", 61200)
item(eidp, "medical", pid2, "pharmacy", "W406 home sale", 80000, "W406S2")
db.execute("INSERT INTO day_noncash_bill (day_entry_id, unit, bill_date, head, bill_no, amount_p, status, entered_by, entered_at) VALUES (?,?,?,?,?,?,?,?,?)", (eidp, "medical", dp, "home_medicine", "W406S2", 80000, "open", "walk", now()))
item(eid, "medical", None, "pharmacy_return", "W406 cn1", 150000, "W406CN1")
db.execute("INSERT INTO sale_item_review (day_entry_id, raw_text, guess_name, amount_p, confidence, status) VALUES (?,?,?,?,?,?)", (eid, json.dumps({"bill_no": "W406CN1", "patient_name": "HOME MEDICINE W406", "amount": "1500.00"}), "HOME MEDICINE W406", 150000, 0.5, "open"))
item(eid, "medical", pid, "pharmacy_return", "W406 cn2", 60000, "W406CN2"); line(eid, d, "W406CN2", 1, 1, "W406ITEMB", 61200)
item(eid, "medical", pid, "pharmacy_return", "W406 cn3", 142000, "W406CN3"); line(eid, d, "W406CN3", 1, 1, "W406ITEM", 150000)
item(eid, "medical", pid, "pharmacy_return", "W406 cn4", 30000, "W406CN4"); line(eid, d, "W406CN4", 1, 1, "W406ITEMC", 30000)
line(eid, d, "W406CN5", 1, 1, "W406ITEMD", 25000)
db.execute("INSERT INTO identity_resolution (unit, business_date, bill_no, rung, bill_name, noted_at) VALUES ('medical',?,?,?,?,?)", (d, "W406CN5", "walk", "W406 ORPHAN PATIENT", now()))
item(eid, "medical", pid, "pharmacy_return", "W406 cn6", 61700, "W406CN6"); line(eid, d, "W406CN6", 1, 1, "W406ITEMB", 61700)
item(eid, "medical", pid, "pharmacy_return", "W406 cn7", 65000, "W406CN7"); line(eid, d, "W406CN7", 1, 1, "W406ITEMB", 65000)
item(eid, "medical", pid2, "pharmacy_return", "W406 cn8", 80000, "W406CN8")
db.commit()
j1 = cn()
W = {x["bill"]: x for x in j1.get("notes", []) if str(x.get("bill", "")).startswith("W406")}
out["w_n"] = len(W)
if not NEW:
    out["old_pending"] = [j0.get("pending_approval"), j1.get("pending_approval"), "kinds" in j1]
    out["old_w"] = {k: [v.get("verdict"), v.get("needs_approval"), v.get("kind")] for k, v in W.items()}
    out["needs1"] = needs_line()
    print("JSON:" + json.dumps(out, default=str)); raise SystemExit
K1 = j1["kinds"]
out["w"] = {k: [v.get("kind"), v.get("kind_why"), v.get("verdict"), v.get("diff_p"), v.get("noise"), v.get("status"), v.get("needs_ok"), v.get("pending_ok"), v.get("name") or v.get("patient_text")] for k, v in sorted(W.items())}
out["pending1"] = [j0["pending_approval"], j1["pending_approval"], j0["pending_old"], j1["pending_old"]]
out["sums"] = [K1["counter"]["p"] - j0["kinds"]["counter"]["p"], K1["noncash"]["p"] - j0["kinds"]["noncash"]["p"], K1["counter"]["n"] - j0["kinds"]["counter"]["n"], K1["noncash"]["n"] - j0["kinds"]["noncash"]["n"]]
import sanjeevni_cash as sc
mr = next((m for m in sc.month_rows(db, "medical") if m["ym"] == M), None)
cs = (mr["sale_p"] - mr["home_p"] - mr["proc_p"]) if mr else None
out["pct"] = [K1["counter"]["sales_p"], cs, K1["counter"]["pct"], (round(100.0 * K1["counter"]["p"] / cs, 1) if cs else None), K1.get("prev", {}).get("ym"), "counter_returns_pct" in K1.get("prev", {})]
out["kinds_rows"] = q("SELECT bill_no, kind, source, by FROM cn_kind WHERE unit='medical' AND bill_no LIKE 'W406%' ORDER BY bill_no")
# --- 3  the owner's flip, audited, kept; cn-approve untouched
out["flip_darpan"] = P("darpan", "/finance/darpan/api/cn-kind", {"bill": "W406CN2", "kind": "noncash"})[0]
out["flip_bad"] = P("manoj", "/finance/darpan/api/cn-kind", {"bill": "W406CN2", "kind": "sideways"})[0]
out["flip"] = P("manoj", "/finance/darpan/api/cn-kind", {"bill": "W406CN2", "kind": "noncash"})
j2 = cn(); W2 = {x["bill"]: x for x in j2["notes"] if str(x.get("bill", "")).startswith("W406")}
out["flip_after"] = [W2["W406CN2"]["kind"], W2["W406CN2"]["kind_source"], W2["W406CN2"]["kind_by"], j2["kinds"]["counter"]["n"] - K1["counter"]["n"], j2["kinds"]["noncash"]["n"] - K1["noncash"]["n"]]
out["flip_row"] = q("SELECT kind, source, by FROM cn_kind WHERE unit='medical' AND bill_no='W406CN2'")
out["flip_audit"] = q("SELECT who, action, detail FROM darpan_audit WHERE action='cn_kind' ORDER BY id DESC LIMIT 1")
P("manoj", "/finance/darpan/api/cn-kind", {"bill": "W406CN2", "kind": "counter"})
out["approve"] = P("manoj", "/finance/darpan/api/cn-approve", {"bill": "W406CN3", "decision": "approved", "note": "walk"})
j3 = cn(); W3 = {x["bill"]: x for x in j3["notes"] if str(x.get("bill", "")).startswith("W406")}
out["approve_after"] = [W3["W406CN3"]["status"], (W3["W406CN3"].get("approval") or {}).get("status"), W3["W406CN3"]["pending_ok"], j3["pending_approval"] - j1["pending_approval"], W3["W406CN2"]["kind"], W3["W406CN2"]["kind_source"]]
out["approval_row"] = q("SELECT status, decided_by FROM darpan_return_approval WHERE unit='medical' AND cn_bill='W406CN3'")
# --- 4  Needs you and the Month table
out["needs1"] = needs_line()
os.environ["NEEDS_YOU_WITHOUT_S406"] = "1"; out["needs_old_rule"] = needs_line(); del os.environ["NEEDS_YOU_WITHOUT_S406"]
t0 = time.time(); mo = G("manoj", "/finance/sanjeevni/api/months")[1]; out["ms"].append(("months", int((time.time() - t0) * 1000)))
mrow = next((m for m in mo["months"] if m["ym"] == M), {})
out["months1"] = [mrow.get("counter_returns_n"), mrow.get("counter_returns_p"), mrow.get("counter_returns_pct"), mrow.get("counter_returns"), j3["kinds"]["counter"]["n"], j3["kinds"]["counter"]["p"], j3["kinds"]["counter"]["pct"], all("counter_returns_pct" in m for m in mo["months"])]
out["gate"] = {u: G(u, "/finance/darpan/api/cn-detail?month=" + M)[0] for u in ("bhati", "darpan", "amir")}
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
M = N["month"]

print("-- 1  the real month (%s), read-only" % M)
r0 = N["real0"]
check("cn-detail answers with the two kinds: %s returns, ₹%s; counter %s; non-cash %s; Need-your-OK %s (was %s under the old rule)" % (r0[0], (r0[1] or 0) // 100, r0[4], r0[5], r0[3], r0[2]),
      r0[6] and isinstance(r0[4], dict) and r0[3] is not None and r0[3] <= 6, r0)
check("CN00208 (the HOME MEDICINE credit note, 11-Sep) classes noncash, and says why", N["cn208"] is not None and N["cn208"][0] == "noncash", N["cn208"])
check("every real line carries one status word from the set", all(w in ("ok", "never bought", "over-refund", "discounted", "unchecked", "large", "your OK", "rejected") for w in N["real_words"]), N["real_words"])
check("the Needs-you returns line carries the new count (%s)" % N["needs0"][0], N["needs0"][0] == r0[3], (N["needs0"], r0[3]))
check("the approvals page carries the new renderer, the flip route, the old renderer one link away, the Month returns column", all(N["page"]), N["page"])

print("-- 2  the crafted credit notes (%s, prior sale on %s)" % tuple(N["days"]))
w = N["w"]
check("all eight W406 notes are in the month", N["w_n"] == 8 and set(w) == {"W406CN%d" % i for i in range(1, 9)}, sorted(w))
check("W406CN1 (its text reads HOME MEDICINE) classes noncash by the credit note's own text; the audit could not run -> 'unchecked'; not in Need-your-OK though ₹1,500",
      w["W406CN1"][0] == "noncash" and "own text" in w["W406CN1"][1] and w["W406CN1"][5] == "unchecked" and w["W406CN1"][7] is False, w["W406CN1"])
check("W406CN2 (₹612 of goods, ₹600 refunded): DISCOUNTED RETURN by the audit, difference ₹12 = rounding -> reads ok, not in Need-your-OK",
      w["W406CN2"][0] == "counter" and w["W406CN2"][2] == "DISCOUNTED RETURN" and w["W406CN2"][3] == 1200 and w["W406CN2"][4] is True and w["W406CN2"][5] == "ok" and w["W406CN2"][7] is False, w["W406CN2"])
check("W406CN3 (₹1,500 of goods, ₹1,420 refunded): DISCOUNTED RETURN, ₹80 is not rounding, ₹1,000+ -> 'your OK', in Need-your-OK",
      w["W406CN3"][2] == "DISCOUNTED RETURN" and w["W406CN3"][3] == 8000 and w["W406CN3"][4] is False and w["W406CN3"][5] == "your OK" and w["W406CN3"][7] is True, w["W406CN3"])
check("W406CN4 (₹300, an item the patient never bought): NEVER BOUGHT -> 'your OK' whatever the amount", w["W406CN4"][2] == "NEVER BOUGHT" and w["W406CN4"][5] == "your OK" and w["W406CN4"][7] is True, w["W406CN4"])
check("W406CN5 (lines, no bill row): 'unchecked'; the patient named from the kept bill text (identity_resolution)", w["W406CN5"][2] == "no patient attributed" and w["W406CN5"][5] == "unchecked" and w["W406CN5"][8] == "W406 ORPHAN PATIENT", w["W406CN5"])
check("W406CN6 (refunded ₹5 over the price): REFUNDED MORE THAN PAID by the audit, rounding -> ok", w["W406CN6"][2] == "REFUNDED MORE THAN PAID" and w["W406CN6"][3] == 500 and w["W406CN6"][4] is True and w["W406CN6"][5] == "ok", w["W406CN6"])
check("W406CN7 (refunded ₹38 over): 'over-refund', shown, not in Need-your-OK (under ₹1,000)", w["W406CN7"][2] == "REFUNDED MORE THAN PAID" and w["W406CN7"][3] == 3800 and w["W406CN7"][5] == "over-refund" and w["W406CN7"][7] is False, w["W406CN7"])
check("W406CN8 (the patient's own bill W406S2 is a home-medicine bill): noncash by the patient's bill", w["W406CN8"][0] == "noncash" and "W406S2" in w["W406CN8"][1] and "home medicine" in w["W406CN8"][1], w["W406CN8"])
check("Need-your-OK grew by exactly 2 (CN3, CN4); the old rule would have grown by 8", N["pending1"][1] - N["pending1"][0] == 2 and N["pending1"][3] - N["pending1"][2] == 8, N["pending1"])
check("the counter figures grew by the six counter notes (₹3,837, 6) and the non-cash by the two (₹2,300, 2); the non-cash never enter the counter %",
      N["sums"] == [383700, 230000, 6, 2], N["sums"])
check("the % = counter returns ÷ (sale − home − procedure bills) of the month, from sanjeevni_cash's own month row, to the tenth; last month beside it",
      N["pct"][0] == N["pct"][1] and N["pct"][2] == N["pct"][3] and N["pct"][5], N["pct"])
check("cn_kind holds one auto row per crafted note", len(N["kinds_rows"]) == 8 and all(r["source"] == "auto" for r in N["kinds_rows"]), N["kinds_rows"])

print("-- 3  the owner's flip (audited, kept over the recompute); cn-approve untouched")
check("darpan cannot flip (403); a bad kind is 400; the owner flips W406CN2 to noncash (200)", N["flip_darpan"] == 403 and N["flip_bad"] == 400 and N["flip"][0] == 200, (N["flip_darpan"], N["flip_bad"], N["flip"]))
check("after the flip the note reads noncash (your word, manoj), counter −1 / non-cash +1; cn_kind source owner; darpan_audit carries cn_kind",
      N["flip_after"] == ["noncash", "owner", "manoj", -1, 1] and N["flip_row"] == [{"kind": "noncash", "source": "owner", "by": "manoj"}] and N["flip_audit"] and N["flip_audit"][0]["who"] == "manoj", (N["flip_after"], N["flip_row"], N["flip_audit"]))
check("cn-approve on W406CN3 still works: approved, its line reads ok, Need-your-OK −1; the flipped-back CN2 is still the owner's word",
      N["approve"][0] == 200 and N["approve_after"] == ["ok", "approved", False, -1, "counter", "owner"] and N["approval_row"] == [{"status": "approved", "decided_by": "manoj"}], (N["approve"], N["approve_after"], N["approval_row"]))

print("-- 4  Needs you and the Month table; the gate")
check("the Needs-you line uses the new count (%s); with NEEDS_YOU_WITHOUT_S406=1 (S400's re-run only) the old count (%s)" % (N["needs1"][0], N["needs_old_rule"][0]),
      N["needs1"][0] == N["pending1"][1] - 1 and N["needs_old_rule"][0] == N["pending1"][3] - 1, (N["needs1"], N["needs_old_rule"], N["pending1"]))
m1 = N["months1"]
check("the months API carries counter_returns / counter_returns_pct on every month; this month's equal the card's", m1[7] and m1[0] == m1[4] and m1[1] == m1[5] and m1[2] == m1[6] and m1[3] is not None, m1)
check("bhati, darpan and amir cannot read cn-detail (302/403)", all(v in (302, 403) for v in N["gate"].values()), N["gate"])
check("timing (information): cn-detail / needs-you / months in ms", True, N["ms"])

print("-- 5  NEGATIVE CONTROLS on the box as it is (the unpatched files, the same crafted notes)")
check("NEGATIVE: the old cn-detail has no kinds; CN1 and CN8 are not classed; the old Need-your-OK grows by 8 on the same eight notes (the ₹12 rounding one included)",
      O["old_pending"][2] is False and O["old_pending"][1] - O["old_pending"][0] == 8 and all(v[2] is None for v in O["old_w"].values()), (O["old_pending"], O["old_w"].get("W406CN2")))
check("NEGATIVE: the old Needs-you line carries the old count; the old months API has no returns column; the old page has no new renderer",
      O["needs1"][0] == O["old_pending"][1] and not any(m[3] for m in O["months0"]) and not any(O["page"]), (O["needs1"], O["old_pending"], O["page"]))

print(("WALK_S406 GREEN -- %d/%d" % (n, n)) if not fails else ("WALK_S406 RED -- %d of %d failed" % (len(fails), n)))
sys.exit(1 if fails else 0)
