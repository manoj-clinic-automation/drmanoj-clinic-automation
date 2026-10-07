#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s496.py -- the LIVE-SHAPE walk of S496_POS_STANDIN.  Read-only on everything it is pointed at: it works on
its own scratch copies of the database and never writes to --db, --code or --kit.

    python3 -B walk_s496.py --kit <kit folder> --code <the finance code as it is live> [--code <more>] --db <finance.db>

PART 1  bank_standin on a made-up store: the whole life of a typed figure, every refusal, the settings, the hooks.
PART 2  the real pages on a copy of the real database, served by Flask's test client under the real logins' roles:
        (a) while no figure exists and the bank's statement is in, every page is what the LIVE code gives -- the same
            pages are rendered by the live modules and by the kit's modules in two child processes and compared;
        (b) the clinic: the newest filled day has its statement taken away ON THE COPY -- not due -> nothing; due ->
            the one field; typed -> nothing changes; confirmed -> the bank part stands on it; a wrong figure -> one
            flag; the statement put back -> the bank wins by itself and the typed row is kept;
        (c) Sanjeevni: the same on the newest day Darpan posted -- and after the statement is put back the day is
            decided exactly as it was before the walk began;
        (d) no money row changed anywhere.
Last line:  WALK_S496 GREEN <n> checks   or   WALK_S496 RED <n> failed of <m>
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_PY = ("bank_standin.py", "bank_mpr_status.py", "clinic_money.py", "darpan_kal.py")
KIT_OTHER = ("darpan_kal.html",)
CHECKS = []


def ok(cond, what, detail=""):
    CHECKS.append(bool(cond))
    print("  %s %s%s" % ("pass" if cond else "FAIL", what, ("" if cond else ("  <-- " + str(detail)[:400]))))
    return bool(cond)


def note(t):
    print("  note %s" % t)


def copy_db(src, dst):
    a = sqlite3.connect("file:%s?mode=ro" % src, uri=True, timeout=30)
    b = sqlite3.connect(dst)
    try:
        a.backup(b)
    finally:
        b.close()
        a.close()


def connect(path):
    con = sqlite3.connect(path, timeout=30)
    con.row_factory = sqlite3.Row
    return con


# ============================================================================================ the harness
class Harness:
    """A Flask app carrying the three modules, on one database file, under a login we choose."""

    def __init__(self, dbpath, paths):
        for p in reversed(paths):
            if p not in sys.path:
                sys.path.insert(0, p)
        from flask import Flask, jsonify, g                      # noqa: PLC0415
        self.dbpath = dbpath
        self.user = {"user": "nobody", "role": "staff"}
        app = Flask("walk_s496")
        app.config["TESTING"] = True
        self.app = app

        def db():
            if "con" not in g:
                g.con = connect(dbpath)
            return g.con

        @app.teardown_appcontext
        def _close(_e=None):
            c = g.pop("con", None)
            if c is not None:
                c.close()

        def require(*roles, unit="medical"):
            u = dict(self.user)
            have = {r["role"] for r in db().execute("SELECT role FROM unit_role WHERE unit=? AND username=? AND active=1", (unit, u["user"]))}
            if not have.intersection(roles):
                return None, (jsonify(ok=False, error="not_permitted"), 403)
            return dict(u, roles=sorted(have)), None

        def audit(con, table, row_id, action, before=None, after=None, who=""):
            con.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, after_json, by_whom, at) VALUES (?,?,?,?,?,?,?)",
                        (table, row_id, action, json.dumps(before) if before is not None else None,
                         json.dumps(after) if after is not None else None, who, dt.datetime.now().isoformat()))

        import bank_mpr_status                                   # noqa: PLC0415
        import clinic_money                                      # noqa: PLC0415
        import darpan_kal                                        # noqa: PLC0415
        bank_mpr_status.init(app, db, require, unit="clinic", upi_dir=None)
        clinic_money.init(app, db, require, audit, unit="clinic")
        darpan_kal.init(app, db, require, unit="medical")
        self.reg = False
        try:
            import clinic_register                               # noqa: PLC0415
            clinic_register.init(app, db, require, audit, unit="clinic")
            self.reg = True
        except Exception as ex:                                  # noqa: BLE001
            print("  note the counter sheet's own page is not mounted in this walk (%s) -- its block is asked for directly" % str(ex)[:100])
        self.cm, self.dk, self.bm = clinic_money, darpan_kal, bank_mpr_status
        self.client = app.test_client()

    def as_(self, user, role="staff"):
        self.user = {"user": user, "role": role}
        return self

    def get(self, url):
        r = self.client.get(url)
        return r.status_code, r.get_data(as_text=True)

    def post_form(self, url, data):
        r = self.client.post(url, data=data)
        return r.status_code, r.get_data(as_text=True)

    def post_json(self, url, body):
        r = self.client.post(url, json=body)
        try:
            j = r.get_json()
        except Exception:                                        # noqa: BLE001
            j = None
        return r.status_code, (j or {})

    def get_json(self, url):
        r = self.client.get(url)
        return r.status_code, (r.get_json() or {})

    def blocks(self, d, user):
        """clinic_money.register_blocks as the counter sheet calls it."""
        with self.app.test_request_context("/finance/clinic/register/%s" % d):
            con = connect(self.dbpath)
            try:
                return self.cm.register_blocks(con, d, {"user": user, "roles": ["maker"]})
            finally:
                con.close()


def overlay(kit, scratch):
    """The kit's files in a folder of their own, in front of the live code (darpan_kal reads two files beside itself)."""
    o = os.path.join(scratch, "overlay")
    os.makedirs(o, exist_ok=True)
    for f in KIT_PY + KIT_OTHER:
        shutil.copy2(os.path.join(kit, f), os.path.join(o, f))
    return o


def side_files(o, codes):
    for name in ("darpan_kal_schema.sql", "darpan_month.html"):
        for c in codes:
            p = os.path.join(c, name)
            if os.path.isfile(p):
                shutil.copy2(p, os.path.join(o, name))
                break


# ============================================================================================ PART 1
def part1(kit):
    print("PART 1 -- bank_standin on a made-up store")
    sys.path.insert(0, kit)
    import importlib                                             # noqa: PLC0415
    BS = importlib.import_module("bank_standin")
    BM = importlib.import_module("bank_mpr_status")
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.executescript("""
      CREATE TABLE setting (key TEXT PRIMARY KEY, value TEXT NOT NULL, note TEXT);
      CREATE TABLE business_unit (code TEXT PRIMARY KEY, name TEXT);
      CREATE TABLE upi_statement (id INTEGER PRIMARY KEY, merchant_id TEXT, unit TEXT, statement_date TEXT, filename TEXT,
                                  parsed_total_p INTEGER, txn_count INTEGER, ingested_at TEXT);
      CREATE TABLE upi_txn (id INTEGER PRIMARY KEY, unit TEXT, txn_date TEXT, txn_time TEXT, amount_p INTEGER, rrn TEXT, mode TEXT);
      CREATE TABLE data_flag (id INTEGER PRIMARY KEY, unit TEXT, business_date TEXT, code TEXT, detail TEXT);
      INSERT INTO business_unit VALUES ('clinic','Clinic'),('medical','Sanjeevni'),('lab','Lab'),('physio','Physio');
      INSERT INTO upi_statement (merchant_id, unit, statement_date, ingested_at) VALUES
        ('m1','clinic','2030-01-01','2030-01-02T08:56:00'),('m2','medical','2030-01-01','2030-01-02T08:56:00'),('m3','lab','2030-01-01','2030-01-02T08:56:00');
    """)
    D = "2030-01-07"
    early, due = dt.datetime(2030, 1, 8, 9, 0), dt.datetime(2030, 1, 8, 10, 30)
    fired = []
    BS.on_change("clinic", lambda c, d: fired.append(d))

    us = BS.units(con)
    ok(us[:2] == ["clinic", "medical"] and "lab" in us and "physio" not in us, "the units are read from the statement store (clinic, medical, lab -- not assumed, not physio)", us)
    ok(BS.units_for_page(con, "clinic") == ["clinic", "lab"] and BS.units_for_page(con, "medical") == ["medical"],
       "a unit with no page of its own (lab) rides the clinic's owner page", (BS.units_for_page(con, "clinic"), BS.units_for_page(con, "medical")))
    ok(BM.expect_hhmm(con) == "10:00" and BS.expect_text(con) == "10:00" and BS.tolerance_p(con) == 10000, "defaults: bank expected by 10:00, tolerance ₹100")
    s = BS.day(con, "clinic", D, now=early)
    ok(s["state"] == "waiting" and not s["show"] and not s["offer"], "before the bank's time: not due, nothing is offered", s)
    ok(BS.type_figure(con, "clinic", D, 500000, "shivani", now=early)[1] == "not_due", "a staff figure before the bank's time is refused (not a daily duty)")
    s = BS.day(con, "clinic", D, now=due)
    ok(s["state"] == "not_received" and s["offer"] and s["show"], "after the bank's time with no statement: the one field is offered", s)
    ok(BS.type_figure(con, "clinic", "2030-01-08", 1, "shivani", now=due)[1] == "future", "today's own day cannot be typed (its statement cannot be missing yet)")
    ok(BS.type_figure(con, "clinic", D, -5, "shivani", now=due)[1] == "bad_amount", "a negative figure is refused")
    a_ok, a_code, r1 = BS.type_figure(con, "clinic", D, 500000, "shivani", now=due)
    ok(a_ok and a_code == "saved" and r1["status"] == "typed", "a staff figure is saved as typed")
    ok(BS.standing(con, "clinic", D, now=due) is None and not fired, "typed but not confirmed: NOTHING stands, no hook fired")
    _, _, r2 = BS.type_figure(con, "clinic", D, 510000, "shivani", now=due)
    st = {r["id"]: r["status"] for r in con.execute("SELECT id, status FROM bank_standin")}
    ok(st == {r1["id"]: "superseded", r2["id"]: "typed"}, "typed again: the first row is kept as superseded", st)
    ok(BS.decide(con, r2["id"], "confirm", "manoj", units_allowed=["medical"], now=due)[1] == "not_yours", "a line of another page's unit is refused")
    ok(BS.decide(con, r2["id"], "reject", "manoj", now=due)[1] == "rejected", "the owner rejects")
    s = BS.day(con, "clinic", D, now=due)
    ok(s["rejected"] is not None and s["offer"] and BS.standing(con, "clinic", D, now=due) is None, "rejected: nothing stands, staff may type again")
    _, _, r3 = BS.type_figure(con, "clinic", D, 520000, "alisha", now=due)
    items = BS.owner_items(con, ["clinic", "lab"], now=due)
    ok(len(items) == 1 and items[0]["kind"] == "pos_typed" and "typed by alisha" in items[0]["line"] and "5,200" in items[0]["line"]
       and "07-Jan-2030" in items[0]["line"], "the owner's ONE line: who typed it, for which date, the figure", items)
    ok(BS.owner_items(con, ["medical"], now=due) == [], "the line is not on another unit's page")
    ok(BS.decide(con, r3["id"], "confirm", "manoj", now=due)[1] == "confirmed" and fired == [D], "the owner confirms; the unit's hook is called once")
    sp = BS.standing(con, "clinic", D, now=due)
    ok(sp and sp["amount_p"] == 520000 and sp["label"] == "provisional — POS total, bank not in" and sp["typed_by"] == "alisha"
       and sp["confirmed_by"] == "manoj", "confirmed: it stands, marked 'provisional — POS total, bank not in'", sp)
    ok(BS.type_figure(con, "clinic", D, 1, "shivani", now=due)[1] == "already_confirmed", "staff cannot type over a confirmed figure")
    ok(BS.decide(con, r3["id"], "confirm", "manoj", now=due)[1] == "not_waiting", "a second confirm of the same line is refused")
    ok(not [i for i in BS.owner_items(con, None, now=due) if i["kind"] != "pos_never"], "confirmed and the bank still awaited: no line asks him anything")
    late = dt.datetime(2030, 1, 11, 12, 0)
    sp = BS.standing(con, "clinic", D, now=late)
    it = BS.owner_items(con, ["clinic"], now=late)
    ok(sp["never"] and sp["label"] == "bank statement never received" and len(it) == 1 and it[0]["kind"] == "pos_never" and it[0].get("amber"),
       "the bank never came: the figure keeps standing, marked 'bank statement never received', one quiet line", (sp, it))
    # the owner's own figure: no second confirmation
    b_ok, b_code, r4 = BS.type_figure(con, "clinic", D, 530000, "manoj", owner=True, now=due)
    st = {r["id"]: r["status"] for r in con.execute("SELECT id, status FROM bank_standin")}
    ok(b_ok and b_code == "confirmed" and st[r3["id"]] == "superseded" and st[r4["id"]] == "confirmed"
       and BS.standing(con, "clinic", D, now=due)["amount_p"] == 530000 and fired == [D, D], "the owner's own figure stands at once; the earlier row is kept", st)
    # the bank lands
    con.execute("INSERT INTO upi_statement (merchant_id, unit, statement_date, ingested_at) VALUES ('m1','clinic',?,'2030-01-08T15:56:00')", (D,))
    con.executemany("INSERT INTO upi_txn (unit, txn_date, txn_time, amount_p) VALUES ('clinic',?,?,?)", [(D, "10:00", 300000), (D, "11:00", 215000)])
    con.commit()
    ok(BS.standing(con, "clinic", D, now=due) is None, "the bank's statement is in: the function answers None at once -- the bank replaces it by itself")
    it = BS.owner_items(con, ["clinic"], now=due)
    row = dict(con.execute("SELECT * FROM bank_standin WHERE id=?", (r4["id"],)).fetchone())
    ok(row["status"] == "replaced" and row["bank_p"] == 515000 and row["diff_p"] == -15000 and fired == [D, D, D],
       "the typed row is KEPT, marked replaced, with the bank's figure and the difference; the hook is called", (row, fired))
    ok(len(it) == 1 and it[0]["kind"] == "pos_diff" and all(x in it[0]["line"] for x in ("typed ₹5,300", "bank ₹5,150", "difference ₹150")),
       "a difference beyond the tolerance is ONE line: date, typed, bank, difference", it)
    ok(BS.decide(con, r4["id"], "seen", "manoj", now=due)[1] == "seen" and BS.owner_items(con, ["clinic"], now=due) == [], "'seen' takes the line away; the row stays")
    ok(BS.type_figure(con, "clinic", D, 1, "manoj", owner=True, now=due)[1] == "bank_in" and not BS.day(con, "clinic", D, now=due)["show"],
       "once the bank is in, nothing can be typed and nothing is shown")
    # within the tolerance: no line; a typed row overtaken by the bank lapses quietly
    D2 = "2030-01-09"
    due2 = dt.datetime(2030, 1, 10, 10, 30)
    BS.type_figure(con, "medical", D2, 100000, "manoj", owner=True, now=due2)
    _, _, r6 = BS.type_figure(con, "lab", D2, 70000, "labstaff", now=due2)
    con.execute("INSERT INTO upi_statement (merchant_id, unit, statement_date, ingested_at) VALUES ('m2','medical',?,'x'),('m3','lab',?,'x')", (D2, D2))
    con.execute("INSERT INTO upi_txn (unit, txn_date, amount_p) VALUES ('medical',?,?)", (D2, 105000))
    con.commit()
    it = BS.owner_items(con, None, now=due2)
    lab = dict(con.execute("SELECT * FROM bank_standin WHERE id=?", (r6["id"],)).fetchone())
    ok(it == [] and lab["status"] == "lapsed", "bank within the tolerance: no line; a figure the bank overtook before he decided lapses quietly", (it, lab["status"]))
    # the settings
    ok(BS.save_settings(con, "250", "09:15", None)[0] and BS.tolerance_p(con) == 25000 and BM.expect_hhmm(con) == "09:15",
       "the tolerance and the bank's expected time are settings; bank_mpr_status reads the same key")
    D3 = "2030-01-20"
    ok(BM.mpr_state(con, D3, unit="clinic", now=dt.datetime(2030, 1, 21, 9, 10))["state"] == "waiting"
       and BM.mpr_state(con, D3, unit="clinic", now=dt.datetime(2030, 1, 21, 9, 20))["state"] == "not_received"
       and "09:15" in BM.mpr_state(con, D3, unit="clinic", now=dt.datetime(2030, 1, 21, 9, 20))["line"],
       "the bank's status line turns from WAITING to NOT RECEIVED at the setting's time, and says the time")
    ok(not BS.save_settings(con, "abc", None, None)[0] and not BS.save_settings(con, None, "25:99", None)[0] and BS.tolerance_p(con) == 25000,
       "a tolerance that is not a number, or a time that is not a time, is refused and changes nothing")
    BS.save_settings(con, None, None, False)
    ok(BS.type_figure(con, "clinic", D3, 1, "shivani", now=dt.datetime(2030, 1, 21, 11, 0))[1] == "off"
       and not BS.day(con, "clinic", D3, now=dt.datetime(2030, 1, 21, 11, 0))["offer"]
       and BS.type_figure(con, "clinic", D3, 100, "manoj", owner=True, now=dt.datetime(2030, 1, 21, 11, 0))[0],
       "switched off: staff are not offered the field; the owner's own typing still works")
    n = con.execute("SELECT COUNT(*) FROM bank_standin").fetchone()[0]
    ok(n == 7, "no row was ever deleted: all seven figures typed in this part are still in the table", n)
    html = BS.owner_block_html(con, ["clinic", "lab"], True, now=dt.datetime(2030, 1, 21, 11, 0))
    ok("standin_type" in html and "standin_settings" in html and "NK Pathology" in html and "<script" not in html, "the owner's block: his own typing, the settings, the lab as a choice; no script")
    ok(BS.owner_block_html(con, ["clinic"], False, now=due).count("<button") == 0, "a login that is not his sees no button")
    sys.path.remove(kit)
    for m in ("bank_standin", "bank_mpr_status"):
        sys.modules.pop(m, None)


# ============================================================================================ PART 2 -- child: render pages
def child(args):
    """Render a fixed list of pages with the modules found on sys.path (the live code, or the kit over it)."""
    spec = json.load(open(args.spec, encoding="utf-8"))
    os.environ["CLINIC_MONEY_NOW"] = spec["now"]
    os.environ["BANK_STANDIN_NOW"] = spec["now"]
    H = Harness(args.db, spec["paths"])
    out = {}
    for d in spec["clinic_days"]:
        out["match " + d] = H.as_("reception").get("/finance/clinic/match/%s" % d)
        out["blocks " + d] = [200, H.blocks(d, "reception")]
        out["mpr " + d] = H.as_("manoj", "doctor").get_json("/finance/clinic/bank/mpr/%s.json" % d)
    out["owner"] = H.as_("manoj", "doctor").get("/finance/clinic/money")
    for d in spec["medical_days"]:
        out["kal " + d] = H.as_("darpan").get_json("/finance/darpan/kal/api/day?date=%s" % d)
    out["kal owner"] = H.as_("manoj", "doctor").get_json("/finance/darpan/kal/api/owner")
    json.dump(out, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, sort_keys=True)
    return 0


def strip_block(html):
    """The owner's page of the kit, with the one new card taken out -- what the live page must equal."""
    a = html.find("<div class='card' id='postotal'>")
    if a < 0:
        return html
    b = html.find("</details></div>", a)
    return html if b < 0 else html[:a] + html[b + len("</details></div>"):]


def money_print(path):
    """A fingerprint of every table that holds money or the bank's word -- the stand-in may change none of them."""
    con = connect(path)
    out = {}
    for t in ("day_entry", "cash_movement", "upi_statement", "upi_txn", "sale_item", "clinic_register_day", "clinic_day_line",
              "day_line", "day_noncash_bill", "cash_adjustment", "clinic_other_upi", "clinic_physio_day", "clinic_float_event"):
        try:
            rows = con.execute("SELECT * FROM %s ORDER BY 1" % t).fetchall()
            out[t] = (len(rows), hashlib.md5(repr([tuple(r) for r in rows]).encode("utf-8")).hexdigest())
        except sqlite3.OperationalError:
            out[t] = None
    con.close()
    return out


def take_statement(path, unit, d):
    """ON THE COPY: the statement of one unit's day is put aside, as if the bank had not sent it."""
    con = connect(path)
    st = [tuple(r) for r in con.execute("SELECT * FROM upi_statement WHERE unit=? AND statement_date=?", (unit, d))]
    tx = [tuple(r) for r in con.execute("SELECT * FROM upi_txn WHERE unit=? AND txn_date=?", (unit, d))]
    con.execute("DELETE FROM upi_txn WHERE unit=? AND txn_date=?", (unit, d))
    con.execute("DELETE FROM upi_statement WHERE unit=? AND statement_date=?", (unit, d))
    con.commit()
    con.close()
    return st, tx


def give_statement(path, held):
    st, tx = held
    con = connect(path)
    for r in st:
        con.execute("INSERT INTO upi_statement VALUES (%s)" % ",".join("?" * len(r)), r)
    for r in tx:
        con.execute("INSERT INTO upi_txn VALUES (%s)" % ",".join("?" * len(r)), r)
    con.commit()
    con.close()


def one(path, sql, args=()):
    c = connect(path)
    try:
        r = c.execute(sql, args).fetchone()
        return dict(r) if r is not None else None
    finally:
        c.close()


def part2(args, scratch):
    print("PART 2 -- the real pages on a copy of the real database")
    work = os.path.join(scratch, "work.db")
    copy_db(args.db, work)
    con = connect(work)
    have = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if not ok({"upi_statement", "upi_txn", "setting", "unit_role", "clinic_register_day", "darpan_kal_day", "audit_log"} <= have,
              "the copy has the tables this kit reads"):
        return
    pre_rows = con.execute("SELECT COUNT(*) FROM bank_standin").fetchone()[0] if "bank_standin" in have else 0
    note("bank_standin is %s on this database" % (("already there, %d rows" % pre_rows) if "bank_standin" in have else "not there yet (a first install)"))
    r = con.execute("SELECT value FROM setting WHERE key='bank_mpr.expect_hhmm'").fetchone()
    exp = (r[0] if r else "10:00")
    # the clinic: the newest days that are filled, read by Docterz, with the statement applied on D+1 before the expected time
    cdays = [x[0] for x in con.execute(
        "SELECT r.business_date FROM clinic_register_day r JOIN upi_statement s ON s.unit='clinic' AND s.statement_date=r.business_date "
        "WHERE EXISTS (SELECT 1 FROM clinic_day_line l WHERE l.business_date=r.business_date AND l.section IN ('consult','xray','proc')) "
        "AND substr(s.ingested_at,12,5) < ? AND substr(s.ingested_at,1,10) = date(r.business_date,'+1 day') "
        "ORDER BY r.business_date DESC LIMIT 3", (exp,))]
    # Sanjeevni: the newest days Darpan posted that stand on the bank and are plainly settled (complete, no reason, no owner's word)
    mdays = [x[0] for x in con.execute(
        "SELECT k.business_date FROM darpan_kal_day k JOIN upi_statement s ON s.unit='medical' AND s.statement_date=k.business_date "
        "JOIN day_entry e ON e.unit='medical' AND e.business_date=k.business_date "
        "WHERE k.unit='medical' AND k.handed_p IS NOT NULL AND k.online_provisional=0 AND k.state='complete' "
        "AND COALESCE(k.reason,'none')='none' AND k.owner_decision IS NULL ORDER BY k.business_date DESC LIMIT 3")]
    con.close()
    if not ok(len(cdays) >= 1 and len(mdays) >= 1, "found real days to walk: clinic %s · Sanjeevni %s" % (cdays, mdays)):
        return
    Dc, Dm = cdays[0], mdays[0]
    newest = max(cdays[0], mdays[0])
    now_all = (dt.datetime.fromisoformat(newest) + dt.timedelta(days=3, hours=16)).isoformat()   # a quiet afternoon after every day walked

    # ---- (a) live code vs the kit, on identical copies, no figure anywhere ----------------------------
    ov = overlay(args.kit, scratch)
    side_files(ov, args.code)
    res = {}
    for which, paths in (("live", list(args.code)), ("kit", [ov] + list(args.code))):
        dbc = os.path.join(scratch, "cmp_%s.db" % which)
        copy_db(args.db, dbc)
        spec = os.path.join(scratch, "spec_%s.json" % which)
        outp = os.path.join(scratch, "out_%s.json" % which)
        json.dump(dict(now=now_all, paths=paths, clinic_days=cdays, medical_days=mdays), open(spec, "w"))
        p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--child", "--spec", spec, "--out", outp, "--db", dbc],
                           capture_output=True, text=True, timeout=600, cwd=scratch)
        if p.returncode != 0 or not os.path.isfile(outp):
            ok(False, "the %s code renders the pages" % which, (p.stderr or p.stdout)[-900:])
            return
        res[which] = json.load(open(outp, encoding="utf-8"))
    L, K = res["live"], res["kit"]
    for d in cdays:
        ok(L["match " + d] == K["match " + d] and L["match " + d][0] == 200, "clinic %s, bank in, no figure: the morning-match card is byte for byte the live card" % d,
           _first_diff(L["match " + d][1], K["match " + d][1]))
        ok(L["blocks " + d] == K["blocks " + d], "clinic %s: the counter sheet's blocks are byte for byte the live ones" % d, _first_diff(L["blocks " + d][1], K["blocks " + d][1]))
        a, b = dict(L["mpr " + d][1]), dict(K["mpr " + d][1])
        same_state = a.get("state") == b.get("state") or {a.get("state"), b.get("state")} <= {"applied", "late"}
        ok(same_state and a.get("total_p") == b.get("total_p") and a.get("ok"), "clinic %s: the bank's status line carries the same figure (%s)" % (d, b.get("state")), (a, b))
    ok(L["owner"][0] == 200 and K["owner"][0] == 200 and strip_block(K["owner"][1]) == L["owner"][1] and "standin_type" in K["owner"][1],
       "the owner's Clinic money page = the live page + the one folded line for his own typing", _first_diff(L["owner"][1], strip_block(K["owner"][1])))
    for d in mdays:
        a, b = json.loads(json.dumps(L["kal " + d][1])), json.loads(json.dumps(K["kal " + d][1]))
        extra = b.pop("pos_total", None)
        for k in ("online_source", "marg_online_p", "standin"):
            (b.get("calc") or {}).pop(k, None)
        ok(a == b and a.get("ok") and extra is not None and extra.get("ok") and not extra.get("show"),
           "Sanjeevni %s, bank in: Darpan's day is the live day; the field is NOT offered" % d,
           (extra, _first_diff(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))))
    a, b = dict(L["kal owner"][1]), dict(K["kal owner"][1])
    pos = b.pop("pos", None)
    ok(a == b and a.get("ok") and pos and pos.get("ok") and pos.get("can_act"), "the owner's Kal ka hisaab card: the same lines as live, plus what his fold needs",
       (pos, _first_diff(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))))

    # ---- from here: the kit's modules, in this process, on the working copy ---------------------------
    before_money = money_print(work)
    H = Harness(work, [ov] + list(args.code))
    BS = sys.modules["bank_standin"]
    c = connect(work)
    tol = BS.tolerance_p(c)
    c.close()
    eh, em = [int(x) for x in exp.split(":")]

    def pin(d, hh, mm, plus=1):
        t = (dt.datetime.fromisoformat(d) + dt.timedelta(days=plus)).replace(hour=hh, minute=mm).isoformat()
        os.environ["CLINIC_MONEY_NOW"] = t
        os.environ["BANK_STANDIN_NOW"] = t
        return t

    def pin_before(d):
        t = (dt.datetime.fromisoformat(d) + dt.timedelta(days=1)).replace(hour=eh, minute=em) - dt.timedelta(minutes=1)
        os.environ["CLINIC_MONEY_NOW"] = os.environ["BANK_STANDIN_NOW"] = t.isoformat()

    def md(d):
        c = connect(work)
        try:
            return H.cm.match_day(c, d, now=H.cm._now())
        finally:
            c.close()

    # ---- (b) the clinic ------------------------------------------------------------------------------
    print("  -- the clinic, %s" % Dc)
    pin(Dc, 23, 0, plus=20)
    m0 = md(Dc)
    ok(m0["bank_known"] and m0.get("standin") is None, "before: the bank is in for %s" % Dc)
    held = take_statement(work, "clinic", Dc)
    pin_before(Dc)
    code, page = H.as_("reception").get("/finance/clinic/match/%s" % Dc)
    ok(code == 200 and "id=\"postotal\"" not in page and "pos-total" not in page, "statement missing but the bank is not due yet: the card shows NO field")
    code, _p = H.as_("reception").post_form("/finance/clinic/money/%s/pos-total" % Dc, {"amount": "100", "back": "match"})
    ok(code == 409, "…and a figure posted then is refused", code)
    pin(Dc, eh, em)
    m1 = md(Dc)
    expected = m1.get("expected_bank_p")
    flags1 = sorted(f["key"] for f in m1["flags"])
    ok(m1["bank_state"] == "not_received" and "mpr_missing" in flags1, "at the bank's time, still missing: the match says NOT RECEIVED and raises mpr_missing, as today", (m1["bank_state"], flags1))
    code, page = H.as_("reception").get("/finance/clinic/match/%s" % Dc)
    ok(code == 200 and page.count("id=\"postotal\"") == 1 and page.count("name=\"amount\"") == 1 and "POS machine ka UPI total" in page
       and "Dr Manoj ke haan karne par hi gina jayega" in page, "the morning-match card now offers the ONE optional figure, in Roman Hindi")
    blk = H.blocks(Dc, "reception")
    ok(blk.count("id=\"postotal\"") == 1 and "value=\"register\"" in blk, "the counter sheet offers the same one figure")
    if H.reg:
        code, page = H.as_("reception").get("/finance/clinic/register/%s" % Dc)
        ok(code == 200 and page.count("id=\"postotal\"") == 1, "…and it is on the counter sheet's own page", code)
    code, page = H.as_("reception").post_form("/finance/clinic/money/%s/pos-total" % Dc, {"amount": "", "back": "match"})
    ok(code == 400 and "Kuch save nahi hua" in page, "an empty box saves nothing and says so")
    code, page = H.as_("darpan").post_form("/finance/clinic/money/%s/pos-total" % Dc, {"amount": "5", "back": "match"})
    ok(code == 403, "a login with no place in the clinic is refused", code)
    typed_amt = max(int(expected or 0), 0)
    code, _p = H.as_("reception").post_form("/finance/clinic/money/%s/pos-total" % Dc, {"amount": "%.2f" % (typed_amt / 100.0), "back": "match"})
    ok(code == 302, "reception types the figure (what Docterz expects in the bank that day)", code)
    m2 = md(Dc)
    ok(m2.get("standin") is None and sorted(f["key"] for f in m2["flags"]) == flags1 and m2["lines"] == m1["lines"] and m2["notes"] == m1["notes"],
       "TYPED, NOT CONFIRMED: the match is exactly what it was -- same verdict, same flags, same notes")
    code, page = H.as_("reception").get("/finance/clinic/match/%s" % Dc)
    ok("Dr Manoj ki haan baaki" in page and "Dobara likho" in page, "the card tells the desk: written, waiting for Dr Manoj's yes")
    code, page = H.as_("manoj", "doctor").get("/finance/clinic/money")
    ok(code == 200 and "POS total waiting for you — Clinic" in page and "typed by reception" in page and BS.human(Dc) in page
       and "value=\"confirm\"" in page and "value=\"reject\"" in page, "HIS PAGE: one line -- who typed it, which date, the figure -- with Confirm and Reject")
    code, page = H.as_("bhawna", "doctor").get("/finance/clinic/money")
    ok(code == 200 and "POS total waiting for you — Clinic" in page and "value=\"confirm\"" not in page and "standin_type" not in page,
       "Dr Bhawna's login sees the line but no button: only his login confirms")
    rid = one(work, "SELECT id FROM bank_standin WHERE unit='clinic' AND business_date=? AND status='typed'", (Dc,))["id"]
    code, page = H.as_("bhawna", "doctor").post_form("/finance/clinic/money", {"act": "standin_decide", "id": str(rid), "word": "confirm"})
    ok("Only Dr Manoj" in page and md(Dc).get("standin") is None, "…and a confirm posted from her login changes nothing")
    code, page = H.as_("manoj", "doctor").post_form("/finance/clinic/money", {"act": "standin_decide", "id": str(rid), "word": "confirm"})
    ok(code == 200 and "Confirmed:" in page and "provisional — POS total, bank not in" in page, "he confirms")
    m3 = md(Dc)
    keys3 = sorted(f["key"] for f in m3["flags"])
    ok(m3.get("standin") and m3["standin"]["amount_p"] == typed_amt and "mpr_missing" not in keys3 and "pos_diff" not in keys3
       and any("provisional — POS total, bank not in" in n for n in m3["notes"]) and m3.get("standin_diff_p") == 0,
       "AFTER HIS CONFIRM: the bank part stands on the POS total, marked provisional; mpr_missing is gone; no new flag", (keys3, m3["notes"][-2:]))
    c = connect(work)
    fl = {r["key"]: r["status"] for r in c.execute("SELECT key, status FROM clinic_money_flag WHERE business_date=?", (Dc,))}
    c.close()
    ok(fl.get("mpr_missing") == "cleared", "…and the day was worked again by itself: the stored mpr_missing flag is now 'cleared'", fl)
    code, page = H.as_("reception").get("/finance/clinic/match/%s" % Dc)
    ok("Dr Manoj ne haan kar di" in page and page.count("name=\"amount\"") == 0 and "provisional — POS total, bank not in" in page,
       "the desk's card: confirmed, no box any more, and the day says provisional")
    # his own figure, wrong on purpose -> one flag
    wrong = typed_amt + tol + 5000
    code, page = H.as_("manoj", "doctor").post_form("/finance/clinic/money", {"act": "standin_type", "unit": "clinic", "date": Dc, "amount": "%.2f" % (wrong / 100.0)})
    m4 = md(Dc)
    k4 = [f for f in m4["flags"] if f["code"] == "pos_diff"]
    ok("Saved:" in page and m4["standin"]["amount_p"] == wrong and len(k4) == 1 and k4[0]["amount_p"] == tol + 5000 and not k4[0]["owner"],
       "his own figure stands at once (no second confirmation); beyond the tolerance against Docterz it is ONE flag on the staff card", k4)
    # the settings on his page
    code, page = H.as_("manoj", "doctor").post_form("/finance/clinic/money", {"act": "standin_settings", "tolerance": str((tol + 10000) // 100), "expect": exp, "on": "1"})
    ok("Saved:" in page and not [f for f in md(Dc)["flags"] if f["code"] == "pos_diff"], "he raises the tolerance on screen: the same difference is no longer a flag")
    H.as_("manoj", "doctor").post_form("/finance/clinic/money", {"act": "standin_settings", "tolerance": str(tol // 100), "expect": exp, "on": "1"})
    # the bank lands
    give_statement(work, held)
    pin(Dc, 23, 0, plus=20)                                    # the same clock as the reading taken before the walk
    m5 = md(Dc)
    ok(m5["bank_known"] and m5.get("standin") is None and sorted(f["key"] for f in m5["flags"]) == sorted(f["key"] for f in m0["flags"])
       and m5["lines"] == m0["lines"], "THE BANK'S STATEMENT LANDS: the match is the bank's own again -- the same verdict and flags as before the walk",
       (m0["lines"], m5["lines"]))
    code, page = H.as_("manoj", "doctor").get("/finance/clinic/money")
    c = connect(work)
    rows = [dict(r) for r in c.execute("SELECT * FROM bank_standin WHERE unit='clinic' AND business_date=? ORDER BY id", (Dc,))]
    c.close()
    last = rows[-1]
    ok([r["status"] for r in rows] == ["superseded", "replaced"] and last["bank_p"] == m5["bank_p"] and last["diff_p"] == m5["bank_p"] - wrong,
       "both typed rows are KEPT (superseded, replaced) with the bank's figure and the difference on the last",
       [(r["status"], r["amount_p"], r["bank_p"], r["diff_p"]) for r in rows])
    want_line = abs(last["diff_p"]) > tol
    ok(("Bank statement in — Clinic" in page) == want_line and "POS total waiting for you" not in page,
       "his page: %s" % ("ONE line -- date, typed, bank, difference" if want_line else "no line (within the tolerance)"))
    if want_line:
        code, page = H.as_("manoj", "doctor").post_form("/finance/clinic/money", {"act": "standin_decide", "id": str(last["id"]), "word": "seen"})
        ok("Bank statement in — Clinic" not in page, "'Seen' takes the line away")
    code, page = H.as_("reception").get("/finance/clinic/match/%s" % Dc)
    ok("id=\"postotal\"" not in page, "the desk's card: no POS box, the bank is in")
    # the lab: no page of its own -> his typing on the clinic page
    labday = (one(work, "SELECT date(MAX(statement_date),'+1 day') d FROM upi_statement WHERE unit='lab'") or {}).get("d")
    if labday:
        pin(labday, eh, em, plus=2)
        code, page = H.as_("manoj", "doctor").post_form("/finance/clinic/money", {"act": "standin_type", "unit": "lab", "date": labday, "amount": "1234"})
        c = connect(work)
        sp = BS.standing(c, "lab", labday)
        c.close()
        ok("Saved:" in page and "NK Pathology" in page and sp and sp["amount_p"] == 123400,
           "the third unit of the statement store (NK Pathology): he types its figure on Clinic money and it stands")

    # ---- (c) Sanjeevni -------------------------------------------------------------------------------
    print("  -- Sanjeevni, %s" % Dm)
    QROW = "SELECT * FROM darpan_kal_day WHERE unit='medical' AND business_date=?"
    pin(Dm, 23, 0, plus=20)
    row0 = one(work, QROW, (Dm,))
    c = connect(work)
    calc0 = H.dk.compute_day(c, Dm)
    c.close()
    ok(calc0["statement_in"] and calc0["online_source"] == "bank", "before: Sanjeevni's %s stands on the bank" % Dm)
    heldm = take_statement(work, "medical", Dm)
    c = connect(work)
    H.dk.ensure_schema(c)
    calc1 = H.dk.compute_day(c, Dm)
    H.dk._decide(c, Dm, calc1, dict(c.execute(QROW, (Dm,)).fetchone()), "walk")
    c.commit()
    c.close()
    row1 = one(work, QROW, (Dm,))
    ok(calc1["online_source"] == "marg" and calc1["online_provisional"] == 1 and row1["online_provisional"] == 1,
       "statement put aside on the copy: the day stands on Marg's own UPI/card figure, provisional -- as it does today")
    pin_before(Dm)
    code, j = H.as_("darpan").get_json("/finance/darpan/kal/api/day?date=%s" % Dm)
    ok(code == 200 and j["pos_total"]["ok"] and not j["pos_total"]["show"], "before the bank's time: Darpan's form offers nothing", j.get("pos_total"))
    code, j = H.as_("darpan").post_json("/finance/darpan/kal/api/pos-total", {"date": Dm, "amount_p": 100})
    ok(code == 409 and j.get("error") == "not_due", "…and a figure posted then is refused", (code, j))
    pin(Dm, eh, em)
    code, j = H.as_("darpan").get_json("/finance/darpan/kal/api/day?date=%s" % Dm)
    ok(j["pos_total"]["offer"] and j["pos_total"]["show"] and j["pos_total"]["typed"] is None, "after the bank's time, statement missing: his same form offers the one optional figure")
    code, page = H.as_("darpan").get("/finance/darpan/kal")
    ok(code == 200 and "कल का UPI total — POS मशीन से" in page and "डॉक्टर साहब के हाँ करने पर ही यह गिना जाएगा" in page and "function posField" in page,
       "his page carries the field's words in Devanagari")
    pos_amt = int(calc1["online_p"]) + 123400
    code, j = H.as_("amir").post_json("/finance/darpan/kal/api/pos-total", {"date": Dm, "amount_p": pos_amt})
    ok(code == 403, "a viewer of the pharmacy cannot type it", code)
    code, j = H.as_("darpan").post_json("/finance/darpan/kal/api/pos-total", {"date": Dm, "amount_p": "abc"})
    ok(code == 400, "a figure that is not a number is refused")
    code, j = H.as_("darpan").post_json("/finance/darpan/kal/api/pos-total", {"date": Dm, "amount_p": pos_amt})
    ok(code == 200 and j.get("state") == "saved" and j["pos_total"]["typed"]["amount_p"] == pos_amt, "Darpan types the POS total", (code, j))
    code, j = H.as_("darpan").get_json("/finance/darpan/kal/api/day?date=%s" % Dm)
    row2 = one(work, QROW, (Dm,))
    same = all(row2[k] == row1[k] for k in ("online_p", "online_provisional", "expected_p", "diff_p", "state", "verdict", "reason"))
    ok(j["calc"]["online_source"] == "marg" and j["calc"]["online_p"] == calc1["online_p"] and j["calc"]["expected_p"] == calc1["expected_p"] and same,
       "TYPED, NOT CONFIRMED: the day stands exactly as it did -- Marg's figure, the same expected cash, the same decision")
    code, j = H.as_("darpan").get_json("/finance/darpan/kal/api/owner")
    ok(code == 403, "Darpan cannot open the owner's card")
    code, j = H.as_("manoj", "doctor").get_json("/finance/darpan/kal/api/owner")
    first = (j.get("items") or [{}])[0]
    ok(code == 200 and first.get("kind") == "pos_typed" and "typed by darpan" in first.get("line", "") and "Sanjeevni" in first.get("line", "")
       and BS.human(Dm) in first.get("line", "") and j["pos"]["can_act"],
       "HIS CARD (Kal ka hisaab on Approvals): the first line is the typed figure -- who, which date, the figure", first)
    rid = first.get("id")
    code, j2 = H.as_("darpan").post_json("/finance/darpan/kal/api/pos-total/decide", {"id": rid, "word": "confirm"})
    ok(code == 403, "Darpan cannot confirm his own figure", code)
    code, j2 = H.as_("manoj", "doctor").post_json("/finance/darpan/kal/api/pos-total/decide", {"id": rid, "word": "confirm"})
    ok(code == 200 and j2.get("state") == "confirmed", "he confirms", (code, j2))
    code, j = H.as_("darpan").get_json("/finance/darpan/kal/api/day?date=%s" % Dm)
    row3 = one(work, QROW, (Dm,))
    cc = j["calc"]
    ok(cc["online_source"] == "pos" and cc["online_p"] == pos_amt and cc["online_provisional"] == 1 and not cc["statement_in"]
       and cc["standin"]["label"] == "provisional — POS total, bank not in" and cc["marg_online_p"] == calc1["online_p"]
       and cc["expected_p"] == calc1["expected_p"] - 123400,
       "AFTER HIS CONFIRM: the online figure is the POS total, STILL provisional and marked so; expected cash moves by exactly the difference", cc)
    ok(row3["online_p"] == pos_amt and row3["online_provisional"] == 1 and row3["expected_p"] == cc["expected_p"]
       and row3["diff_p"] == row3["handed_p"] - cc["expected_p"], "…and the day was decided again on it by itself (the stored day carries the new figures)",
       {k: row3[k] for k in ("online_p", "online_provisional", "expected_p", "diff_p", "state")})
    ok(j["pos_total"]["confirmed"]["amount_p"] == pos_amt and not j["pos_total"]["offer"], "Darpan's form: confirmed, the box is gone")
    code, j = H.as_("manoj", "doctor").post_json("/finance/darpan/kal/api/pos-total/settings", {"tolerance": "x", "expect": exp})
    ok(code == 400, "a bad setting from the Approvals card is refused")
    give_statement(work, heldm)
    code, j = H.as_("darpan").get_json("/finance/darpan/kal/api/day?date=%s" % Dm)
    row4 = one(work, QROW, (Dm,))
    c = connect(work)
    srow = [dict(r) for r in c.execute("SELECT * FROM bank_standin WHERE unit='medical' AND business_date=? ORDER BY id", (Dm,))]
    c.close()
    keys = ("net_sale_p", "home_p", "proc_p", "online_p", "online_provisional", "expected_p", "diff_p", "state", "verdict", "reason", "handed_p", "handed_to",
            "owner_decision", "received_at", "landed_movement_id")
    back = all(row4[k] == row0[k] for k in keys)
    ok(j["calc"]["online_source"] == "bank" and j["calc"]["online_provisional"] == 0 and not j["pos_total"]["show"] and back,
       "THE BANK'S STATEMENT LANDS: the day is the bank's own again and is decided EXACTLY as before the walk began",
       {k: (row0[k], row4[k]) for k in keys if row4[k] != row0[k]})
    ok(len(srow) == 1 and srow[0]["status"] == "replaced" and srow[0]["bank_p"] == calc0["online_p"] and srow[0]["diff_p"] == calc0["online_p"] - pos_amt,
       "the typed row is kept: replaced, with the bank's figure and the difference", srow)
    code, j = H.as_("manoj", "doctor").get_json("/finance/darpan/kal/api/owner")
    diffs = [i for i in j.get("items") or [] if i.get("kind") == "pos_diff"]
    want = bool(srow) and abs(srow[0]["diff_p"] or 0) > tol
    ok((len(diffs) == 1) == want and (not want or ("typed ₹" in diffs[0]["line"] and "bank ₹" in diffs[0]["line"] and "difference ₹" in diffs[0]["line"])),
       "his card: ONE line -- date, typed, bank, difference" if want else "his card: no line (within the tolerance)", diffs)

    # ---- (d) nothing that holds money changed ----------------------------------------------------------
    after_money = money_print(work)
    changed = [t for t in before_money if before_money[t] != after_money[t]]
    ok(changed == [], "NO MONEY ROW CHANGED: day_entry, cash_movement, the bank's statements and payments, the sale, the counter sheet -- identical before and after", changed)
    n = one(work, "SELECT COUNT(*) n FROM bank_standin")["n"]
    ok(n >= pre_rows + 4, "every figure typed in this walk is still a row (%d rows; nothing deleted)" % n)
    note("the database it was pointed at was opened read-only and copied; the walk wrote only under its scratch folder")


def _first_diff(a, b):
    if a == b:
        return ""
    n = min(len(a), len(b))
    i = next((k for k in range(n) if a[k] != b[k]), n)
    return "differs at %d: live …%r… kit …%r…" % (i, a[max(0, i - 60):i + 80], b[max(0, i - 60):i + 80])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kit", default=HERE)
    ap.add_argument("--code", action="append", default=[])
    ap.add_argument("--finance", default=None)            # accepted for the installer's habit; the same as one more --code
    ap.add_argument("--db")
    ap.add_argument("--child", action="store_true")
    ap.add_argument("--spec")
    ap.add_argument("--out")
    ap.add_argument("--part1-only", action="store_true")
    args = ap.parse_args()
    if args.child:
        return child(args)
    if args.finance and args.finance not in args.code:
        args.code.insert(0, args.finance)
    for f in KIT_PY + KIT_OTHER + ("finance_approvals.html",):
        if not os.path.isfile(os.path.join(args.kit, f)):
            print("WALK_S496 RED the kit has no %s" % f)
            return 1
    fa = open(os.path.join(args.kit, "finance_approvals.html"), encoding="utf-8").read()
    print("PART 0 -- the kit's own files")
    ok(all(x in fa for x in ("function kalPosFold", "function kalPosBtn", "/finance/darpan/kal/api/pos-total/decide", ">Confirm</button>", ">Reject</button>")),
       "the Approvals page carries his Confirm / Reject, his own typing and the settings")
    scratch = tempfile.mkdtemp(prefix="walk_s496_")
    try:
        part1(args.kit)
        if not args.part1_only:
            if not args.db or not args.code:
                print("WALK_S496 RED part 2 needs --db and --code")
                return 1
            part2(args, scratch)
    except Exception as ex:                                      # noqa: BLE001
        import traceback                                         # noqa: PLC0415
        traceback.print_exc()
        ok(False, "the walk ran to its end", repr(ex))
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    bad = CHECKS.count(False)
    print("WALK_S496 %s" % (("GREEN %d checks" % len(CHECKS)) if not bad else ("RED %d failed of %d" % (bad, len(CHECKS)))))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
