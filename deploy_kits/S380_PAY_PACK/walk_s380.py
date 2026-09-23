#!/usr/bin/env python3
"""walk_s380.py -- kit S380_PAY_PACK. The REAL app over a SCRATCH COPY of finance.db, August set FINAL in
the copy as it is live. Proves: the pay page carries the pack button and the name box; the pack page holds
the three papers in order (letter, annexure, sheet) and prints each on its own sheet; the annexure on the
pack is the SAME annexure the pay page shows; the sign-off prints under the annexure and the sheet; the
letter's date, cheque number and the signature name can be typed after FINAL and are audited; every figure
door still refuses after FINAL; the email file keeps its exact bytes and is named by the month it is paid
in. Writes the rendered pages to --html for the print proof. Prints counts and words only.
  python3 walk_s380.py --app DIR --db scratch.db [--html DIR]
"""
import argparse, json, os, subprocess, sys
ap = argparse.ArgumentParser(); ap.add_argument("--app", required=True); ap.add_argument("--db", required=True)
ap.add_argument("--html")
a = ap.parse_args()
n, fails = 0, []
def check(label, cond, got=None):
    global n
    n += 1
    print(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got) + "]") if got is not None else ""))
    if not cond: fails.append(label)
PROBE = r'''
import json, os, sys, re, hashlib, sqlite3, io, zipfile
sys.path.insert(0, os.environ["APPDIR"]); os.chdir(os.environ["APPDIR"])
os.environ.update(FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_DEV_USER="manoj", FINANCE_DEV_ROLE="owner")
con = sqlite3.connect(os.environ["FINANCE_DB"])
con.execute("INSERT OR REPLACE INTO purchase_month (month, status, finalised_by, finalised_at) VALUES "
            "('2026-08','final','manoj','2026-09-23T09:30:00')")
con.commit(); con.close()
import finance_app as fa, purchase_app as pa
c = fa.app.test_client(); H = {"X-Clinic-User": "manoj", "X-Clinic-Role": "owner"}
V = {"X-Clinic-User": "shavez", "X-Clinic-Role": "viewer"}
B = "/finance/purchase"
out = {}
r = c.get(B + "/page/pay/2026-08", headers=H); pay = r.get_data(as_text=True)
out["pay"] = [r.status_code, "Print the bank pack" in pay, 'id="advcard_s380"' in pay, 'id="lt_sign"' in pay,
              pay.count('/page/pay/2026-08/pack?print=1'), "visibility:hidden" in pay.split("S266")[0] if False else ("body *{visibility:hidden" in pay)]
r = c.get(B + "/page/pay/2026-08/pack", headers=H); pk = r.get_data(as_text=True)
papers = re.findall(r'<div class="paper (port|land)">', pk)
i_l, i_a, i_s = pk.find('id="letter_s266"'), pk.find('id="advice_s265"'), pk.find('table class="sheet"')
out["pack"] = [r.status_code, papers, 0 < i_l < i_a < i_s, pk.count('<div class="sgnoff">'), "window.print()" in pk,
               "setTimeout(function(){window.print()" in pk]
def adv(t):
    i = t.index('<div id="advice_s265">'); j = t.index('<div class="sgnoff">', i); return t[i:j]
out["same_advice"] = adv(pay) == adv(pk)
out["pack_print"] = "setTimeout(function(){window.print()" in c.get(B + "/page/pay/2026-08/pack?print=1", headers=H).get_data(as_text=True)
# the letter's words after FINAL
r = c.post(B + "/api/pay-letter", json={"month": "2026-08", "date_text": "SEPTEMBER 23, 2026", "cheque_no": "000123",
           "signatory": "Test Signatory"}, headers=H)
out["letter_after_final"] = [r.status_code, (r.get_json() or {}).get("ok")]
pk2 = c.get(B + "/page/pay/2026-08/pack", headers=H).get_data(as_text=True)
out["after"] = [pk2.count("Test Signatory"), "000123" in pk2, "SEPTEMBER 23, 2026" in pk2,
                "No cheque number has been typed" in pk2, "No signature name is set" in pk2]
with fa.app.app_context():
    d = fa.db()
    out["audit"] = [d.execute("SELECT COUNT(*) FROM purchase_audit WHERE action='pay_signatory'").fetchone()[0],
                    d.execute("SELECT COUNT(*) FROM purchase_audit WHERE action='pay_letter'").fetchone()[0]]
    d.commit()
# figure doors still locked
r = c.post(B + "/api/pay-line", json={"month": "2026-08", "vendor_norm": "x", "carry_fwd": "1", "paid": ""}, headers=H)
out["payline_final"] = [r.status_code, "FINAL" in ((r.get_json() or {}).get("message") or "")]
out["viewer_letter"] = c.post(B + "/api/pay-letter", json={"month": "2026-08", "signatory": "X"}, headers=V).status_code
out["viewer_pack"] = c.get(B + "/page/pay/2026-08/pack", headers=V).status_code
# the email file
r = c.get(B + "/page/pay/2026-08/advice.xlsx", headers=H)
cd = r.headers.get("Content-Disposition", "")
z = zipfile.ZipFile(io.BytesIO(r.data))
out["xlsx"] = [r.status_code, cd, hashlib.md5(z.read("xl/worksheets/sheet1.xml")).hexdigest()]
r = c.get(B + "/page/pay/2025-12/advice.xlsx", headers=H); out["dec"] = r.headers.get("Content-Disposition", "")
out["other_months"] = [c.get(B + "/page/pay/2026-07", headers=H).status_code, c.get(B + "/page/pay/2026-09/pack", headers=H).status_code]
if os.environ.get("HTMLDIR"):
    open(os.path.join(os.environ["HTMLDIR"], "pay.html"), "w").write(c.get(B + "/page/pay/2026-08", headers=H).get_data(as_text=True))
    open(os.path.join(os.environ["HTMLDIR"], "pack.html"), "w").write(pk2)
print("JSON:" + json.dumps(out, default=str))
'''
env = dict(os.environ, APPDIR=a.app, FINANCE_DB=a.db, HTMLDIR=a.html or "")
p = subprocess.run([sys.executable, "-B", "-c", PROBE], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=a.app)
O = next((json.loads(x[5:]) for x in p.stdout.splitlines() if x.startswith("JSON:")), None)
if not O:
    sys.exit("!! the app did not answer: " + p.stderr[-3000:])
check("the payment sheet carries the pack button (twice: top and advice card), the name box, and no visibility trick",
      O["pay"][0] == 200 and O["pay"][1] and O["pay"][2] and O["pay"][3] and O["pay"][4] >= 2 and not O["pay"][5], O["pay"])
check("the pack holds three papers -- portrait, landscape, portrait", O["pack"][0] == 200 and O["pack"][1] == ["port", "land", "port"], O["pack"][:2])
check("in the order the bank gets them: the letter, the annexure, the sheet", O["pack"][2])
check("the sign-off prints twice (annexure and sheet) and the page has its print button", O["pack"][3] == 2 and O["pack"][4], O["pack"][3])
check("opened plain it does not print by itself; opened with ?print=1 it does", not O["pack"][5] and O["pack_print"])
check("the annexure in the pack is byte-for-byte the annexure on the payment sheet", O["same_advice"])
check("after FINAL the letter's date, cheque number and signature name are taken", O["letter_after_final"] == [200, True], O["letter_after_final"])
check("and they print: the name under both sign-offs, the cheque number and the date in the letter, the warnings gone",
      O["after"] == [2, True, True, False, False], O["after"])
check("each write is audited (the name once, the letter once)", O["audit"][0] >= 1 and O["audit"][1] >= 1, O["audit"])
check("a FIGURE door still refuses after FINAL (carried-in / paid)", O["payline_final"] == [403, True], O["payline_final"])
check("a viewer may read the pack but cannot type the letter", O["viewer_pack"] == 200 and O["viewer_letter"] == 403, [O["viewer_pack"], O["viewer_letter"]])
check("August's email file is named by the month it is PAID in -- SEPTEMBER", O["xlsx"][0] == 200 and "NEFT ADVICE SEPTEMBER 2026.xlsx" in O["xlsx"][1], O["xlsx"][1])
check("December's rolls into the next year", "NEFT ADVICE JANUARY 2026.xlsx" in O["dec"], O["dec"])
check("July's sheet and September's pack still open", O["other_months"] == [200, 200], O["other_months"])
print("XLSX_SHEET_MD5 " + O["xlsx"][2])
print(("WALK_S380 GREEN -- %d/%d" % (n, n)) if not fails else ("WALK_S380 RED -- %d of %d failed" % (len(fails), n)))
sys.exit(1 if fails else 0)
