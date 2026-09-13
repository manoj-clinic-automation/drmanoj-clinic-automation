#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_autoapply_s243.py -- the LIVE-SHAPE walk for S243_AUTOAPPLY.

A real Flask app (the finance_app.py named by FIN_APP, imported as gunicorn
imports it) over a real sqlite database built from finance_schema.sql +
finance_returns.sql, with the real finance_ingest / finance_returns /
marg_report beside it.  Every push is a REAL Marg-shaped .xls (written with
xlwt, read back by xlrd exactly as the server reads the counter's export),
sent as the multipart marg_gate.py builds (field 'file', X-Finance-Marg).

Nothing live is touched: everything lives in a temp folder that is removed.

    FIN_APP=<finance_app.py under test> FIN_MODS=<folder with the modules> \
        python3 -B walk_autoapply_s243.py

On the box after install (copies nothing live; builds its own db):
    FIN_APP=/root/finance/finance_app.py FIN_MODS=/root/finance \
        /root/wa/venv/bin/python3 -B /root/deploy/repo/deploy_kits/S243_AUTOAPPLY/walk_autoapply_s243.py

Run against an UNPATCHED file the walk asserts the SYMPTOM instead (a not-filed
day's push sits PENDING "(day not filed)") -- that is how 12-Sep sat overnight.
"""
import io
import json
import os
import shutil
import sqlite3
import sys
import tempfile

FIN_APP = os.environ.get("FIN_APP", "/root/finance/finance_app.py")
FIN_MODS = os.environ.get("FIN_MODS", os.path.dirname(os.path.abspath(FIN_APP)) or "/root/finance")
SCHEMA_DIR = os.environ.get("FIN_SCHEMA_DIR", FIN_MODS)
TMP = tempfile.mkdtemp(prefix="walk_s243_aa_")
MOD = os.path.join(TMP, "mods")
UI = os.path.join(TMP, "ui")
DB = os.path.join(TMP, "finance.db")
OFF = os.path.join(TMP, "AUTOAPPLY_OFF")
os.makedirs(MOD)
os.makedirs(UI)
shutil.copyfile(FIN_APP, os.path.join(MOD, "finance_app.py"))
for m in ("finance_ingest", "finance_returns", "finance_upi", "marg_report", "finance_identity"):
    p = os.path.join(FIN_MODS, m + ".py")
    if os.path.exists(p):
        shutil.copyfile(p, os.path.join(MOD, m + ".py"))
for f in ("finance_daily.html", "finance_review.html", "finance_approvals.html"):
    open(os.path.join(UI, f), "w").write("<html><body>walk stub %s</body></html>" % f)

con = sqlite3.connect(DB)
con.executescript(open(os.path.join(SCHEMA_DIR, "finance_schema.sql"), encoding="utf-8").read())
con.executescript(open(os.path.join(SCHEMA_DIR, "finance_returns.sql"), encoding="utf-8").read())
con.execute("CREATE TABLE IF NOT EXISTS upi_txn (id INTEGER PRIMARY KEY, merchant_id TEXT NOT NULL, "
            "unit TEXT, txn_date TEXT NOT NULL, amount_p INTEGER NOT NULL, rrn TEXT NOT NULL, mode TEXT, "
            "txn_time TEXT, source_sha TEXT, ingested_at TEXT)")
con.execute("UPDATE ingest_source SET active=1 WHERE unit='medical' AND adapter='marg_export'")
sid = con.execute("SELECT id FROM ingest_source WHERE unit='medical' AND adapter='marg_export'").fetchone()[0]
con.execute("DELETE FROM ingest_column_map WHERE source_id=?", (sid,))
for fld in ("bill_date", "bill_no", "clinic_id", "patient_name", "description", "amount", "mode"):
    con.execute("INSERT INTO ingest_column_map (source_id, our_field, their_column, required) VALUES (?,?,?,?)",
                (sid, fld, fld, 1 if fld in ("bill_date", "amount") else 0))
con.execute("INSERT OR IGNORE INTO unit_role (unit, username, role, active) VALUES ('medical','zzwalkdoc','checker',1)")
con.execute("INSERT OR IGNORE INTO unit_role (unit, username, role, active) VALUES ('medical','zzwalkmaker','maker',1)")
con.commit()
con.close()

os.environ.update(FINANCE_DB=DB, FINANCE_UI_DIR=UI, FINANCE_ALLOW_HEADER_AUTH="1",
                  FINANCE_PORTAL_LOGIN="/portal", FINANCE_SCAN_DIR=os.path.join(TMP, "scans"),
                  FINANCE_MARG_TOKEN="DUMMY-TOKEN-PUT-HERE", FINANCE_AUTOAPPLY_OFF=OFF,
                  FINANCE_UPI_DIR=os.path.join(TMP, "upi"))
sys.path.insert(0, MOD)
import finance_app as FA                                    # noqa: E402

SRC = open(FA.__file__, encoding="utf-8").read()
PATCHED = "S243 AUTO-APPLY -- newest export wins" in SRC
HAS_AUTOFILE = "S210 (D354 autofile)" in SRC
HAS_S219 = "S219 M1 -- MARG AUTO-APPLY" in SRC
HAS_DISMISS = "/finance/api/marg-push/dismiss" in SRC
print("walking %s" % FIN_APP)
print("  S243 mark: %s | S210 autofile: %s | S219 M1: %s | S210/S211 remove route: %s"
      % (PATCHED, HAS_AUTOFILE, HAS_S219, HAS_DISMISS))
print("  temp db %s" % DB)

PASSED, FAILED = [], []


def ck(label, cond, detail=""):
    (PASSED if cond else FAILED).append(label)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", label,
                          ("   [%s]" % str(detail)[:300]) if detail and not cond else ""))


# ---------------------------------------------------------------- the fake export
def make_xls(day_ddmmyyyy, bills):
    """bills: list of (bill_no, description, net_rupees, items) with items a
    list of (name, pack, qty, amount_rupees).  Shaped as Marg prints the
    BILL WISE SALES STATEMENT (Detail, with item detail): title, 9-column
    header, a date row, bill rows, drug lines under each bill, DAY TOTAL,
    GRAND TOTAL with the Bills: footer.  All cash; no phone anywhere."""
    import xlwt
    wb = xlwt.Workbook()
    sh = wb.add_sheet("Sheet1")
    r = 0
    sh.write(r, 0, "SANJEEVNI MEDICAL STORE (walk fixture)"); r += 1
    sh.write(r, 0, "BILL WISE SALES STATEMENT AS ON %s" % day_ddmmyyyy); r += 1
    for c, h in enumerate(["BILL NO.", "DESCRIPTION", "D.R.", "GROSS AMT.", "DISCOUNT",
                           "TAX", "DR/CR", "NET AMT.", "CASH"]):
        sh.write(r, c, h)
    r += 1
    sh.write(r, 0, day_ddmmyyyy); r += 1
    tot = 0
    for bill_no, desc, net, items in bills:
        sh.write(r, 0, bill_no); sh.write(r, 1, desc); sh.write(r, 2, ".CASH")
        sh.write(r, 3, "%.2f" % net); sh.write(r, 4, "0.00"); sh.write(r, 5, "0.00")
        sh.write(r, 6, "0.00"); sh.write(r, 7, "%.2f" % net); sh.write(r, 8, "%.2f" % net)
        r += 1
        for i, (name, pack, qty, amt) in enumerate(items, 1):
            sh.write(r, 0, ""); sh.write(r, 1, "%d 3 %s %s" % (i, name, pack))
            sh.write(r, 2, qty); sh.write(r, 3, "%.2f 12/27" % amt); sh.write(r, 4, "WB%02d" % i)
            r += 1
        tot += net
    sh.write(r, 2, "DAY TOTAL"); sh.write(r, 3, "%.2f" % tot); sh.write(r, 4, "0.00")
    sh.write(r, 5, "0.00"); sh.write(r, 6, "0.00"); sh.write(r, 7, "%.2f" % tot); sh.write(r, 8, "%.2f" % tot)
    r += 1
    sh.write(r, 1, "Bills: %d" % len(bills)); sh.write(r, 2, "GRAND TOTAL")
    sh.write(r, 3, "%.2f" % tot); sh.write(r, 4, "0.00"); sh.write(r, 5, "0.00")
    sh.write(r, 6, "0.00"); sh.write(r, 7, "%.2f" % tot); sh.write(r, 8, "%.2f" % tot)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def bills_for(n, start=1, day_tag=""):
    out = []
    for k in range(start, start + n):
        out.append(("A%06d" % k, "WALK PATIENT %s%d 1%03d" % (day_tag, k, k), 100.0 * k,
                    [("WALK TAB %d" % k, "1*10", "1:0", 60.0 * k), ("WALK SYP %d" % k, "100ML", "1:0", 40.0 * k)]))
    return out


def build_multipart(file_bytes, filename="REPORT_1.XLS", field="file"):
    """Exactly marg_gate.py's shape (S201 boundary, application/vnd.ms-excel)."""
    boundary = "----margGateS201Boundary7d91c4e2"
    pre = ("--%s\r\nContent-Disposition: form-data; name=\"%s\"; filename=\"%s\"\r\n"
           "Content-Type: application/vnd.ms-excel\r\n\r\n" % (boundary, field, filename)).encode("utf-8")
    post = ("\r\n--%s--\r\n" % boundary).encode("utf-8")
    return pre + file_bytes + post, "multipart/form-data; boundary=%s" % boundary


c = FA.app.test_client()
TOK = {"X-Finance-Marg": "DUMMY-TOKEN-PUT-HERE"}
DOC = {"X-Clinic-User": "zzwalkdoc", "X-Clinic-Role": "doctor"}


def push(blob, name):
    body, ctype = build_multipart(blob, filename=name)
    r = c.post("/finance/api/marg-push", data=body, content_type=ctype, headers=TOK)
    return r.status_code, (r.get_json(silent=True) or {})


def q(sql, *a):
    x = sqlite3.connect(DB)
    x.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in x.execute(sql, a).fetchall()]
    finally:
        x.close()


def q1(sql, *a):
    rows = q(sql, *a)
    return rows[0] if rows else None


def staging(pid):
    return q1("SELECT * FROM marg_push_staging WHERE id=?", pid)


def s243(pid):
    row = staging(pid) or {}
    try:
        return (json.loads(row.get("apply_result_json") or "{}") or {}).get("s243") or {}
    except ValueError:
        return {}


def day_id(iso):
    r = q1("SELECT id FROM day_entry WHERE unit='medical' AND business_date=?", iso)
    return r["id"] if r else None


def n_sale_items(iso):
    d = day_id(iso)
    return q1("SELECT COUNT(*) c FROM sale_item WHERE day_entry_id=?", d)["c"] if d else 0


def n_lines(iso):
    d = day_id(iso)
    return q1("SELECT COUNT(*) c FROM sale_line_item WHERE day_entry_id=?", d)["c"] if d else 0


def audits(pid, action):
    return q("SELECT * FROM audit_log WHERE table_name='marg_push_staging' AND row_id=? AND action=?", pid, action)


def hub_rows():
    j = c.get("/finance/api/marg-push/list", headers=DOC).get_json() or {}
    return dict((p["id"], p) for p in j.get("pushes") or [])


def hub_text(p):
    """The exact expression the patched hub uses for an applied row."""
    return "✓ " + ("applied automatically " if p.get("applied_by") == "auto" else "loaded ") + (p.get("applied_at") or "")[:16]


# =============================================================== 0 · the plumbing
print("\n--- 0 · plumbing")
sc, j = push(b"pushed nonsense", "x.xls")
ck("a file that is not a Marg export is REFUSED whole, as today (422)", sc == 422 and j.get("verdict") == "REFUSED", (sc, j))
ck("the refusal left its data_flag, as today",
   (q1("SELECT COUNT(*) c FROM data_flag WHERE code='MARG_PUSH_REJECTED'") or {}).get("c", 0) >= 1)
sc, j = c.post("/finance/api/marg-push", data={}, headers={"X-Finance-Marg": "guess"}).status_code, None
ck("the wrong token is still refused (401)", sc == 401, sc)

if not PATCHED:
    # ---------------------------------------------------------- the symptom
    print("\n--- U · UNPATCHED file: the symptom the owner met on 13-Sep morning")
    D = "2026-09-12"
    sc, j = push(make_xls("12-09-2026", bills_for(3)), "SALE_BILLWISE_DETAIL__2026-09-12__walk__u1.xls")
    pid = j.get("id")
    ck("push of a NOT-filed day is ACCEPTED-FOR-REVIEW only", j.get("verdict") == "ACCEPTED-FOR-REVIEW", j)
    ck("...and the row sits PENDING", (staging(pid) or {}).get("status") == "pending")
    ck("...the day is not filed (no day_entry) -- '(day not filed)' on the hub", day_id(D) is None)
    ck("...nothing in the books", n_sale_items(D) == 0 and n_lines(D) == 0)
    print("RESULT (unpatched): %d passed, %d failed -- the symptom is reproduced" % (len(PASSED), len(FAILED)))
    shutil.rmtree(TMP, ignore_errors=True)
    sys.exit(1 if FAILED else 0)

# =============================================================== 1 · at once
print("\n--- 1 · a VERIFIED sale report for a NOT-filed day applies AT ONCE")
D1 = "2026-09-12"
F1 = make_xls("12-09-2026", bills_for(3))
sc, j = push(F1, "SALE_BILLWISE_DETAIL__2026-09-12__20260912-2301__f1.xls")
p1 = j.get("id")
ck("HTTP 200, verdict APPLIED", sc == 200 and j.get("verdict") == "APPLIED", (sc, j.get("verdict"), j.get("message")))
ck("the message says applied automatically", "Applied automatically" in (j.get("message") or ""), j.get("message"))
row = staging(p1) or {}
ck("staging row status='applied'", row.get("status") == "applied", row.get("status"))
ck("staging row applied_by='auto'", row.get("applied_by") == "auto", row.get("applied_by"))
ck("staging row records the S243 rule and per-day facts",
   s243(p1).get("rule", "").startswith("S243") and s243(p1).get("days", {}).get(D1, {}).get("bills") == 3, s243(p1))
ck("the day was FILED by the apply (D354 autofile), entered_by auto",
   day_id(D1) is not None and (q1("SELECT entered_by FROM day_entry WHERE id=?", day_id(D1)) or {}).get("entered_by") == "auto",
   q1("SELECT * FROM day_entry WHERE unit='medical' AND business_date=?", D1))
ck("sale_item holds the 3 bills", n_sale_items(D1) == 3, n_sale_items(D1))
ck("sale_line_item holds the 6 drug lines", n_lines(D1) == 6, n_lines(D1))
ck("audit_log: 'auto-apply' by 'auto' naming the rule",
   any(a["by_whom"] == "auto" and "S243" in (a["after_json"] or "") for a in audits(p1, "auto-apply")), audits(p1, "auto-apply"))
ck("audit_log: the checker-path 'apply' row is also by 'auto'",
   any(a["by_whom"] == "auto" for a in audits(p1, "apply")), audits(p1, "apply"))
ck("the MARG_DAY_NOT_FILED flag written at push time is cleared",
   (q1("SELECT COUNT(*) c FROM data_flag WHERE code='MARG_DAY_NOT_FILED' AND business_date=?", D1) or {}).get("c") == 0)
h = hub_rows().get(p1) or {}
ck("hub list: applied_by auto, auto.rule present", h.get("applied_by") == "auto" and (h.get("auto") or {}).get("rule", "").startswith("S243"), h)
ck("hub card text reads '✓ applied automatically <time>'",
   hub_text(h).startswith("✓ applied automatically 20"), hub_text(h))
ck("hub list: the day reads FILED now (S210 F-249 re-answers it)",
   all(d.get("filed") for d in (h.get("survey") or {}).get("survey") or []), h.get("survey"))

# =============================================================== 2 · older than applied
print("\n--- 2 · a SECOND push for the same day with FEWER bills is put aside")
F2 = make_xls("12-09-2026", bills_for(2))
sc, j = push(F2, "SALE_BILLWISE_DETAIL__2026-09-12__20260912-1751__f2.xls")
p2 = j.get("id")
ck("HTTP 200, verdict SUPERSEDED", sc == 200 and j.get("verdict") == "SUPERSEDED", (sc, j))
row = staging(p2) or {}
ck("status='superseded' (the table's own word; 'dismissed' is refused by its CHECK)", row.get("status") == "superseded", row.get("status"))
ck("applied_by='auto', rule 'older than applied'", row.get("applied_by") == "auto" and s243(p2).get("rule") == "older than applied", s243(p2))
ck("its replay payload is cleared (can never be replayed by the day-save)", row.get("parsed_json") is None)
ck("audit_log 'auto-dismiss' by auto", any(a["by_whom"] == "auto" for a in audits(p2, "auto-dismiss")))
ck("the books are untouched: still 3 bills, 6 lines", n_sale_items(D1) == 3 and n_lines(D1) == 6)
ck("the first push stays APPLIED", (staging(p1) or {}).get("status") == "applied")
h = hub_rows().get(p2) or {}
ck("hub list carries the rule for the superseded row", (h.get("auto") or {}).get("rule") == "older than applied", h)
ck("the SAME bytes again -> ALREADY-RECEIVED, as today", push(F2, "again.xls")[1].get("verdict") == "ALREADY-RECEIVED")

# =============================================================== 3 · fuller export
print("\n--- 3 · a LATER, FULLER export for the same day (4 bills) is applied over it")
F3 = make_xls("12-09-2026", bills_for(4))
sc, j = push(F3, "SALE_BILLWISE_DETAIL__2026-09-12__20260913-0900__f3.xls")
p3 = j.get("id")
ck("verdict APPLIED", j.get("verdict") == "APPLIED", j)
ck("the day now holds 4 bills and 8 lines (replaced, not duplicated)", n_sale_items(D1) == 4 and n_lines(D1) == 8, (n_sale_items(D1), n_lines(D1)))
ck("one live ingest_batch for the day; the earlier one is 'superseded' (ingest_day rule)",
   (q1("SELECT COUNT(*) c FROM ingest_batch WHERE day_entry_id=? AND status IN ('ok','partial')", day_id(D1)) or {}).get("c") == 1
   and (q1("SELECT COUNT(*) c FROM ingest_batch WHERE day_entry_id=? AND status='superseded'", day_id(D1)) or {}).get("c") >= 1)
ck("F1 stays APPLIED (it truly was; history is not rewritten)", (staging(p1) or {}).get("status") == "applied")
ck("F3 applied_by auto, facts say 4 bills, last bill 4",
   (staging(p3) or {}).get("applied_by") == "auto" and s243(p3).get("days", {}).get(D1, {}).get("last_bill") == 4, s243(p3))
F3b = make_xls("12-09-2026", bills_for(3, start=2))     # same COUNT as an older state, later bill number
sc, j = push(F3b, "SALE_BILLWISE_DETAIL__2026-09-12__20260913-0930__f3b.xls")
ck("same-count re-export with NO later bill than applied (A2..A4 vs A1..A4) is put aside", j.get("verdict") == "SUPERSEDED", j.get("verdict"))
F3c = make_xls("12-09-2026", bills_for(4, start=2))     # 4 bills, last A5 > A4
sc, j = push(F3c, "SALE_BILLWISE_DETAIL__2026-09-12__20260913-0940__f3c.xls")
ck("same-count export whose LAST bill is later (A5) is applied", j.get("verdict") == "APPLIED", j.get("verdict"))
edited = bills_for(4, start=2)
edited[1] = (edited[1][0], edited[1][1], edited[1][2] + 10.0, edited[1][3])     # one bill corrected in Marg
F3d = make_xls("12-09-2026", edited)
sc, j = push(F3d, "SALE_BILLWISE_DETAIL__2026-09-12__20260913-0950__f3d.xls")
ck("same bills, one amount corrected (net differs from the recorded apply) -> applied, newest wins", j.get("verdict") == "APPLIED", j.get("verdict"))
edited2 = bills_for(4, start=2)
edited2[2] = (edited2[2][0], edited2[2][1], edited2[2][2] + 5.0, edited2[2][3])
sc, j = push(make_xls("12-09-2026", edited2), "SALE_BILLWISE_DETAIL__2026-09-12__20260913-0955__f3e.xls")
ck("same count, same last bill, DIFFERENT net again -> applied (arrival order is the tie-break: newest wins)", j.get("verdict") == "APPLIED", j.get("verdict"))
ck("...the day's net follows the latest export", (q1("SELECT total_p FROM ingest_batch WHERE day_entry_id=? AND status IN ('ok','partial')", day_id(D1)) or {}).get("total_p") == 140500, q1("SELECT total_p FROM ingest_batch WHERE day_entry_id=? AND status IN ('ok','partial')", day_id(D1)))
fewer = bills_for(3, start=2)
fewer[0] = (fewer[0][0], fewer[0][1], fewer[0][2] + 7.0, fewer[0][3])
sc, j = push(make_xls("12-09-2026", fewer), "SALE_BILLWISE_DETAIL__2026-09-12__20260913-0956__f3f.xls")
ck("...fewer bills with a different net is still put aside (the net rule only ranks the SAME bill set)", j.get("verdict") == "SUPERSEDED", j.get("verdict"))

# =============================================================== 4 · OFF switch
print("\n--- 4 · the OFF file: behaves exactly as today; the manual Apply still works")
open(OFF, "w").write("off\n")
D2 = "2026-09-11"
F4 = make_xls("11-09-2026", bills_for(2, start=101, day_tag="B"))
sc, j = push(F4, "SALE_BILLWISE_DETAIL__2026-09-11__20260911-2220__f4.xls")
p4 = j.get("id")
ck("with the OFF file, a not-filed day's push is ACCEPTED-FOR-REVIEW only", j.get("verdict") == "ACCEPTED-FOR-REVIEW", j)
ck("...the message says NOTHING entered the books (today's words)", "NOTHING" in (j.get("message") or ""), j.get("message"))
ck("...row PENDING, nothing in the books, no day filed", (staging(p4) or {}).get("status") == "pending" and day_id(D2) is None)
ck("...no automatic audit row was written", not audits(p4, "auto-apply") and not audits(p4, "auto-dismiss"))
r = c.post("/finance/api/marg-push/apply", json={"id": p4}, headers=DOC)
jj = r.get_json() or {}
ck("the checker's Apply button works unchanged (ok, day ingested)", r.status_code == 200 and jj.get("ok") and jj.get("ingested"), (r.status_code, jj))
ck("...status applied, applied_by = the checker (not auto)",
   (staging(p4) or {}).get("status") == "applied" and (staging(p4) or {}).get("applied_by") == "zzwalkdoc", staging(p4))
ck("...hub card text for a hand apply still reads '✓ loaded <time>'", hub_text(hub_rows().get(p4) or {}).startswith("✓ loaded 20"))
ck("...2 bills, 4 lines in the books", n_sale_items(D2) == 2 and n_lines(D2) == 4)
r = c.post("/finance/api/marg-push/apply", json={"id": p4}, headers=DOC)
ck("Apply on a non-pending row is refused 409, as today", r.status_code == 409)
r = c.post("/finance/api/marg-push/apply", json={"id": p4})
ck("Apply without a checker login is refused", r.status_code in (401, 403, 302), r.status_code)
os.remove(OFF)

# =============================================================== 5 · supersede an older pending
print("\n--- 5 · an OLDER push for the same day still pending is superseded when the newer applies")
open(OFF, "w").write("off\n")
D3 = "2026-09-10"
F5 = make_xls("10-09-2026", bills_for(2, start=201, day_tag="C"))
sc, j = push(F5, "SALE_BILLWISE_DETAIL__2026-09-10__20260910-1751__f5.xls")
p5 = j.get("id")
ck("(OFF) the older push is pending", (staging(p5) or {}).get("status") == "pending")
os.remove(OFF)
F6 = make_xls("10-09-2026", bills_for(3, start=201, day_tag="C"))
sc, j = push(F6, "SALE_BILLWISE_DETAIL__2026-09-10__20260910-2220__f6.xls")
p6 = j.get("id")
md5_8 = (staging(p6) or {}).get("file_md5", "")[:8]
ck("the newer push is APPLIED", j.get("verdict") == "APPLIED", j)
ck("the older one is now 'superseded' with rule 'superseded by <md5-8>'",
   (staging(p5) or {}).get("status") == "superseded" and s243(p5).get("rule") == "superseded by %s" % md5_8, s243(p5))
ck("...its audit row 'auto-dismiss' by auto exists", any(a["by_whom"] == "auto" for a in audits(p5, "auto-dismiss")))
ck("...the response names it", any(s.get("id") == p5 for s in (j.get("auto") or {}).get("superseded") or []), j.get("auto"))
ck("the day holds the newer export: 3 bills", n_sale_items(D3) == 3)
if HAS_DISMISS:
    open(OFF, "w").write("off\n")
    F7 = make_xls("09-09-2026", bills_for(1, start=301, day_tag="D"))
    sc, j = push(F7, "SALE_BILLWISE_DETAIL__2026-09-09__f7.xls")
    p7 = j.get("id")
    os.remove(OFF)
    r = c.post("/finance/api/marg-push/dismiss", json={"id": p7, "reason": "walk: owner's Remove"}, headers=DOC)
    ck("the owner's Remove button works unchanged (S211: status 'rejected')",
       r.status_code == 200 and (staging(p7) or {}).get("status") == "rejected", (r.status_code, staging(p7)))

# =============================================================== 6 · already filed
print("\n--- 6 · a day already FILED by hand: the push applies at once (the S219 order, now by S243)")
D4 = "2026-09-08"
x = sqlite3.connect(DB)
x.execute("INSERT INTO day_entry (unit, business_date, status, source, entered_by, entered_at) VALUES "
          "('medical', ?, 'submitted', 'app', 'zzwalkmaker', '2026-09-08T21:00:00')", (D4,))
x.commit(); x.close()
F8 = make_xls("08-09-2026", bills_for(2, start=401, day_tag="E"))
sc, j = push(F8, "SALE_BILLWISE_DETAIL__2026-09-08__f8.xls")
p8 = j.get("id")
ck("verdict APPLIED", j.get("verdict") == "APPLIED", j)
ck("applied_by auto; 2 bills in the books", (staging(p8) or {}).get("applied_by") == "auto" and n_sale_items(D4) == 2)
if HAS_S219:
    ck("the S219 apply summary line rides along (one rule, D349)",
       any("bills" in s for s in (j.get("auto") or {}).get("summary") or []), j.get("auto"))

# =============================================================== 7 · two-day report
print("\n--- 7 · a two-day report: one day already fully held, one new -> applied (the new day is what it brings)")
x = sqlite3.connect(DB); x.close()
import xlwt                                                  # noqa: E402


def make_xls_2day(d_a, bills_a, d_b, bills_b):
    wb = xlwt.Workbook(); sh = wb.add_sheet("Sheet1"); r = 0
    sh.write(r, 0, "BILL WISE SALES STATEMENT FROM %s TO %s" % (d_a, d_b)); r += 1
    for cc, hh in enumerate(["BILL NO.", "DESCRIPTION", "D.R.", "GROSS AMT.", "DISCOUNT", "TAX", "DR/CR", "NET AMT.", "CASH"]):
        sh.write(r, cc, hh)
    r += 1
    grand = 0
    for dd, bb in ((d_a, bills_a), (d_b, bills_b)):
        sh.write(r, 0, dd); r += 1
        tot = 0
        for bill_no, desc, net, items in bb:
            sh.write(r, 0, bill_no); sh.write(r, 1, desc); sh.write(r, 2, ".CASH")
            for cc in (3, 7, 8):
                sh.write(r, cc, "%.2f" % net)
            for cc in (4, 5, 6):
                sh.write(r, cc, "0.00")
            r += 1
            for i, (name, pack, qty, amt) in enumerate(items, 1):
                sh.write(r, 1, "%d 3 %s %s" % (i, name, pack)); sh.write(r, 2, qty); sh.write(r, 3, "%.2f 12/27" % amt); r += 1
            tot += net
        sh.write(r, 2, "DAY TOTAL")
        for cc in (3, 7, 8):
            sh.write(r, cc, "%.2f" % tot)
        for cc in (4, 5, 6):
            sh.write(r, cc, "0.00")
        r += 1
        grand += tot
    sh.write(r, 1, "Bills: %d" % (len(bills_a) + len(bills_b))); sh.write(r, 2, "GRAND TOTAL")
    for cc in (3, 7, 8):
        sh.write(r, cc, "%.2f" % grand)
    for cc in (4, 5, 6):
        sh.write(r, cc, "0.00")
    buf = io.BytesIO(); wb.save(buf); return buf.getvalue()


D5 = "2026-09-07"
F9 = make_xls_2day("10-09-2026", bills_for(3, start=201, day_tag="C"), "07-09-2026", bills_for(2, start=501, day_tag="F"))
sc, j = push(F9, "SALE_BILLWISE_DETAIL__2026-09-07__2026-09-10__f9.xls")
ck("verdict APPLIED (D3 held equal, D5 new)", j.get("verdict") == "APPLIED", j)
ck("D5 filed and holding 2 bills; D3 still 3", n_sale_items(D5) == 2 and n_sale_items(D3) == 3, (n_sale_items(D5), n_sale_items(D3)))
F10 = make_xls_2day("10-09-2026", bills_for(3, start=201, day_tag="C"), "07-09-2026", bills_for(2, start=501, day_tag="F"))
ck("the identical bytes again -> ALREADY-RECEIVED", push(F10, "f10.xls")[1].get("verdict") == "ALREADY-RECEIVED")

# =============================================================== 8 · nothing else moved
print("\n--- 8 · the rest of the surface")
ck("every applied day still holds its drug lines at the end (bill numbers are unique across days, as in Marg)",
   dict((r["business_date"], r["c"]) for r in q("SELECT business_date, COUNT(*) c FROM sale_line_item GROUP BY business_date"))
   == {D1: 8, D2: 4, D3: 6, D4: 4, D5: 4},
   q("SELECT business_date, COUNT(*) c FROM sale_line_item GROUP BY business_date"))
ck("the two MARG_DAY_NOT_FILED flags left are the hand-applied day (unchanged path) and the removed, never-filed day",
   sorted(r["business_date"] for r in q("SELECT business_date FROM data_flag WHERE code='MARG_DAY_NOT_FILED'")) == ["2026-09-09", D2],
   q("SELECT business_date FROM data_flag WHERE code='MARG_DAY_NOT_FILED'"))
ck("healthz answers 200", c.get("/finance/healthz").status_code == 200)
ck("the list route is still checker-only", c.get("/finance/api/marg-push/list").status_code in (401, 403, 302))
ck("no audit row by 'auto' names a phone-shaped number",
   not any(__import__("re").search(r"\d{10}", a["after_json"] or "") for a in q("SELECT after_json FROM audit_log WHERE by_whom='auto'")))
import py_compile                                            # noqa: E402
try:
    py_compile.compile(FIN_APP, doraise=True)
    ck("py_compile of the file under test", True)
except Exception as ex:                                      # noqa: BLE001
    ck("py_compile of the file under test", False, ex)

print("\nRESULT: %d passed, %d failed" % (len(PASSED), len(FAILED)))
for f in FAILED:
    print("  FAILED:", f)
if os.environ.get("KEEP_TMP"):
    print("KEEP_TMP set: leaving %s in place" % TMP)
else:
    shutil.rmtree(TMP, ignore_errors=True)
sys.exit(1 if FAILED else 0)
