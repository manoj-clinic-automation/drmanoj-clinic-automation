#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""walk_s639.py -- the LIVE-SHAPE walk of kit S639_PARCHI_DESK (D775). Made-up patients, made-up IDs, a temp database.

    python3 walk_s639.py <dir with the NEW slip_log.py + parchi_desk.py> <dir with the rest: slip_adjust ...> [--old|--no-desk]

The real Flask shape: slip_log.init(app, db, require, audit) mounts the slips, slip_adjust and the desk; the desk's doors
are asked over the test client as Shavez and as the owner. --old runs it on the live slip_log.py: exactly the S639
checks go red, none of the older ones. --no-desk proves the new slip_log stands without parchi_desk.py.
The last line is the verdict the installer reads."""
import json
import os
import shutil
import sqlite3
import sys
import tempfile

NEW, REST = sys.argv[1], sys.argv[2]
OLD = "--old" in sys.argv
NODESK = "--no-desk" in sys.argv
sys.path[:0] = [NEW, REST]
os.environ["SLIP_NOW"] = "2026-10-24T10:30:00"
if NODESK:
    class _Block:
        def find_spec(self, name, path=None, target=None):
            if name == "parchi_desk":
                raise ImportError("hidden by the walk")
            return None
    sys.meta_path.insert(0, _Block())

import flask                                              # noqa: E402

TMP = tempfile.mkdtemp(prefix="s639walk_")
DB = os.path.join(TMP, "f.db")
CUR = {"user": "shavez"}
ROLES = {"shavez": ["maker"], "alisha": ["maker"], "manoj": ["checker"], "nobody": []}
TODAY, YDAY = "2026-10-24", "2026-10-23"


def db():
    if "con" not in flask.g:
        c = sqlite3.connect(DB)
        c.row_factory = sqlite3.Row
        flask.g.con = c
    return flask.g.con


def require(*roles, unit="slips"):
    have = set(ROLES[CUR["user"]])
    if not have.intersection(roles):
        return None, (flask.jsonify(ok=False, error="not_permitted"), 403)
    return dict(user=CUR["user"], role="staff", roles=sorted(have)), None


def audit(con, table, row_id, action, before=None, after=None, who=""):
    con.execute("INSERT INTO audit_log (table_name,row_id,action,before_json,after_json,by_whom,at) VALUES (?,?,?,?,?,?,?)",
                (table, row_id, action, before, after, who, "now"))


SEED = """
CREATE TABLE audit_log (id INTEGER PRIMARY KEY, table_name TEXT, row_id INTEGER, action TEXT, before_json TEXT, after_json TEXT,
  by_whom TEXT, at TEXT);
CREATE TABLE setting (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE clinic_day_revenue (business_date TEXT PRIMARY KEY, taken_at TEXT, total_amount_p INTEGER DEFAULT 0);
CREATE TABLE clinic_day_line (business_date TEXT, section TEXT, sn INTEGER, patient TEXT DEFAULT '', clinic_id TEXT DEFAULT '',
  amount_p INTEGER DEFAULT 0, mode TEXT DEFAULT '', gateway_ref TEXT DEFAULT '', shift TEXT DEFAULT '');
CREATE TABLE patient_ref (id INTEGER PRIMARY KEY, clinic_id TEXT, name TEXT, phone_last4 TEXT, merged_into TEXT, last_seen TEXT);
CREATE TABLE owner_service (id INTEGER PRIMARY KEY, kind TEXT, name TEXT, price_p INTEGER, side TEXT, status TEXT, active INTEGER);
INSERT INTO owner_service VALUES (1,'xray','Knee AP & Lat',100000,'ask','approved',1),(2,'xray','Wrist AP & Lat',50000,'ask','approved',1),
  (3,'proc','ILI knee',50000,'ask','approved',1),(4,'proc','Dressing',10000,'','approved',1);
INSERT INTO patient_ref (clinic_id,name,phone_last4,last_seen) VALUES ('5001','Patient One','0000','2026-10-01'),('5002','Patient Two','0000','2026-10-01');
INSERT INTO clinic_day_line (business_date,section,sn,patient,clinic_id,amount_p,mode) VALUES ('2026-10-20','consult',1,'Patient Two','5002',60000,'Cash');
"""
RES = []


def ok(name, cond, s639=True):
    RES.append((name, bool(cond), s639))
    print(("  ok   " if cond else "  RED  ") + name)


def main():
    import slip_log as SL
    app = flask.Flask("walk")
    SL.init(app, db, require, audit, unit="slips")
    with app.app_context():
        con = db()
        con.executescript(SEED)
        SL._schema_done = False
        SL.ensure(con)
        con.execute("UPDATE slip_book SET start_no=first_no+10")
        con.commit()
    cl = app.test_client()

    def get(p, who="shavez"):
        CUR["user"] = who
        r = cl.get(p)
        return r.status_code, r.get_data(as_text=True)

    def post(p, body, who="shavez"):
        CUR["user"] = who
        r = cl.post(p, data=json.dumps(body), content_type="application/json")
        try:
            return r.status_code, r.get_json() or {}
        except Exception:                                # noqa: BLE001
            return r.status_code, {}

    # --- older behaviour, both files
    st, h = get("/finance/slips?s=opd")
    ok("A  (older) the OPD parchi page opens", st == 200 and "slip_no" in h, s639=False)
    CUR["user"] = "shavez"
    r = cl.post("/finance/slips/save", data={"series": "opd", "slip_no": "19211", "clinic_id": "5001", "sec": "opd"})
    with app.app_context():
        n = db().execute("SELECT COUNT(*) FROM slip WHERE series='opd' AND slip_no=19211 AND state='ok'").fetchone()[0]
    ok("B  (older) the old OPD form still saves a parchi", r.status_code == 303 and n == 1, s639=False)
    st, h = get("/finance/slips/report/%s" % TODAY, "manoj")
    ok("C  (older) the night report opens", st == 200, s639=False)

    # --- the desk
    st, h = get("/finance/slips/desk")
    has = st == 200 and "Parchi desk" in h and "__BOOT__" not in h
    ok("1  the desk opens for Shavez, one page: OPD, X-ray/Proc, Blood test, the day's list", has and "b-opd" in h and "b-xp" in h and "b-bl" in h)
    st2, h2 = get("/finance/slips/desk", "manoj")
    ok("2  ... and for the owner, in English", st2 == 200 and '"eng": true' in h2)
    st3, _ = get("/finance/slips/desk", "nobody")
    ok("3  a login with no role is refused", st3 == 200 and not ("b-opd" in _))
    st, j = post("/finance/slips/desk/api/save", {"series": "opd", "slip_no": "19212", "clinic_id": "5002", "day": ""})
    ok("4  OPD saves through log_slip (the next number, the name)", j.get("ok") and "Patient Two" in j.get("msg", ""))
    chips = [o["cid"] for o in (j.get("state") or {}).get("opd", [])]
    ok("5  the saved OPD appears at once in the day's state (the live chips)", "5002" in chips and "5001" in chips)
    ok("6  the next number moves on", (j.get("state") or {}).get("nx_opd") == 19213)
    st, j = post("/finance/slips/desk/api/save", {"series": "xp", "slip_no": "1011", "clinic_id": "5002", "day": "",
                                                    "items": [{"id": 1, "k": "xray", "side": "R"}, {"id": 3, "k": "proc", "side": "L",
                                                                                                         "disc": "100", "why": "poor"}]})
    with app.app_context():
        it = db().execute("SELECT name, side, price_p, discount_p FROM slip_item ORDER BY id").fetchall()
        pend = db().execute("SELECT COUNT(*) FROM slip_adjust WHERE state='pending' AND kind='discount'").fetchone()[0]
    ok("7  X-ray/Proc saves the tapped tiles with side and the rate", j.get("ok") and [tuple(x) for x in it][:1] == [("Knee AP & Lat", "R", 100000, 0)])
    ok("8  a chhoot goes for approval exactly as before (slip_adjust pending)", pend == 1 and it[1]["discount_p"] == 10000)
    st, j = post("/finance/slips/desk/api/save", {"series": "xp", "slip_no": "1012", "clinic_id": "5002", "day": "",
                                                    "items": [{"id": 2, "k": "xray", "side": "L"}, {"id": 2, "k": "xray", "side": "L"}]})
    ok("9  a duplicate the person chose to Keep is saved as two lines", j.get("ok") and len(j["state"]["xp"][-1]["items"]) == 2)
    st, j = post("/finance/slips/desk/api/save", {"series": "xp", "slip_no": "1013", "clinic_id": "5002", "day": "",
                                                    "items": [{"id": 1, "k": "xray", "disc": "100"}]})
    ok("10 every old rule holds: a chhoot with no reason is refused", not j.get("ok") and "wajah" in (j.get("err") or ""))
    st, j = post("/finance/slips/desk/api/save", {"series": "opd", "slip_no": "19260", "clinic_id": "5001", "day": ""})
    ok("11 a big jump in the number asks 'Haan, yahi number'", not j.get("ok") and j.get("ask") == "gap_ok")
    st, j = post("/finance/slips/desk/api/save", {"series": "opd", "slip_no": "19260", "clinic_id": "5001", "day": "", "gap_ok": True})
    with app.app_context():
        miss = db().execute("SELECT COUNT(*) FROM slip WHERE series='opd' AND state='missing'").fetchone()[0]
    ok("12 ... and saves once confirmed, the numbers between left as chhoote", j.get("ok") and miss == 47 and j["state"]["missing"])
    st, j = post("/finance/slips/desk/api/save", {"series": "opd", "slip_no": "19261", "clinic_id": "9999", "day": ""})
    ok("13 a clinic ID far ahead asks 'ID sahi hai'", not j.get("ok") and j.get("ask") == "id_ok")
    st, j = post("/finance/slips/desk/api/undo", {"kind": "slip", "id": 999})
    ok("14 Undo refuses anything but your own last entry", not j.get("ok"))
    with app.app_context():
        last = __import__("parchi_desk").state(db(), TODAY, "shavez")["last"] if not (OLD or NODESK) else None
    st, j = post("/finance/slips/desk/api/undo", {"kind": (last or {}).get("kind"), "id": (last or {}).get("id")})
    with app.app_context():
        v = db().execute("SELECT state FROM slip WHERE series='opd' AND slip_no=19260").fetchone()
        miss2 = db().execute("SELECT COUNT(*) FROM slip WHERE series='opd' AND state='missing'").fetchone()[0]
    ok("15 Undo takes back the last parchi and the chhoote numbers its save made", j.get("ok") and v and v[0] == "void" and miss2 == 0)
    st, j = post("/finance/slips/desk/api/undo", {"kind": ((j.get("state") or {}).get("last") or {}).get("kind"),
                                                    "id": ((j.get("state") or {}).get("last") or {}).get("id")})
    with app.app_context():
        pend2 = db().execute("SELECT COUNT(*) FROM slip_adjust WHERE state='pending'").fetchone()[0]
    ok("16 Undo of the next one back (the duplicate parchi) works, and a chhoot left pending stays only on live parchis",
       j.get("ok") and pend2 == 1)
    st, j = post("/finance/slips/desk/api/blood", {"clinic_id": "5002"})
    ok("17 Blood test saves from a tapped patient", j.get("ok") and j["state"]["blood"] and j["state"]["blood"][0]["cid"] == "5002")
    st, j = post("/finance/slips/desk/api/blood", {"clinic_id": "5002"})
    ok("18 ... once a day, the old page's rule", not j.get("ok") and "pehle se" in (j.get("err") or ""))
    st, j = post("/finance/slips/desk/api/save", {"series": "opd", "slip_no": "19213", "clinic_id": "5001", "day": YDAY})
    with app.app_context():
        dd = db().execute("SELECT day FROM slip WHERE series='opd' AND slip_no=19213 AND state='ok'").fetchone()
    ok("19 a late parchi lands on its own day (LATE_DAYS)", j.get("ok") and dd and dd[0] == YDAY)
    st, j = post("/finance/slips/desk/api/save", {"series": "opd", "slip_no": "19214", "clinic_id": "5001", "day": "2026-09-01"})
    ok("20 a day beyond the late window is refused", not j.get("ok"))
    st, j = post("/finance/slips/desk/api/save", {"series": "opd", "slip_no": "19215", "clinic_id": "5001", "day": ""}, who="manoj")
    ok("21 the owner can use the desk when staff are away", j.get("ok"))
    st, h = get("/finance/slips/report/%s" % TODAY, "manoj")
    ok("22 the night report no longer asks for the room's Paid / Done", st == 200 and "room did not tick" not in h)
    st, h = get("/finance/slips", "shavez")
    ok("23 the menu offers the desk first; the room page has no count", "/finance/slips/desk" in h and "purana page" in h)
    ok("24 the owner's report links the desk", "/finance/slips/desk" in get("/finance/slips/report/%s" % TODAY, "manoj")[1])
    red = [n for n, c, _s in RES if not c]
    green = len(RES) - len(red)
    if OLD or NODESK:
        print("%d S639 check(s) red · %d older red · %d green" % (len([1 for n, c, s in RES if not c and s]),
                                                                   len([1 for n, c, s in RES if not c and not s]), green))
    else:
        print("%d of %d green" % (green, len(RES)))


if __name__ == "__main__":
    try:
        main()
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
