#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""walk_s636.py -- the LIVE-SHAPE walk of kit S636_DAY_CHECK (D776 stage 1). Made-up patients, made-up IDs, a temp database.

    python3 walk_s636.py <dir with the NEW clinic_register.py + day_check.py> <dir with the rest: slip_log, slip_adjust,
                         clinic_money, owner_console> [--old]

The real Flask app shape: clinic_register.init(app, db, require, audit) mounts the register AND day_check, the pages are
asked over the test client as the staff and as the owner, the buttons are pressed, a Docterz re-export is simulated.
--old runs the same walk on the live clinic_register.py: exactly the S636 checks must go red, nothing older.
The last line is the verdict the installer reads."""
import os
import sqlite3
import sys
import tempfile
import types

NEW, REST = sys.argv[1], sys.argv[2]
OLD = "--old" in sys.argv
NODC = "--no-day-check" in sys.argv          # the new register with day_check.py missing: it must still work as before
sys.path[:0] = [NEW, REST]
if NODC:
    class _Block:
        def find_spec(self, name, path=None, target=None):
            if name == "day_check":
                raise ImportError("hidden by the walk")
            return None
    sys.meta_path.insert(0, _Block())
os.environ.setdefault("SLIP_NOW", "2026-10-23T09:00:00")

import datetime as _dt                                    # noqa: E402

import flask                                              # noqa: E402

TMP = tempfile.mkdtemp(prefix="s636walk_")
DB = os.path.join(TMP, "f.db")
USERS = {"shivani": ("clinic", ["maker"]), "alisha": ("clinic", ["maker"]), "shavez": ("slips", ["maker"]),
         "bhati": ("slips", ["maker"]), "manoj": ("clinic", ["checker"]), "nobody": (None, [])}
CUR = {"user": "shivani"}


def db():
    g = flask.g
    if "con" not in g:
        c = sqlite3.connect(DB)
        c.row_factory = sqlite3.Row
        g.con = c
    return g.con


def require(*roles, unit="finance"):
    u = CUR["user"]
    un, rl = USERS[u]
    have = set(rl) if (un == unit or (un == "clinic" and unit == "slips" and u == "manoj")) else set()
    if u in ("shavez", "bhati") and unit == "slips":
        have = {"maker"}
    if not have.intersection(roles):
        return None, (flask.jsonify(ok=False, error="not_permitted"), 403)
    return dict(user=u, role="staff", roles=sorted(have)), None


def audit(con, table, row_id, action, before=None, after=None, who=""):
    import json
    con.execute("INSERT INTO audit_log (table_name,row_id,action,before_json,after_json,by_whom,at) VALUES (?,?,?,?,?,?,?)",
                (table, row_id, action, json.dumps(before) if before is not None else None,
                 json.dumps(after) if after is not None else None, who, "now"))


BASE = """
CREATE TABLE audit_log (id INTEGER PRIMARY KEY, table_name TEXT NOT NULL, row_id INTEGER, action TEXT NOT NULL,
  before_json TEXT, after_json TEXT, by_whom TEXT, at TEXT NOT NULL);
CREATE TABLE setting (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE clinic_day_revenue (business_date TEXT PRIMARY KEY, taken_at TEXT, total_amount_p INTEGER DEFAULT 0);
CREATE TABLE clinic_day_line (business_date TEXT NOT NULL, section TEXT NOT NULL, sn INTEGER NOT NULL,
  patient TEXT NOT NULL DEFAULT '', clinic_id TEXT NOT NULL DEFAULT '', amount_p INTEGER NOT NULL DEFAULT 0,
  mode TEXT NOT NULL DEFAULT '', gateway_ref TEXT NOT NULL DEFAULT '', shift TEXT NOT NULL DEFAULT '',
  PRIMARY KEY (business_date, section, sn));
CREATE TABLE clinic_day_tender (business_date TEXT NOT NULL, clinic_id TEXT NOT NULL DEFAULT '', invoice_no TEXT NOT NULL
  DEFAULT '', tender TEXT NOT NULL, amount_p INTEGER NOT NULL, source_file TEXT NOT NULL DEFAULT '');
CREATE TABLE upi_txn (id INTEGER PRIMARY KEY, merchant_id TEXT, unit TEXT, txn_date TEXT, amount_p INTEGER, rrn TEXT,
  mode TEXT, txn_time TEXT, source_sha TEXT, ingested_at TEXT);
CREATE TABLE patient_ref (id INTEGER PRIMARY KEY, clinic_id TEXT, name TEXT, phone_last4 TEXT, merged_into TEXT);
"""
D1, D2, D3 = "2026-10-22", "2026-10-21", "2026-10-20"     # the 22-Oct shape, the 07-Oct shape, a clean day


def seed(con):
    import clinic_register as CR
    import slip_log as SL
    con.executescript(BASE)
    CR._schema_done = False
    CR._ensure(con)
    SL._schema_done = False
    SL.ensure(con)
    ln = []
    # --- D1, the shape of 22-Oct: one parchi X-ray not billed (cash), an X-ray billed cash paid UPI (room tick blank),
    #     a consultation billed card paid UPI, Rs 700 UPI no patient, one ID written twice + one bill with no parchi
    cons = [("A1", "9101", 800, "Cash"), ("A2", "9102", 600, "Cash"), ("A3", "9103", 600, "Cash"), ("A4", "9104", 600, "Debit Card"),
            ("A5", "9105", 600, "Online Payment"), ("A6", "9106", 500, "Online Payment"), ("A7", "9107", 600, "Cash")]
    for i, (n, c, a, m) in enumerate(cons, 1):
        ln.append((D1, "consult", i, "Patient " + n, c, a * 100, m))
    xr = [("A2", "9102", 1000, "Cash"), ("A3", "9103", 1000, "Cash"), ("A5", "9105", 500, "Online Payment")]
    for i, (n, c, a, m) in enumerate(xr, 1):
        ln.append((D1, "xray", i, "Patient " + n, c, a * 100, m))
    ln.append((D1, "proc", 1, "Patient A7", "9107", 50000, "Cash"))
    # --- D2, the shape of 07-Oct: a patient's X-ray and slab on parchis, cash collected, nothing in Docterz
    for i, (n, c, a, m) in enumerate([("B1", "9201", 600, "Cash"), ("B2", "9202", 600, "Cash")], 1):
        ln.append((D2, "consult", i, "Patient " + n, c, a * 100, m))
    # --- D3 clean
    ln.append((D3, "consult", 1, "Patient C1", "9301", 60000, "Cash"))
    ln.append((D3, "xray", 1, "Patient C1", "9301", 50000, "Online Payment"))
    con.executemany("INSERT INTO clinic_day_line (business_date,section,sn,patient,clinic_id,amount_p,mode) VALUES (?,?,?,?,?,?,?)", ln)
    for d in (D1, D2, D3):
        con.execute("INSERT INTO clinic_day_revenue VALUES (?,?,0)", (d, d + " 21:20:00"))
    # the register (the handwritten book's totals)
    reg = {D1: dict(cons_cash_p=260000, cons_upi_p=240000, xray_cash_p=160000, xray_upi_p=150000, proc_cash_p=50000),
           D2: dict(cons_cash_p=120000, xray_cash_p=50000, proc_cash_p=250000),
           D3: dict(cons_cash_p=60000, xray_upi_p=50000)}
    for d, v in reg.items():
        cols = ",".join(v)
        con.execute("INSERT INTO clinic_register_day (business_date,%s,entered_by,entered_at) VALUES (?,%s,'shivani','x')"
                    % (cols, ",".join("?" * len(v))), [d] + list(v.values()))
    # the bank (D1: 4,000 UPI = the register; D3: 500)
    for d, amts in ((D1, [600, 500, 500, 1000, 600, 700]), (D3, [500])):
        for a in amts:
            con.execute("INSERT INTO upi_txn (unit,txn_date,amount_p) VALUES ('clinic',?,?)", (d, a * 100))
    # the parchis
    def slip(series, no, day, cid, paid="", items=()):
        cur = con.execute("INSERT INTO slip (series,slip_no,day,clinic_id,paid_mode,logged_by,logged_at) VALUES (?,?,?,?,?,?,?)",
                          (series, no, day, cid, paid, "shavez", day + " 10:00:00"))
        for k, (kind, name, side, price) in enumerate(items):
            con.execute("INSERT INTO slip_item (slip_id,kind,name,side,price_p,sort) VALUES (?,?,?,?,?,?)",
                        (cur.lastrowid, kind, name, side, price * 100, k))
        return cur.lastrowid
    for no, c in ((501, "9101"), (502, "9102"), (503, "9103"), (504, "9104"), (505, "9105"), (506, "9107"), (507, "9107")):
        slip("opd", no, D1, c)
    slip("xp", 601, D1, "9102", "cash", [("xray", "Knee AP & Lat", "", 1000)])
    slip("xp", 602, D1, "9103", "", [("xray", "Knee AP & Lat", "", 1000)])               # tick blank: billed cash, paid UPI
    slip("xp", 603, D1, "9105", "upi", [("xray", "Ankle AP & Lat", "R", 500)])
    slip("xp", 604, D1, "9108", "cash", [("xray", "DL spine 11x14", "", 600)])            # no Docterz line: entry missing
    slip("xp", 605, D1, "9107", "cash", [("proc", "ILI knee", "", 500)])
    slip("opd", 701, D2, "9201")
    slip("opd", 702, D2, "9202")
    slip("xp", 711, D2, "9202", "cash", [("xray", "Foot AP & Obl", "R", 500)])
    slip("xp", 712, D2, "9202", "cash", [("proc", "Short below knee slab", "R", 2500)])
    slip("opd", 721, D3, "9301")
    slip("xp", 722, D3, "9301", "upi", [("xray", "Wrist AP & Lat", "", 500), ("xray", "Wrist AP & Lat", "", 500)])  # written twice
    con.commit()


RES = []


def ok(name, cond, s636=True):
    RES.append((name, bool(cond), s636))
    print(("  ok   " if cond else "  RED  ") + name)


def main():
    import clinic_register as CR
    app = flask.Flask("walk")
    app.secret_key = "walk"
    CR.init(app, db, require, audit, unit="clinic")
    import slip_log as SL
    SL.init(app, db, require, audit, unit="slips")
    with app.app_context():
        seed(db())
    try:
        import day_check as DC
    except Exception:                                    # noqa: BLE001
        DC = None
    cl = app.test_client()

    def get(path, who):
        CUR["user"] = who
        r = cl.get(path)
        return r.status_code, r.get_data(as_text=True)

    def post(path, who, data):
        CUR["user"] = who
        r = cl.post(path, data=data)
        return r.status_code, r.headers.get("Location", ""), r.get_data(as_text=True)

    with app.app_context():
        con = db()
        if DC is not None and not OLD and not NODC:
            c1 = DC.check_day(con, D1)
            ok("1  22-Oct shape reads 'Rs 1,300 Docterz entry missing · 2 payment modes wrong · 1 parchi to fix'",
               DC.summary_en(c1) == "22-Oct: Rs 1,300 Docterz entry missing · 2 payment modes wrong · 1 parchi to fix")
            kinds = sorted((c["kind"], c["amount"]) for c in c1["cards"])
            ok("2  ... as Rs 600 entry missing + Rs 700 patient not found + two modes + the ID written twice",
               kinds == sorted([("missing", 60000), ("notfound", 70000), ("mode", 100000), ("mode", 60000), ("parchi", 0)]))
            c2 = DC.check_day(con, D2)
            ok("3  07-Oct shape reads 'Rs 3,000 Docterz entry missing' (two lines, cash)",
               DC.summary_en(c2) == "21-Oct: Rs 3,000 Docterz entry missing" and all(c["tender"] == "cash" for c in c2["cards"]))
            c3 = DC.check_day(con, D3)
            ok("4  a parchi line written twice, register = Docterz: one parchi card, no money line",
               DC.summary_en(c3) == "20-Oct: 1 parchi to fix")
        else:
            for n in ("1  22-Oct shape", "2  the kinds", "3  07-Oct shape", "4  the duplicate"):
                ok(n + " (no day_check)", False)
    st, html = get("/finance/clinic/register/list", "manoj")
    ok("A  (older) the day list opens", st == 200 and "Every day" in html, s636=False)
    st, html2 = get("/finance/clinic/register/%s" % D3, "shivani")
    ok("B  (older) a day's register opens with the three records", st == 200 and "The three records" in html2, s636=False)
    CUR["user"] = "shivani"
    r = cl.post("/finance/clinic/register/%s" % D3, data={"cons_cash_p": "600", "xray_upi_p": "500"})
    with app.app_context():
        rw = db().execute("SELECT cons_cash_p, xray_upi_p FROM clinic_register_day WHERE business_date=?", (D3,)).fetchone()
    ok("C  (older) the register's Save stores the figures", r.status_code == 200 and tuple(rw) == (60000, 50000), s636=False)
    st, html = get("/finance/clinic/register/list", "shivani")
    ok("5  the day list's chip opens the day's corrections", st == 200 and "href='/finance/clinic/check/%s'" % D1 in html)
    ok("6  the chip names the kinds (not the UPI-only verdict)", "Rs 1,300 Docterz entry missing · 2 payment modes wrong" in html)
    st, html = get("/finance/clinic/register/%s" % D1, "shivani")
    ok("7  the register's day page shows the cards under the three records, in Hindi for staff",
       st == 200 and "id='check'" in html and "Docterz mein entry nahi" in html)
    st, html = get("/finance/clinic/register/%s" % D1, "manoj")
    ok("8  ... and in English for the owner", st == 200 and "Rs 600 — Docterz entry missing" in html)
    CUR["user"] = "shivani"
    r = cl.post("/finance/clinic/register/%s" % D1, data={"cons_cash_p": "2600", "cons_upi_p": "2400", "xray_cash_p": "1600",
                                                          "xray_upi_p": "1500", "proc_cash_p": "500"})
    h = r.get_data(as_text=True)
    ok("9  the Save says the day's check at once", r.status_code == 200 and "The day's check:" in h)
    st, html = get("/finance/clinic/check/%s" % D1, "shavez")
    ok("10 the check page opens for Shavez (unit slips) with the three records on top", st == 200 and "The three records" in html)
    if DC is None or OLD or NODC:
        for n in ("11 tick", "12 tick is not proof", "13 re-export clears", "14 not right", "15 found it", "16 free -> approval",
                  "17 not paid -> approval", "18 fix the ID", "19 remove duplicate", "20 permissions", "21 undo", "22 nobody"):
            ok(n + " (no day_check)", False)
    else:
        with app.app_context():
            c1 = DC.check_day(db(), D1)
        key_add = next(c["key"] for c in c1["cards"] if c["kind"] == "missing")
        st, loc, _ = post("/finance/clinic/check/%s/act" % D1, "alisha", {"key": key_add, "act": "added"})
        ok("11 Alisha taps Added: stored", st == 303 and "ok=" in loc)
        with app.app_context():
            c1 = DC.check_day(db(), D1)
        card = next(c for c in c1["cards"] if c["key"] == key_add)
        ok("12 a tick is never proof: the line stays, marked", card["tick"] is not None and card["tick"]["who"] == "alisha")
        with app.app_context():
            con = db()
            con.execute("INSERT INTO clinic_day_line (business_date,section,sn,patient,clinic_id,amount_p,mode) VALUES (?,?,?,?,?,?,?)",
                        (D1, "xray", 9, "Patient A8", "9108", 60000, "Cash"))
            con.commit()
            c1 = DC.check_day(con, D1)
        ok("13 the re-export shows it: the line is gone", not any(c["key"] == key_add for c in c1["cards"]))
        key_mode = next(c["key"] for c in c1["cards"] if c["kind"] == "mode")
        st, loc, _ = post("/finance/clinic/check/%s/act" % D1, "shivani", {"key": key_mode, "act": "notright", "reason": "docterz_right"})
        with app.app_context():
            t = DC._ticks(db(), D1).get(key_mode)
        ok("14 Not right takes a tapped reason", t is not None and t["reason"] == "docterz_right")
        key_nf = next(c["key"] for c in c1["cards"] if c["kind"] == "notfound")
        post("/finance/clinic/check/%s/act" % D1, "shavez", {"key": key_nf, "act": "found", "pick": "9106"})
        with app.app_context():
            t = DC._ticks(db(), D1).get(key_nf)
        ok("15 Found it keeps the patient picked from the day's list", t is not None and t["pick"] == "9106")
        # Free and Not paid on D2 (two parchi lines not in Docterz)
        with app.app_context():
            c2 = DC.check_day(db(), D2)
        a, b = [c for c in c2["cards"] if c["kind"] == "missing"][:2]
        st, loc, _ = post("/finance/clinic/check/%s/act" % D2, "shivani",
                          {"key": a["key"], "act": "free", "slip": a["slip"]["id"], "item": a["item"]["id"], "reason": "poor"})
        with app.app_context():
            pend = [r for r in db().execute("SELECT * FROM slip_adjust WHERE state='pending' AND kind='free'")]
        ok("16 Free goes to his approval (slip_adjust, pending)", len(pend) == 1 and "ok=" in loc)
        st, loc, _ = post("/finance/clinic/check/%s/act" % D2, "shivani",
                          {"key": b["key"], "act": "notpaid", "slip": b["slip"]["id"]})
        with app.app_context():
            pc = [r for r in db().execute("SELECT * FROM slip_adjust WHERE state='pending' AND kind='cancel' AND cancel_how='never_taken'")]
        ok("17 Not paid goes to his approval (radd, money never taken)", len(pc) == 1 and "ok=" in loc)
        # parchi buttons
        with app.app_context():
            c1 = DC.check_day(db(), D1)
        pid = next(c for c in c1["cards"] if c.get("pkind") == "opd_wrong_id")
        st, loc, _ = post("/finance/clinic/check/%s/act" % D1, "alisha",
                          {"key": pid["key"], "act": "fixid", "slip": pid["slip"]["id"], "to": pid["to_cid"]})
        denied = "err=" in loc
        st, loc, _ = post("/finance/clinic/check/%s/act" % D1, "shavez",
                          {"key": pid["key"], "act": "fixid", "slip": pid["slip"]["id"], "to": pid["to_cid"]})
        with app.app_context():
            now_id = db().execute("SELECT clinic_id FROM slip WHERE id=?", (pid["slip"]["id"],)).fetchone()[0]
            c1 = DC.check_day(db(), D1)
        ok("18 Shavez fixes the ID (the parchi card goes); Alisha may not", denied and now_id == pid["to_cid"]
           and not any(c["kind"] == "parchi" for c in c1["cards"]))
        with app.app_context():
            c3 = DC.check_day(db(), D3)
        dup = c3["cards"][0]
        st, loc, _ = post("/finance/clinic/check/%s/act" % D3, "bhati", {"key": dup["key"], "act": "dupitem"})
        with app.app_context():
            n = db().execute("SELECT COUNT(*) FROM slip_item i JOIN slip s ON s.id=i.slip_id WHERE s.day=?", (D3,)).fetchone()[0]
            c3 = DC.check_day(db(), D3)
            aud = db().execute("SELECT COUNT(*) FROM audit_log WHERE action='slip_item_removed_duplicate'").fetchone()[0]
        ok("19 Remove duplicate takes off the repeated line, audited; the day reads 'all correct'",
           n == 1 and aud == 1 and DC.summary_en(c3) == "20-Oct: all correct")
        st, loc, _ = post("/finance/clinic/check/%s/act" % D1, "bhati", {"key": key_mode, "act": "changed"})
        ok("20 Bhati may not tick a Docterz line", "err=" in loc)
        post("/finance/clinic/check/%s/act" % D1, "shivani", {"key": key_mode, "act": "undo"})
        with app.app_context():
            t = DC._ticks(db(), D1).get(key_mode)
        ok("21 Undo takes a tick back", t is None)
        st, html = get("/finance/clinic/check/%s" % D1, "nobody")
        ok("22 a login with no role is refused", "Not permitted" in html)
    # owner_console: his line, counts only
    if DC is not None and not OLD and not NODC:
        for m in ("bank_mpr_status", "darpan_kal", "packs", "sanjeevni_cash"):
            sys.modules.setdefault(m, types.ModuleType(m))
        import owner_console as OC
        with app.app_context():
            sec = OC.sec_money(db(), {"clinic_day": D1, "sanj_day": D1, "today": "2026-10-23", "tile": {}})
        txt = [ln_["text"] for ln_ in sec["lines"]]
        hit = [t for t in txt if "Docterz entry missing" in t or "payment mode" in t]
        ok("23 his console line counts kinds, names no patient", bool(hit) and "Patient" not in " ".join(txt)
           and "2 payment modes wrong" in hit[0])
        ok("24 an earlier day with lines shows under it; a clean earlier day does not",
           any("21‑Oct" in t for t in txt) and not any("20‑Oct" in t for t in txt))
    else:
        ok("23 console line (no day_check)", False)
        ok("24 console earlier days (no day_check)", False)
    red = [n for n, c, _s in RES if not c]
    green = len(RES) - len(red)
    if OLD or NODC:
        s636_red = len([1 for n, c, s in RES if not c and s])
        older_red = len([1 for n, c, s in RES if not c and not s])
        print("%d S636 check(s) red · %d older red · %d green" % (s636_red, older_red, green))
    else:
        print("%d of %d green" % (green, len(RES)))


if __name__ == "__main__":
    try:
        main()
    finally:
        import shutil
        shutil.rmtree(TMP, ignore_errors=True)
