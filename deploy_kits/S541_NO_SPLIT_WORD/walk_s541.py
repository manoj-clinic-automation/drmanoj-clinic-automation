#!/usr/bin/env python3
"""walk_s541.py -- kit S541 (session 313, 13-Oct-2026; D718; F-869). READ-ONLY.
    python3 -B walk_s541.py <folder holding finance_clinic_day.py, clinic_day_pdf.py, packs.py>
                            [--db <a COPY of finance.db> --from 2026-09-01] [--expect-red] [--preview <date> <out.html> <out.pdf>]
Part A: a made-up day in memory (no person, no number): a one-to-one bill, a grouped bill, a bill with one item in two parts,
a bill with no parts, a booked visit whose procedure line carries the Razorpay number (F-869), plain lines. It holds the day
page, the month table, the PDF and the accountants' income sheet to D718: no 'split' anywhere, each line as it was paid, the
day's total unchanged. --expect-red runs Part A on the OLD files: it must fail (the negative control).
Part B (--db): every day from --from on a copy of the real database: the day's total by mode equal to the old page's (cash +
online + card + other + not known = old cash + online + card + split + other), every day's online figure unchanged, every
'Split Payment' line given words, no 'split' in any day page, month table or PDF; and the bills counted by kind.
Prints 'WALK OK ...' on success; exit 1 on any failure."""
import ast
import importlib.util
import io
import os
import re
import sqlite3
import sys
import types
import zipfile

FAILS = []
RUN = [0]
NAMES = ("finance_clinic_day", "clinic_day_pdf", "packs", "clinic_money")


def split_strings(path):
    """Every string a person could read (not a docstring, not an identifier-like key, not Docterz's own mode word
    'Split Payment' that the code must still recognise) that says 'split'."""
    tree = ast.parse(open(path, encoding="utf-8").read())
    docs = set(id(n.value) for n in ast.walk(tree)
               if isinstance(n, ast.Expr) and isinstance(getattr(n, "value", None), ast.Constant) and isinstance(n.value.value, str))
    bad = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs:
            v = n.value
            if re.fullmatch(r"[A-Za-z_]+", v) or v.strip() == "Split Payment":
                continue
            if re.search(r"split", v, re.I):
                bad.append("%s:%d %r" % (os.path.basename(path), n.lineno, v[:50]))
    return bad


def ok(cond, what):
    RUN[0] += 1
    if not cond:
        FAILS.append(what)


class _Req(object):
    args = {}


def _stub_flask():
    try:
        import flask                                     # noqa: F401
        return False
    except ImportError:
        fl = types.ModuleType("flask")

        class _BP(object):
            def __init__(self, *a, **k):
                pass

            def route(self, *a, **k):
                return lambda f: f
        fl.Blueprint = _BP
        fl.request = _Req()
        for n in ("jsonify", "render_template_string", "send_file", "Response", "redirect"):
            setattr(fl, n, None)
        sys.modules["flask"] = fl
        return True


def load(folder):
    stub = _stub_flask()
    mods = {}
    for name in NAMES:
        spec = importlib.util.spec_from_file_location(name, os.path.join(folder, name + ".py"))
        m = importlib.util.module_from_spec(spec)
        sys.modules[name] = m                            # clinic_day_pdf imports finance_clinic_day by name
        spec.loader.exec_module(m)
        mods[name] = m
    fcd = mods["finance_clinic_day"]
    fcd._require = lambda *a, **k: ({"user": "walk"}, None)
    if stub:
        fcd.request = _Req()
    return mods


def day_html(fcd, con, date):
    fcd._db = lambda: con
    return fcd.clinic_day_detail(date)


def month_html(fcd, con, ym):
    fcd._db = lambda: con
    req = sys.modules["flask"].request if not hasattr(fcd, "request") else fcd.request
    try:
        req.args = {"m": ym}
    except Exception:                                    # a real flask request cannot be set: run in a context
        pass
    try:
        return fcd.clinic_day_page()
    except RuntimeError:                                 # real flask, outside a request: use a test context
        import flask
        app = flask.Flask("walk")
        with app.test_request_context("/finance/clinic/day?m=%s" % ym):
            return fcd.clinic_day_page()


def pdf_bytes(pdf, con, date):
    d = pdf.day_data(con, date)
    return pdf.render_pdf(d, who="walk") if d else b""


def nosplit(s):
    if isinstance(s, bytes):
        s = s.decode("latin-1")
    return re.search(r"split", s, re.I) is None


def made_up():
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.executescript("""
    CREATE TABLE setting (key TEXT PRIMARY KEY, value TEXT);
    CREATE TABLE clinic_day_revenue (business_date TEXT PRIMARY KEY, source_file TEXT, cons_count INT, cons_amount_p INT,
      xray_count INT, xray_amount_p INT, proc_count INT, proc_amount_p INT, total_count INT, total_amount_p INT, morning INT,
      evening INT, free_revisits INT, free_concession INT, tender_json TEXT);
    CREATE TABLE clinic_day_line (business_date TEXT, section TEXT, sn INT, patient TEXT DEFAULT '', clinic_id TEXT DEFAULT '',
      amount_p INT, mode TEXT, shift TEXT DEFAULT 'Morning', gateway_ref TEXT NOT NULL DEFAULT '');
    CREATE TABLE clinic_day_tender (business_date TEXT, clinic_id TEXT DEFAULT '', invoice_no TEXT DEFAULT '', tender TEXT,
      amount_p INT, source_file TEXT DEFAULT '');
    CREATE TABLE icici_statement_line (id INTEGER PRIMARY KEY, account_ref TEXT, txn_date TEXT, value_date TEXT, description TEXT,
      reference TEXT, withdrawal_p INT DEFAULT 0, deposit_p INT DEFAULT 0, balance_p INT, is_cash_deposit INT DEFAULT 0,
      source_file TEXT, sha256 TEXT, ingested_at TEXT);
    CREATE TABLE icici_statement_period (id INTEGER PRIMARY KEY, account_ref TEXT, period_from TEXT, period_to TEXT, opening_p INT,
      closing_p INT, source_file TEXT, sha256 TEXT, ingested_at TEXT, layout TEXT, closing_printed INT);
    CREATE TABLE upi_txn (id INTEGER PRIMARY KEY, merchant_id TEXT, unit TEXT, txn_date TEXT, amount_p INT, rrn TEXT, mode TEXT);
    CREATE TABLE payment_register (row_no INTEGER PRIMARY KEY, date_raw TEXT DEFAULT '', date_iso TEXT, vendor TEXT DEFAULT '',
      description TEXT DEFAULT '', amount_raw TEXT DEFAULT '', amount_paise INT, in_drive INT, gmail_link TEXT DEFAULT '',
      content_md5 TEXT DEFAULT 'x', first_seen TEXT DEFAULT '', last_seen TEXT DEFAULT '');
    """)
    R = 100
    D = "2031-03-02"
    S = "Split Payment"
    lines = [  # section, clinic, rupees, mode, ref
        ("consult", "A1", 600, S, ""), ("xray", "A1", 500, S, ""),                          # one to one
        ("consult", "B2", 600, S, ""), ("xray", "B2", 500, S, ""), ("proc", "B2", 2500, S, ""),   # grouped
        ("consult", "C3", 600, S, ""), ("xray", "C3", 800, S, ""),                          # one item in two parts
        ("proc", "D4", 1500, S, ""),                                                        # no parts
        ("consult", "E5", 600, "Online Payment", "pay_WALK1"), ("proc", "E5", 1000, "Online Payment", "pay_WALK1"),  # F-869
        ("consult", "F6", 600, "Cash", ""), ("revisit", "G7", 0, "", ""),
    ]
    sn = {}
    for sec, cid, rs, mode, ref in lines:
        sn[sec] = sn.get(sec, 0) + 1
        con.execute("INSERT INTO clinic_day_line (business_date, section, sn, clinic_id, amount_p, mode, gateway_ref) "
                    "VALUES (?,?,?,?,?,?,?)", (D, sec, sn[sec], cid, rs * R, mode, ref))
    for cid, t, rs in (("A1", "Cash", 600), ("A1", "Online Payment", 500), ("B2", "Cash", 1100), ("B2", "Online Payment", 2500),
                       ("C3", "Cash", 1000), ("C3", "Online Payment", 400)):
        con.execute("INSERT INTO clinic_day_tender (business_date, clinic_id, invoice_no, tender, amount_p) VALUES (?,?,?,?,?)",
                    (D, cid, "INV-" + cid, t, rs * R))
    cons = sum(rs for s, _c, rs, _m, _r in lines if s == "consult") * R
    xray = sum(rs for s, _c, rs, _m, _r in lines if s == "xray") * R
    proc = sum(rs for s, _c, rs, _m, _r in lines if s == "proc") * R
    tj = '{"Cash": %d, "Online Payment": %d, "Split Payment": %d}' % (600 * R, 1600 * R, 7600 * R)
    con.execute("INSERT INTO clinic_day_revenue VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (D, "walk", 5, cons, 3, xray, 3, proc, 11, cons + xray + proc, 8, 3, 1, 0, tj))
    con.execute("INSERT INTO clinic_day_revenue VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("2031-04-01", "walk", 1, 600 * R, 0, 0, 0, 0, 1, 600 * R, 1, 0, 0, 0, '{"Cash": 60000}'))
    con.execute("INSERT INTO clinic_day_line (business_date, section, sn, clinic_id, amount_p, mode) VALUES "
                "('2031-04-01','consult',1,'H8',60000,'Cash')")
    return con, D


def part_a(folder):
    for name in NAMES:
        bad = split_strings(os.path.join(folder, name + ".py"))
        ok(not bad, "A: a readable string still says 'split': %s" % "; ".join(bad[:3]))
    m = load(folder)
    fcd, pdf, packs = m["finance_clinic_day"], m["clinic_day_pdf"], m["packs"]
    con, D = made_up()
    R = 100
    h = day_html(fcd, con, D)
    ok(nosplit(h), "A: the day page still says 'split'")
    ok("Cash ₹400 + Online ₹400" in h, "A: the X-ray paid two ways is not shown as 'Cash ₹400 + Online ₹400'")
    ok(h.count("mode not known") == 1, "A: the bill with no parts does not read 'mode not known' exactly once")
    ok("SPLIT PAYMENTS" not in h, "A: the SPLIT PAYMENTS card is still on the day page")
    mt = getattr(fcd, "mode_texts", None)
    ok(mt is not None, "A: no mode_texts in finance_clinic_day")
    if mt:
        w = mt(con, D)
        ok(w.get(("consult", 1)) == "Cash" and w.get(("xray", 1)) == "Online Payment", "A: one-to-one bill wrong: %r" % (w,))
        ok(w.get(("consult", 2)) == "Cash" and w.get(("xray", 2)) == "Cash" and w.get(("proc", 1)) == "Online Payment",
           "A: grouped bill wrong")
        ok(w.get(("consult", 3)) == "Cash" and w.get(("xray", 3)) == "Cash ₹400 + Online ₹400", "A: two-part bill wrong")
        ok(w.get(("proc", 2)) == "mode not known", "A: no-parts bill wrong")
        kinds = sorted(b["kind"] for b in fcd.bill_parts(con, D))
        ok(kinds == ["grouped", "not_known", "one", "two_parts"], "A: bill kinds %r" % kinds)
        row = con.execute("SELECT * FROM clinic_day_revenue WHERE business_date=?", (D,)).fetchone()
        t = fcd.day_tender(con, row)
        ok((t["cash"], t["online"], t["card"], t["unknown"]) == (3300 * R, 5000 * R, 0, 1500 * R),
           "A: the day by mode is %r" % ((t["cash"], t["online"], t["card"], t["unknown"]),))
        ok(t["cash"] + t["online"] + t["card"] + t["unknown"] + sum(p for _l, p in t["other"]) == row["total_amount_p"],
           "A: the day's modes do not add to its total")
    # F-869: the booked visit's procedure line is ICICI money, its consultation line the portal's
    ok(fcd.our_portal_p(con, D) == 600 * R, "A: F-869 -- portal is %r, expected the consultation fee only" % fcd.our_portal_p(con, D))
    ok(fcd.our_online_p(con, D) == (1600 + 500 + 2500 + 400) * R, "A: the day's online figure moved")
    # the morning match (clinic_money): no 'split' in how a part is described; F-869 in its own channel rule
    cm = m["clinic_money"]
    try:
        doc = cm._docterz(con, D)
        ok(all(nosplit(o.get("how") or "") for o in doc["online"]), "A: the morning match describes a part as 'split'")
        ok([o["channel"] for o in doc["online"] if o.get("gateway_ref")] == ["portal", "icici"],
           "A: F-869 -- the morning match's channels for the booked visit are %r"
           % [o["channel"] for o in doc["online"] if o.get("gateway_ref")])
    except Exception as e:                                # noqa: BLE001
        ok(False, "A: the morning match's reading raised %r" % (e,))
    # the month tables
    h = month_html(fcd, con, "2031-03")
    ok(nosplit(h), "A: the month table still says 'split'")
    ok('<th class="r">Mode not known</th>' in h and "3,300" in h and "5,000" in h, "A: the month table's cash / online / not-known cells are wrong")
    h = month_html(fcd, con, "2031-04")
    ok(nosplit(h) and '<th class="r">Mode not known</th>' not in h, "A: a month with every mode known shows a 'Mode not known' column")
    # the PDF
    b = pdf_bytes(pdf, con, D)
    ok(b.startswith(b"%PDF") and nosplit(b), "A: the PDF still says 'split'")
    ok(b"Cash Rs 400 + Online Rs 400" in b, "A: the PDF does not show the X-ray in two parts")
    ok(b"Mode not known Rs 1,500" in b and b"Cash Rs 3,300" in b and b"Online Rs 5,000" in b, "A: the PDF's Paid as line is wrong")
    # the accountants' income sheet
    try:
        x, err = packs.build_income(con, "2031-03")
    except Exception as e:                                # noqa: BLE001
        x, err = None, repr(e)
    ok(x is not None, "A: the income sheet did not build: %s" % err)
    if x:
        z = zipfile.ZipFile(io.BytesIO(x))
        txt = "".join(z.read(n).decode("utf-8", "replace") for n in z.namelist() if n.endswith(".xml"))
        ok(nosplit(txt), "A: the accountants' income sheet still says 'split'")
        ok("Mode not known" in txt or "payment mode was not in the export" in txt, "A: the income sheet does not name the unknown mode")


def part_b(folder, db, frm):
    m = load(folder)
    fcd, pdf = m["finance_clinic_day"], m["clinic_day_pdf"]
    con = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    con.row_factory = sqlite3.Row
    days = [r[0] for r in con.execute("SELECT business_date FROM clinic_day_revenue WHERE business_date>=? ORDER BY 1", (frm,))]
    kinds = {}
    nlines = 0
    for d in days:
        row = con.execute("SELECT * FROM clinic_day_revenue WHERE business_date=?", (d,)).fetchone()
        old = fcd._tender(row)
        new = fcd.day_tender(con, row)
        so = old["cash"] + old["online"] + old["card"] + old["split"] + sum(p for _l, p in old["other"])
        sn = new["cash"] + new["online"] + new["card"] + new["unknown"] + sum(p for _l, p in new["other"])
        ok(so == sn, "B %s: modes add to %d, the old page's to %d" % (d, sn, so))
        ok(new["cash"] >= old["cash"] and new["online"] >= old["online"] and new["card"] >= old["card"],
           "B %s: a mode went down" % d)
        ok(new["unknown"] == 0, "B %s: Rs %d whose mode is not known" % (d, new["unknown"] // 100))
        for b in fcd.bill_parts(con, d):
            kinds[b["kind"]] = kinds.get(b["kind"], 0) + 1
            for key, a in b["items"]:
                ok(sum(p for _t, p in b["alloc"].get(key, [])) == a or b["kind"] in ("not_known", "unmatched"),
                   "B %s: an item's parts do not make its amount" % d)
        w = fcd.mode_texts(con, d)
        sl = con.execute("SELECT COUNT(*) FROM clinic_day_line WHERE business_date=? AND mode='Split Payment'", (d,)).fetchone()[0]
        nlines += sl
        ok(len(w) == sl, "B %s: %d lines paid by parts, %d given words" % (d, sl, len(w)))
        h = day_html(fcd, con, d)
        ok(nosplit(h), "B %s: the day page says 'split'" % d)
        dz = m["clinic_money"]._docterz(con, d)
        ok(all(nosplit(o.get("how") or "") for o in dz["online"]), "B %s: the morning match says 'split'" % d)
        b = pdf_bytes(pdf, con, d)
        ok(b.startswith(b"%PDF") and nosplit(b), "B %s: the PDF says 'split'" % d)
    for ym in sorted({d[:7] for d in days}):
        ok(nosplit(month_html(fcd, con, ym)), "B %s: the month table says 'split'" % ym)
    con.close()
    return days, kinds, nlines


def preview(folder, db, date, out_html, out_pdf):
    m = load(folder)
    con = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    con.row_factory = sqlite3.Row
    h = day_html(m["finance_clinic_day"], con, date)
    h = h.replace("<body>", "<body><p style='background:#fff3cd;border:1px solid #e0c060;padding:8px;border-radius:6px'>"
                  "PREVIEW, not live — built from the server's database as copied at 01:35 on 13-Oct-2026, with the new page "
                  "of kit S541. Nothing on the server has changed.</p>", 1)
    open(out_html, "w", encoding="utf-8").write(h)
    open(out_pdf, "wb").write(pdf_bytes(m["clinic_day_pdf"], con, date))
    con.close()


def main(a):
    if not a:
        print(__doc__)
        return 2
    folder = a[0]
    if "--preview" in a:
        i = a.index("--preview")
        preview(folder, a[a.index("--db") + 1], a[i + 1], a[i + 2], a[i + 3])
        print("PREVIEW written")
        return 0
    red = "--expect-red" in a
    try:
        part_a(folder)
    except Exception as e:                                # noqa: BLE001
        FAILS.append("A raised %r" % (e,))
    if red:
        if FAILS:
            print("WALK OK (negative control: the old files fail %d of %d checks, e.g. %s)" % (len(FAILS), RUN[0], FAILS[0][:80]))
            return 0
        print("WALK RED: the negative control passed on the old files -- the walk proves nothing")
        return 1
    extra = ""
    if "--db" in a:
        frm = a[a.index("--from") + 1] if "--from" in a else "2026-09-01"
        try:
            days, kinds, nl = part_b(folder, a[a.index("--db") + 1], frm)
            extra = " · B: %d days from %s, %d lines paid by parts in %d bills (%s)" % (
                len(days), frm, nl, sum(kinds.values()), ", ".join("%s %d" % kv for kv in sorted(kinds.items())))
        except Exception as e:                            # noqa: BLE001
            FAILS.append("B raised %r" % (e,))
    if FAILS:
        print("WALK RED: %d of %d checks failed" % (len(FAILS), RUN[0]))
        for f in FAILS[:15]:
            print("  - " + f)
        return 1
    print("WALK OK: %d checks green%s" % (RUN[0], extra))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
