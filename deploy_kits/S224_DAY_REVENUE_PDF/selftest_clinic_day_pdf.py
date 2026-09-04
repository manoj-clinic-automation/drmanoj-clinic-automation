#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""selftest_clinic_day_pdf.py -- the real blueprint on a real Flask app over a temp finance.db
seeded with a synthetic day, every page fetched over HTTP, assertions on the delivered bytes.

The tables are created with the DDL of docterz_ingest.py as built at S223_SPLIT_LEGS
(clinic_day_revenue, clinic_day_line, clinic_day_tender); the S223 kits seeded their tests by
running the real ingester over real Day Revenue workbooks, which the repository cannot hold
(F-185). Every name and ID here is invented and shaped so no test can mistake it for a person.

    python3 -B selftest_clinic_day_pdf.py
"""
import json, os, re, sqlite3, sys, tempfile, urllib.parse
def urllib_q(s):
    return urllib.parse.quote(s, safe="")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flask import Flask, jsonify
import clinic_day_pdf as CP

F, N = [], []
def ck(l, c, d=""):
    N.append(l)
    print("  %s  %s%s" % ("PASS" if c else "FAIL", l, ("   [%s]" % d) if d and not c else ""))
    if not c: F.append(l)

DDL = """
CREATE TABLE IF NOT EXISTS clinic_day_revenue (
  business_date TEXT PRIMARY KEY, source_file TEXT NOT NULL, source_id TEXT NOT NULL,
  source_mtime TEXT NOT NULL, taken_at TEXT NOT NULL,
  cons_count INTEGER NOT NULL, cons_amount_p INTEGER NOT NULL,
  xray_count INTEGER NOT NULL, xray_amount_p INTEGER NOT NULL,
  proc_count INTEGER NOT NULL, proc_amount_p INTEGER NOT NULL,
  total_count INTEGER NOT NULL, total_amount_p INTEGER NOT NULL,
  morning INTEGER, evening INTEGER, free_revisits INTEGER NOT NULL, free_concession INTEGER NOT NULL,
  f93_phantom_rows INTEGER NOT NULL, tender_json TEXT NOT NULL,
  sheet_total_p INTEGER, sheet_cash_p INTEGER, sheet_online_p INTEGER,
  variance_note TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS clinic_day_line (
  business_date TEXT NOT NULL, section TEXT NOT NULL, sn INTEGER NOT NULL,
  patient TEXT NOT NULL DEFAULT '', clinic_id TEXT NOT NULL DEFAULT '',
  amount_p INTEGER NOT NULL DEFAULT 0, mode TEXT NOT NULL DEFAULT '', shift TEXT NOT NULL DEFAULT '',
  PRIMARY KEY (business_date, section, sn));
CREATE TABLE IF NOT EXISTS clinic_day_tender (
  business_date TEXT NOT NULL, clinic_id TEXT NOT NULL DEFAULT '', invoice_no TEXT NOT NULL DEFAULT '',
  tender TEXT NOT NULL, amount_p INTEGER NOT NULL, source_file TEXT NOT NULL DEFAULT '');
"""

DAY = "2026-09-03"
# invented: 21 consults of Rs 500, 6 X-rays of Rs 300, 2 procedures, 3 free revisits, 1 concession
LINES = []
for i in range(1, 22):
    LINES.append((DAY, "consult", i, "Test Patient %02d" % i, "T-%03d" % i, 50000,
                  "Cash" if i % 3 else "Online Payment", "morning" if i <= 12 else "evening"))
for i in range(1, 7):
    LINES.append((DAY, "xray", i, "Test Patient %02d" % (i * 3), "T-%03d" % (i * 3), 30000,
                  "Split Payment" if i == 2 else "Cash", "morning"))
LINES.append((DAY, "proc", 1, "Test Patient 05", "T-005", 150000, "Debit Card", "evening"))
LINES.append((DAY, "proc", 2, "Test Patient 40", "T-040", 275000, "Online Payment", "evening"))
for i in range(1, 4):
    LINES.append((DAY, "revisit", i, "Test Revisit %d" % i, "T-%03d" % (60 + i), 0, "", "morning"))
LINES.append((DAY, "concession", 1, "Test Concession 1", "", 0, "", "evening"))
CONS = 21 * 50000; XR = 6 * 30000; PR = 150000 + 275000; TOT = CONS + XR + PR
TENDER = {"Cash": 14 * 50000 + 5 * 30000, "Online Payment": 7 * 50000 + 275000,
          "Debit Card": 150000, "Split Payment": 30000}
assert sum(TENDER.values()) == TOT

def seed(path, with_lines=True, with_tenders=True):
    c = sqlite3.connect(path)
    c.executescript(DDL)
    c.execute("INSERT INTO clinic_day_revenue VALUES (?,?,?,?,?, ?,?, ?,?, ?,?, ?,?, ?,?, ?,?, ?, ?, ?,?,?, ?)",
              (DAY, "Staff_Action_Today_x.xlsx", "id", "2026-09-04T00:00:00Z", "2026-09-04T01:00:00",
               21, CONS, 6, XR, 2, PR, 29, TOT, 19, 10, 3, 1, 0, json.dumps(TENDER),
               TOT + 100000, None, None, "sheet total differs by 1,000"))
    if with_lines:
        c.executemany("INSERT INTO clinic_day_line VALUES (?,?,?,?,?,?,?,?)", LINES)
    if with_tenders:
        c.executemany("INSERT INTO clinic_day_tender VALUES (?,?,?,?,?,?)", [
            (DAY, "T-006", "INV-77", "Wallet", 18000, "Day_Tenders.csv"),
            (DAY, "T-006", "INV-77", "Online Payment", 12000, "Day_Tenders.csv")])
    c.commit(); c.close()

TMP = tempfile.mkdtemp(prefix="s224pdf_")
DBP = os.path.join(TMP, "finance.db")
seed(DBP)
ROLE = {"who": "checker"}
def _db():
    c = sqlite3.connect(DBP); c.row_factory = sqlite3.Row; return c
app = Flask(__name__)
def _require(*roles, unit="clinic"):
    if ROLE["who"] in roles:
        return {"user": "testdoc", "roles": [ROLE["who"]]}, None
    with app.app_context():
        return None, (jsonify(ok=False, error="not_permitted"), 403)
CP.init(app, _db, _require, unit="clinic", url_prefix="")
cl = app.test_client()

def pdf_text(b):
    """Every (...) string of every Tj in the uncompressed streams, unescaped."""
    out = []
    for m in re.finditer(rb"\((.*?)(?<!\\)\) Tj", b, re.S):
        out.append(m.group(1).replace(b"\\(", b"(").replace(b"\\)", b")").replace(b"\\\\", b"\\"))
    return b"\n".join(out).decode("cp1252", "replace")

print("-- 1  the PDF ------------------------------------------------------------")
r = cl.get("/finance/clinic/day/%s/pdf" % DAY)
ck("HTTP 200 for the clinic checker", r.status_code == 200, str(r.status_code))
b = r.data
ck("it is a PDF: starts with %PDF-1.4", b.startswith(b"%PDF-1.4"))
ck("it ends with %%EOF", b.rstrip().endswith(b"%%EOF"))
ck("Content-Type application/pdf", r.mimetype == "application/pdf")
ck("inline by default, named Docterz_Revenue_<date>.pdf",
   r.headers.get("Content-Disposition") == 'inline; filename="Docterz_Revenue_%s.pdf"' % DAY)
ck("Content-Length is the body", r.headers.get("Content-Length") == str(len(b)))
npages = int(re.search(rb"/Count (\d+)", b).group(1))
ck("at least one page (Count %d)" % npages, npages >= 1)
ck("every page object is there", len(re.findall(rb"/Type /Page\b", b)) == npages)
ck("xref offsets are exact", all(
    b[int(o):int(o) + 12].startswith(b"%d 0 obj" % (i + 1))
    for i, o in enumerate(re.findall(rb"\n(\d{10}) 00000 n", b))))
ck("startxref points at the xref table",
   b[int(re.search(rb"startxref\n(\d+)", b).group(1)):].startswith(b"xref"))
txt = pdf_text(b)
ck("the date is in the text (03-Sep-2026)", "03-Sep-2026" in txt)
ck("the total is in the text, Indian grouping (Rs %s)" % CP._inr(TOT), "Rs " + CP._inr(TOT) in txt)
ck("the three heads carry their amounts", all(
    "Rs " + CP._inr(x) in txt for x in (CONS, XR, PR)))
ck("all five sections are titled, in the page's order",
   [t for _, t in CP.SECTIONS] == [t for t in [x for _, x in CP.SECTIONS] if t in txt]
   and txt.index("PAID CONSULTATIONS") < txt.index("X-RAY") < txt.index("PROCEDURES")
   < txt.index("FREE REVISITS") < txt.index("FREE / CONCESSION"))
ck("every line's patient and clinic ID are on the sheet",
   all(l[3] in txt and (l[4] in txt or not l[4]) for l in LINES))
ck("a line with no clinic ID prints a dash, not a blank", "Test Concession 1" in txt)
ck("subtotals: consult, x-ray, proc", all("Rs " + CP._inr(x) in txt for x in (CONS, XR, PR)))
PEOPLE = len({l[4] for l in LINES if l[4]}) + sum(1 for l in LINES if not l[4])
ck("people seen = distinct IDs + anonymous (%d)" % PEOPLE, "%d people seen" % PEOPLE in txt)
ck("the tender line: Cash / Online / Card / Split, from tender_json",
   all(s in txt for s in ("Cash Rs 8,500", "Online Rs 6,250", "Card Rs 1,500", "Split Rs 300")))
ck("the split legs block is on the sheet", "SPLIT PAYMENTS" in txt and "INV-77" in txt
   and "Wallet Rs 180" in txt and "Online Payment Rs 120" in txt)
ck("D367: the sheet's own (differing) total is nowhere", CP._inr(TOT + 100000) not in txt
   and "variance" not in txt.lower())
ck("the rupee sign is not used (core fonts have no glyph)", "₹" not in txt and b"\xe2\x82\xb9" not in b)
ck("no 10-digit run in the PDF's text (the xref table's 10-digit offsets are structure, not text)",
   not re.search(r"\d{10}", txt))
ck("no Docterz UID shape in the text", not re.search(r"\b[A-Z]{5}\d{5}\b", txt))
ck("Page 1 of N is printed", "Page 1 of %d" % npages in txt)
ck("the maker's name is on the foot line", "by testdoc" in txt)

print("\n-- 2  dl=1, the .pdf alias, the gate ----------------------------------------")
r = cl.get("/finance/clinic/day/%s/pdf?dl=1" % DAY)
ck("?dl=1 -> attachment", r.headers.get("Content-Disposition", "").startswith("attachment;"))
r2 = cl.get("/finance/clinic/day/%s.pdf" % DAY)
ck("/day/<date>.pdf serves the same PDF", r2.status_code == 200 and r2.mimetype == "application/pdf")
ROLE["who"] = "maker"
ck("a clinic MAKER gets 403 on the PDF", cl.get("/finance/clinic/day/%s/pdf" % DAY).status_code == 403)
ROLE["who"] = "viewer"
r = cl.get("/finance/clinic/day/%s/pdf" % DAY)
ck("a viewer gets 403 on the PDF", r.status_code == 403)
ck("the refusal carries no PDF and no figure", not r.data.startswith(b"%PDF") and b"Rs " not in r.data)
r = cl.get("/finance/clinic/day/%s/share" % DAY)
ck("a viewer gets 403 on the share page, in words", r.status_code == 403 and b"Not permitted" in r.data)
ck("the refusal leaks no money", not re.search(rb"\d{1,3},\d{2,3}", r.data))
ROLE["who"] = "checker"
ck("a malformed date -> 404, not a stack trace", cl.get("/finance/clinic/day/2026-13-99/pdf").status_code == 404)
ck("a valid date with no day -> 404 in words",
   cl.get("/finance/clinic/day/2019-01-01/pdf").status_code == 404)
ck("a date shaped 2026-9-3 is refused (must be yyyy-mm-dd)", cl.get("/finance/clinic/day/2026-9-3/pdf").status_code == 404)

print("\n-- 3  the share page ---------------------------------------------------------")
r = cl.get("/finance/clinic/day/%s/share" % DAY)
h = r.get_data(as_text=True)
ck("HTTP 200, a complete HTML document", r.status_code == 200 and h.startswith("<!doctype html")
   and h.rstrip().endswith("</html>"))
ck("mobile viewport", 'name="viewport"' in h)
ck("'Share PDF on WhatsApp' button", 'id="share"' in h and "Share PDF on WhatsApp" in h)
ck("'Download PDF' link to ?dl=1", 'href="/finance/clinic/day/%s/pdf?dl=1"' % DAY in h and "Download PDF" in h)
ck("the JS uses navigator.share with files, and canShare first",
   "navigator.share(" in h and "navigator.canShare(" in h and "files:[f]" in h)
ck("the PDF is fetched with the session cookie", "credentials:'same-origin'" in h)
ck("the fallback: wa.me text link with the numbers, no file", "https://wa.me/?text=" in h
   and urllib_q("Rs " + CP._inr(TOT)) in h)
ck("the fallback wa.me text names the PDF's absolute URL", urllib_q("/finance/clinic/day/%s/pdf" % DAY) in h)
ck("the day's total and heads are on the page", "Rs " + CP._inr(TOT) in h and "Rs " + CP._inr(PR) in h)
ck("a date picker, defaulting to this date, posting to /finance/clinic/share",
   'type="date"' in h and 'value="%s"' % DAY in h and 'action="/finance/clinic/share"' in h)
ck("a link back to the A4 page", 'href="/finance/clinic/day/%s"' % DAY in h)
ck("no patient name on the share page (only the PDF carries them)", "Test Patient" not in h)
ck("no 10-digit run on the share page", not re.search(r"\d{10}", h))
r = cl.get("/finance/clinic/day/2019-01-01/share")
h = r.get_data(as_text=True)
ck("a date with no day says so and points at the newest day",
   "No day was read" in h and "/finance/clinic/day/%s/share" % DAY in h)
ck("a malformed date on the share page -> 404 with the picker",
   cl.get("/finance/clinic/day/nonsense/share").status_code == 404)

print("\n-- 4  the bookmark ---------------------------------------------------------------")
import datetime as dt
y = (dt.date.today() - dt.timedelta(days=1)).isoformat()
r = cl.get("/finance/clinic/share")
ck("/finance/clinic/share -> 302 to yesterday's share page",
   r.status_code == 302 and r.headers["Location"].endswith("/finance/clinic/day/%s/share" % y))
r = cl.get("/finance/clinic/share?d=%s" % DAY)
ck("?d=<date> -> that day's share page", r.status_code == 302
   and r.headers["Location"].endswith("/finance/clinic/day/%s/share" % DAY))
r = cl.get("/finance/clinic/share?d=garbage")
ck("a bad ?d falls back to yesterday", r.status_code == 302 and y in r.headers["Location"])

print("\n-- 5  a day with totals but no lines, no tender table; no table at all --------------")
DB2 = os.path.join(TMP, "bare.db"); seed(DB2, with_lines=False, with_tenders=False)
def _db2():
    c = sqlite3.connect(DB2); c.row_factory = sqlite3.Row; return c
CP._db = _db2
r = cl.get("/finance/clinic/day/%s/pdf" % DAY)
t2 = pdf_text(r.data)
ck("still a PDF, with the totals and the 'no entries' note",
   r.status_code == 200 and "Rs " + CP._inr(TOT) in t2 and "No entries were stored" in t2)
DB3 = os.path.join(TMP, "empty.db"); sqlite3.connect(DB3).close()
def _db3():
    c = sqlite3.connect(DB3); c.row_factory = sqlite3.Row; return c
CP._db = _db3
ck("with no clinic_day_revenue table at all: 404, not a 500",
   cl.get("/finance/clinic/day/%s/pdf" % DAY).status_code == 404)
ck("share page with no table: 'No day has been read yet'",
   "No day has been read yet" in cl.get("/finance/clinic/day/%s/share" % DAY).get_data(as_text=True))
CP._db = _db

print("\n-- 6  the writer's own edges ------------------------------------------------------")
ck("Indian grouping", [CP._inr(x) for x in (0, 99900, 100000, 12345600, 1234567800, -50000)]
   == ["0", "999", "1,000", "1,23,456", "1,23,45,678", "-500"])
ck("None -> dash", CP._inr(None) == "-")
ck("typographic characters fold to WinAnsi-safe text",
   CP._latin(u"₹ 5 — café ’x’") == "Rs  5 - café 'x'")
ck("parentheses and backslashes are escaped in strings",
   CP._PDF._pdfstr("a(b)c\\d") == b"a\\(b\\)c\\\\d")
big = os.path.join(TMP, "big.db"); seed(big, with_lines=False)
c = sqlite3.connect(big)
c.executemany("INSERT INTO clinic_day_line VALUES (?,?,?,?,?,?,?,?)", [
    (DAY, "consult", i, "Long Name Test Patient Number %03d With A Very Long Surname Indeed" % i,
     "T-%03d" % i, 50000, "Cash", "morning") for i in range(1, 140)])
c.commit(); c.close()
def _dbb():
    cc = sqlite3.connect(big); cc.row_factory = sqlite3.Row; return cc
CP._db = _dbb
r = cl.get("/finance/clinic/day/%s/pdf" % DAY)
nb = int(re.search(rb"/Count (\d+)", r.data).group(1))
tb = pdf_text(r.data)
ck("139 lines paginate onto %d pages with the header repeated" % nb, nb >= 3
   and tb.count("PAID CONSULTATIONS (continued)") == nb - 1 and "Page %d of %d" % (nb, nb) in tb)
ck("over-long names are trimmed with an ellipsis, never overrun the column", "..." in tb)
CP._db = _db

print("\n%s  %d checks, %d failed" % ("RED" if F else "GREEN", len(N), len(F)))
for f in F:
    print("  FAILED: " + f)
sys.exit(1 if F else 0)
