#!/usr/bin/env python3
"""walk_s768.py FILES_DIR SHARED_DIR FINANCE_DIR [--control]
A walk on MADE-UP rows (no live data): Stock milaan's stockmatch.py from FILES_DIR (the kit's, or the live one for the control),
section_map.py from FINANCE_DIR, a stand-in scan_register. Last line: 'WALK S768 GREEN' or, with --control on the live files,
'CONTROL S768 RED as it must be'."""
import datetime as dt
import json
import os
import sqlite3
import sys
import tempfile
import types

FILES, SHARED, FIN = sys.argv[1], sys.argv[2], sys.argv[3]
CONTROL = "--control" in sys.argv
sys.path[:0] = [FILES, FIN, SHARED]
for m in ("stockmatch", "section_count", "section_map", "scan_register"):
    sys.modules.pop(m, None)

from flask import Flask, g, jsonify  # noqa: E402

SCANS = {"open": []}
SR = types.ModuleType("scan_register")
SR.sup_norm = lambda s: " ".join(str(s or "").upper().replace(".", " ").split())
SR.register = lambda con, month: dict(scans=[dict(x) for x in SCANS["open"] if x.get("month") == month])
sys.modules["scan_register"] = SR

TMP = tempfile.mkdtemp(prefix="w768_")
DB = os.path.join(TMP, "f.db")
TODAY = dt.date.today()
D0 = TODAY - dt.timedelta(days=1)
DMY = lambda d: d.strftime("%d-%m-%Y")  # noqa: E731
ISO = lambda d: d.isoformat()  # noqa: E731

con = sqlite3.connect(DB)
con.executescript("""
CREATE TABLE stock_snapshot (as_on TEXT, item TEXT, qty INTEGER, packing TEXT, pack_size INTEGER, loaded_at TEXT, source TEXT);
CREATE TABLE sale_line_item (id INTEGER PRIMARY KEY, day_entry_id INTEGER, ingest_batch_id INTEGER, unit TEXT, business_date TEXT, bill_no TEXT,
  is_return INTEGER, seq INTEGER, item_name TEXT, item_key TEXT, pack TEXT, qty_raw TEXT, amount_p INTEGER, expiry_ym TEXT, batch TEXT);
CREATE TABLE purchase_line (id INTEGER PRIMARY KEY, supplier_norm TEXT, bill_no TEXT, bill_date TEXT, month TEXT, item TEXT, packing TEXT, batch TEXT,
  expiry TEXT, tax TEXT, qty REAL, free REAL, rate_p INTEGER, discount_pct REAL, amount_p INTEGER, net_rate_p INTEGER, net_amount_p INTEGER,
  loose_qty REAL, purchase_rate_p INTEGER, direction TEXT, source_md5 TEXT, line_type TEXT);
CREATE TABLE marg_hand_change (id INTEGER PRIMARY KEY, k20 TEXT, item TEXT, kind TEXT, day_from TEXT, day_to TEXT, marg_from REAL, marg_to REAL,
  system_moved REAL, shift REAL, pair_item TEXT, found_at TEXT, status TEXT, status_at TEXT, hist INTEGER);
CREATE TABLE amir_job (id INTEGER PRIMARY KEY, key TEXT NOT NULL UNIQUE, kind TEXT NOT NULL, subject TEXT NOT NULL, text_hi TEXT, sub_hi TEXT,
  created_at TEXT NOT NULL, created_by TEXT, show_from TEXT, said_at TEXT, said_by TEXT, said_what TEXT, done_at TEXT, done_how TEXT, reopened_at TEXT);
CREATE TABLE audit_log (id INTEGER PRIMARY KEY, table_name TEXT, row_id INTEGER, action TEXT, before_json TEXT, after_json TEXT, by_whom TEXT, at TEXT);
CREATE TABLE stock_count (id INTEGER PRIMARY KEY, unit TEXT, marg_as_on TEXT, status TEXT, section TEXT);
INSERT INTO stock_count (unit, marg_as_on, status) VALUES ('medical','06-09-2026','submitted');
CREATE TABLE stock_item_section (item_key TEXT PRIMARY KEY, item TEXT NOT NULL, section TEXT NOT NULL, source TEXT NOT NULL, seeded_as TEXT, by_user TEXT, at TEXT NOT NULL);
INSERT INTO stock_item_section VALUES ('CAST SHOE S TYNOR','CAST SHOE S TYNOR','Orthotics','owner','Consumables','manoj','2026-10-01T10:00:00');
""")
SNAP0 = [("KNEE SUPPORT M HINGED", 1), ("KNEE SUPPORT L HINGED", 2), ("CAST SHOE M TYNOR", 2), ("CAST SHOE L TYNOR", 1),
         ("SOFT COLLAR BODY AID S", 0), ("ARM SLING XL UNISON", 3), ("KNEE CAP UNISON XXL LYCRA", 1), ("ACILOC 300", 77)]
for it, q in SNAP0:
    con.execute("INSERT INTO stock_snapshot VALUES (?,?,?,?,?,?,?)", (DMY(D0 - dt.timedelta(days=1)), it, q, "1*1", 1 if it != "ACILOC 300" else 20, "x", "push_snapshot"))
con.execute("INSERT INTO purchase_line (supplier_norm, bill_no, bill_date, item, qty, free, direction, source_md5, line_type) VALUES "
            "('YUVIKA SURGICALS','585','2026-09-05','KNEE SUPPORT HINGED M',4,0,'PURCHASE','a','ITEMWISE')")
con.execute("INSERT INTO marg_hand_change (k20, item, kind, day_from, day_to, status) VALUES ('CAST SHOE L TYNOR','CAST SHOE L TYNOR','hand','2026-10-23','2026-10-25','open')")
con.commit()
con.close()

app = Flask(__name__)


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB, timeout=30)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def _close(_e):
    c = g.pop("db", None)
    if c is not None:
        c.close()


ROLES = {"darpan": ["maker"], "manoj": ["checker"]}
CUR = {"u": "darpan"}


def require(*roles, unit="medical"):
    have = ROLES.get(CUR["u"], []) if unit == "stockmatch" else []
    if not set(have) & set(roles):
        return None, (jsonify(ok=False, error="not_permitted"), 403)
    return dict(user=CUR["u"], role="staff", roles=have), None


import stockmatch  # noqa: E402

stockmatch.init(app, db, require, unit="medical")
cl = app.test_client()
RES = []


def check(name, ok):
    RES.append((name, bool(ok)))
    print(("GREEN " if ok else "RED   ") + name)


def as_(u):
    CUR["u"] = u


def J(r):
    try:
        return r.get_json() or {}
    except Exception:  # noqa: BLE001
        return {}


P = "/finance/stockmatch/count"
as_("darpan")
r = cl.get(P + "/api/healthz")
check("1 the count is mounted on Stock milaan (healthz 200)", r.status_code == 200 and J(r).get("kit") == "S768_SECTION_COUNT")
r = cl.get("/finance/stockmatch")
check("2 Stock milaan still opens and carries the link to the count", r.status_code == 200 and b"s768count" in r.data)
if CONTROL:
    old = r.status_code == 200
    s768 = [ok for n, ok in RES if not n.startswith("2")] + [b"s768count" in r.data]
    print("CONTROL S768 RED as it must be" if old and not any(s768) else "CONTROL S768 NOT RED (the live files already carry S768?)")
    sys.exit(0)

import section_count as SC  # noqa: E402

c0 = sqlite3.connect(DB)
c0.row_factory = sqlite3.Row
nd, nf = SC.seed_from(c0, os.path.join(FILES, "section_count_seed_S768.txt"))
c0.commit()
check("3 the seed: 75 display rows, 21 marks (2 of them two-star); again writes nothing",
      (nd, nf) == (75, 21) and SC.seed_from(c0, os.path.join(FILES, "section_count_seed_S768.txt")) == (0, 0)
      and c0.execute("SELECT COUNT(*) FROM section_count_flag WHERE level=2").fetchone()[0] == 2)
c0.commit()
c0.close()

as_("amir")
check("4 a login outside Stock milaan is refused (403)", cl.get(P + "/api/state").status_code == 403)

as_("darpan")
SCANS["open"] = [dict(month=TODAY.strftime("%Y-%m"), state="waiting", vendor="Yuvika Surgicals", bill_no="805", stamp="B-0400", day=ISO(TODAY))]
st = J(cl.get(P + "/api/state?section=Orthotics"))
check("5 the guard names the Yuvika scan not in Marg", st.get("guard", {}).get("blocked") and "805" in json.dumps(st["guard"]))
r = cl.post(P + "/api/start", json=dict(section="Orthotics", override=True))
check("6 staff cannot start past the guard, even asking to (409)", r.status_code == 409)
as_("manoj")
r = cl.post(P + "/api/start", json=dict(section="Orthotics"))
check("7 the doctor too is stopped unless he says 'start anyway' (409)", r.status_code == 409)
r = cl.post(P + "/api/start", json=dict(section="Orthotics", override=True))
cid = J(r).get("count")
check("8 the doctor starts anyway; it is recorded", r.status_code == 200 and cid)
c1 = sqlite3.connect(DB)
c1.row_factory = sqlite3.Row
row = c1.execute("SELECT * FROM section_count WHERE id=?", (cid,)).fetchone()
check("9 override_by = the doctor", row["override_by"] == "manoj")
lines = {r["item"]: dict(r) for r in c1.execute("SELECT * FROM section_count_line WHERE count_id=?", (cid,))}
check("10 the lines: the section's items in Marg's newest closing, the new name included, the medicine not",
      "KNEE CAP UNISON XXL LYCRA" in lines and "ACILOC 300" not in lines and len(lines) == 7)
check("11 the marks: #44's name two stars (the seed), the hand-changed cast shoe one star, an unmarked line none",
      lines["KNEE SUPPORT M HINGED"]["flag"] == 2 and lines["CAST SHOE L TYNOR"]["flag"] == 1 and lines["ARM SLING XL UNISON"]["flag"] == 0)
check("12 the seeded display is used (group, kind, size)", lines["KNEE SUPPORT M HINGED"]["grp"] == "Knee support, hinged" and lines["KNEE SUPPORT M HINGED"]["size"] == "M")
c1.close()
r = cl.post(P + "/api/start", json=dict(section="Orthotics", override=True))
check("13 one open count a section (409)", r.status_code == 409)

as_("darpan")
st = J(cl.get(P + "/api/state?section=Orthotics"))
C = st["count"]
byitem = {l["item"]: l for l in C["lines"]}
r = cl.post(P + "/api/save", json=dict(count=cid, rev=C["rev"] + 5, details={}, lines=[]))
check("14 a save on a stale rev is refused (409)", r.status_code == 409)
day = ISO(TODAY)
L = []
for l in C["lines"]:
    v = {"KNEE SUPPORT M HINGED": 3, "CAST SHOE M TYNOR": 1, "SOFT COLLAR BODY AID S": 0}.get(l["item"], l["marg"])
    L.append(dict(n=l["n"], counted=v, second=(v if l["flag"] else None)))
ORIG0 = L[0]["counted"]
L[0]["counted"] = None
det = dict(counted_by="Darpan", entered_by="Darpan", day=day, when="during", last_bill="")
r = cl.post(P + "/api/save", json=dict(count=cid, rev=C["rev"], details=det, lines=L, aside=[dict(words="TYNOR KNEE CAP M", dealer="Yuvika", qty=2)],
                                       extra=[dict(words="CREPE 10CM", qty=3)]))
rev = J(r).get("rev")
check("15 a save moves the rev on", r.status_code == 200 and rev == C["rev"] + 1)
r = cl.post(P + "/api/send", json=dict(count=cid, rev=rev))
check("16 send refused while a line is empty / no last bill during the day (400)", r.status_code == 400)
L[0]["counted"] = ORIG0
for x in L:
    if C["lines"][x["n"] - 1]["flag"]:
        x["second"] = x["counted"]
two = [x for x in L if C["lines"][x["n"] - 1]["flag"]][0]
two["second"] = (two["counted"] or 0) + 1
det["last_bill"] = "A000100"
rev = J(cl.post(P + "/api/save", json=dict(count=cid, rev=rev, details=det, lines=L, aside=[dict(words="TYNOR KNEE CAP M", dealer="Yuvika", qty=2)],
                                           extra=[dict(words="CREPE 10CM", qty=3)]))).get("rev")
r = cl.post(P + "/api/send", json=dict(count=cid, rev=rev))
check("17 send refused while a starred line's two counts differ (400)", r.status_code == 400 and "two counts" in J(r).get("message", ""))
two["second"] = two["counted"]
rev = J(cl.post(P + "/api/save", json=dict(count=cid, rev=rev, details=det, lines=L, aside=[dict(words="TYNOR KNEE CAP M", dealer="Yuvika", qty=2)],
                                           extra=[dict(words="CREPE 10CM", qty=3)]))).get("rev")
r = cl.post(P + "/api/send", json=dict(count=cid, rev=rev))
check("18 a whole count is sent", r.status_code == 200)
st = J(cl.get(P + "/api/state?count=%d" % cid))
check("19 staff see the count sent, never the correction", st["count"]["status"] == "sent" and "correction" not in st["count"])
r = cl.post(P + "/api/to_amir", json=dict(count=cid))
check("20 staff cannot send it to Amir (403)", r.status_code == 403)

as_("manoj")
st = J(cl.get(P + "/api/state?count=%d" % cid))
check("21 the doctor: the correction waits for the count day's closing", st["count"]["correction"]["state"] == "waiting")
c2 = sqlite3.connect(DB)
for it, q in [("KNEE SUPPORT M HINGED", 0), ("KNEE SUPPORT L HINGED", 2), ("CAST SHOE M TYNOR", 2), ("CAST SHOE L TYNOR", 1),
              ("SOFT COLLAR BODY AID S", 0), ("ARM SLING XL UNISON", 3), ("KNEE CAP UNISON XXL LYCRA", 1), ("ACILOC 300", 70)]:
    c2.execute("INSERT INTO stock_snapshot VALUES (?,?,?,?,?,?,?)", (DMY(TODAY), it, q, "1*1", 1, "x", "push_snapshot"))
c2.executemany("INSERT INTO sale_line_item (unit, business_date, bill_no, is_return, seq, item_name, item_key, qty_raw) VALUES (?,?,?,?,?,?,?,?)",
               [("medical", day, "A000099", 0, 1, "KNEE SUPPORT M HINGE", "KNEE SUPPORT M HINGE", "1.0"),
                ("medical", day, "A000101", 0, 1, "KNEE SUPPORT M HINGE", "KNEE SUPPORT M HINGE", "1.0"),
                ("medical", day, "A000102", 1, 1, "ARM SLING XL UNISON", "ARM SLING XL UNISON", "1.0")])
c2.execute("INSERT INTO purchase_line (supplier_norm, bill_no, bill_date, item, qty, free, direction, source_md5, line_type) VALUES "
           "('YUVIKA SURGICALS','806',?,'CAST SHOE M TYNOR',1,0,'PURCHASE','b','ITEMWISE')", (day,))
c2.commit()
c2.close()
st = J(cl.get(P + "/api/state?count=%d" % cid))
K = st["count"]["correction"]
kl = {x["item"]: x for x in K["lines"]}
check("22 ready: Marg at the count = closing + sold after the last bill (a sale before it ignored)",
      K["state"] == "ready" and kl["KNEE SUPPORT M HINGED"]["at_count"] == 1 and kl["KNEE SUPPORT M HINGED"]["change"] == 2)
check("23 a return after the count takes away (closing 3 - 1 returned = 2 at the count; counted 3 -> +1)",
      kl["ARM SLING XL UNISON"]["at_count"] == 2 and kl["ARM SLING XL UNISON"]["change"] == 1)
check("24 a purchase dated the count day puts its line 'by hand' (no change until the doctor gives one)",
      any("purchase dated the count day" in n for n in kl["CAST SHOE M TYNOR"]["notes"]) and kl["CAST SHOE M TYNOR"]["change"] is None and K["hand"] == 1)
check("25 the size-losing name gets its rename (SOFT COLLAR S BODY AID)", any(r["new"] == "SOFT COLLAR S BODY AID" for r in K["renames"]))
check("26 the kept-aside box and the not-listed line are shown, not counted",
      K["aside"] and K["aside"][0]["qty"] == 2 and K["extra"] and all(x["item"] != "TYNOR KNEE CAP M" for x in K["lines"]))
r = cl.post(P + "/api/to_amir", json=dict(count=cid))
check("26a a kept-aside line not yet settled blocks Amir (409)", r.status_code == 409 and "kept-aside" in J(r).get("message", ""))
knee_n = kl["KNEE CAP UNISON XXL LYCRA"]["n"]
r = cl.post(P + "/api/aside_clear", json=dict(count=cid, seq=1, same_day=True, n=knee_n))
st = J(cl.get(P + "/api/state?count=%d" % cid))
K = st["count"]["correction"]
kl = {x["item"]: x for x in K["lines"]}
check("26b settled 'bill entered on the count day': its 2 boxes are added to the named line (counted 1+2, Marg 1 -> +2)",
      r.status_code == 200 and kl["KNEE CAP UNISON XXL LYCRA"]["counted"] == 3 and kl["KNEE CAP UNISON XXL LYCRA"]["change"] == 2 and K["open_aside"] == 0)
r = cl.post(P + "/api/to_amir", json=dict(count=cid))
check("26c a 'by hand' line blocks Amir until the doctor gives its figure (409)", r.status_code == 409 and "#" in J(r).get("message", ""))
as_("darpan")
r1 = cl.post(P + "/api/hand", json=dict(count=cid, n=kl["CAST SHOE M TYNOR"]["n"], change=-1))
as_("manoj")
r = cl.post(P + "/api/hand", json=dict(count=cid, n=kl["CAST SHOE M TYNOR"]["n"], change="-1"))
st = J(cl.get(P + "/api/state?count=%d" % cid))
K = st["count"]["correction"]
kl = {x["item"]: x for x in K["lines"]}
check("26d staff cannot set a line by hand (403); the doctor's -1 stands", r1.status_code == 403 and r.status_code == 200
      and kl["CAST SHOE M TYNOR"]["change"] == -1 and K["hand"] == 0)
r = cl.post(P + "/api/to_amir", json=dict(count=cid))
j = J(r)
c3 = sqlite3.connect(DB)
jobs = c3.execute("SELECT key, kind, text_hi, show_from FROM amir_job ORDER BY id").fetchall()
nchg = sum(1 for x in K["lines"] if x["change"])
check("27 to Amir: one tap job per changed line and per rename, shown now", r.status_code == 200 and len(jobs) == nchg + 1
      and all(k == "tap" and sf for _key, k, _t, sf in jobs) and any("STOCK RECEIVE kijiye: 2 nag" in t for _k, _kk, t, _s in jobs)
      and any("naam badliye: SOFT COLLAR S BODY AID" in t for _k, _kk, t, _s in jobs))
r = cl.post(P + "/api/to_amir", json=dict(count=cid))
check("28 a second send to Amir is refused and writes nothing", r.status_code == 409 and c3.execute("SELECT COUNT(*) FROM amir_job").fetchone()[0] == len(jobs))
check("29 the 06-Sep count is untouched", c3.execute("SELECT COUNT(*) FROM stock_count").fetchone()[0] == 1)
check("30 every write audited (start, send, to_amir)", {r[0] for r in c3.execute("SELECT action FROM audit_log WHERE table_name='section_count'")} >= {"start", "send", "to_amir"})
c3.close()
r = cl.post(P + "/api/aside_clear", json=dict(count=cid, seq=1, same_day=False))
check("31 a kept-aside line is settled once, before Amir (the count has gone: 409)", r.status_code == 409)

SCANS["open"] = []
c4 = sqlite3.connect(DB)
for it, q in [("KNEE SUPPORT M HINGED", 5), ("KNEE SUPPORT L HINGED", 2), ("CAST SHOE M TYNOR", 1), ("CAST SHOE L TYNOR", 1),
              ("SOFT COLLAR BODY AID S", 0), ("ARM SLING XL UNISON", 3), ("KNEE CAP UNISON XXL LYCRA", 1)]:
    c4.execute("INSERT INTO stock_snapshot VALUES (?,?,?,?,?,?,?)", (DMY(TODAY + dt.timedelta(days=1)), it, q, "1*1", 1, "x", "push_snapshot"))
c4.execute("UPDATE section_count_flag SET level=0")
c4.execute("UPDATE marg_hand_change SET status='closed'")
c4.commit()
c4.close()
as_("darpan")
st = J(cl.get(P + "/api/state?section=Orthotics"))
check("32 no scan waiting: the guard is clear", st.get("guard", {}).get("checked") and not st["guard"].get("blocked"))
r = cl.post(P + "/api/start", json=dict(section="Orthotics"))
cid2 = J(r).get("count")
c5 = sqlite3.connect(DB)
c5.row_factory = sqlite3.Row
fl = {r["item"]: (r["flag"], r["flag_why"]) for r in c5.execute("SELECT item, flag, flag_why FROM section_count_line WHERE count_id=?", (cid2,))}
check("33 the second count marks from the record since the first: M hinged (3 counted - 1 sold after = 2, Marg 5) two stars; "
      "arm sling (3 + 1 returned = 4, Marg 3) one star; L hinged (2, Marg 2) none",
      r.status_code == 200 and fl["KNEE SUPPORT M HINGED"][0] == 2 and "record" in fl["KNEE SUPPORT M HINGED"][1]
      and fl["ARM SLING XL UNISON"][0] == 1 and fl["KNEE SUPPORT L HINGED"][0] == 0)
c5.close()
as_("manoj")
r = cl.post(P + "/api/cancel", json=dict(count=cid2))
check("34 the doctor cancels an open count", r.status_code == 200)
r = cl.post(P + "/api/flag", json=dict(section="Orthotics", item="CAST SHOE M TYNOR", level=2))
as_("darpan")
r2 = cl.post(P + "/api/flag", json=dict(section="Orthotics", item="CAST SHOE M TYNOR", level=0))
check("35 the doctor marks a line; staff cannot (403)", r.status_code == 200 and r2.status_code == 403)
r = cl.get(P)
check("36 the page is served", r.status_code == 200 and b"Section count" in r.data)
SR.register = lambda con, month: (_ for _ in ()).throw(RuntimeError("assets.db unreachable"))
as_("darpan")
st = J(cl.get(P + "/api/state?section=Orthotics"))
r = cl.post(P + "/api/start", json=dict(section="Orthotics", override=True))
check("38 scans that cannot be read block like a waiting bill: staff cannot start (409)", st["guard"]["blocked"] and not st["guard"]["checked"] and r.status_code == 409)
SR.register = lambda con, month: dict(scans=[])
r = cl.post(P + "/api/start", json=dict(section="Medicines"))
check("39 v1 counts Orthotics only (400 for Medicines)", r.status_code == 400)
c6 = sqlite3.connect(DB)
try:
    c6.execute("INSERT INTO section_count (section, status, started_at) VALUES ('Orthotics','draft','x')")
    c6.execute("INSERT INTO section_count (section, status, started_at) VALUES ('Orthotics','draft','y')")
    dup = True
except sqlite3.IntegrityError:
    dup = False
c6.rollback()
c6.close()
check("40 two drafts of one section cannot exist (unique index)", not dup)
c7 = sqlite3.connect(DB)
c7.row_factory = sqlite3.Row
s_ok = SC.sales_on(c7, day, "during", "B000001", set())
uns = set()
SC.sales_on(c7, day, "during", "B000001", uns)
c7.close()
check("41 a bill of another series is neither before nor after: its line goes by hand", not s_ok and "KNEE SUPPORT M HINGE" in uns)
check("37 rename_for refuses a clash and keeps the other four of the paper",
      SC.rename_for("CERVICAL COLLAR SOFT HOPE L", []) == "CERVICAL COLLAR L SOFT HOPE" and SC.rename_for("BLING CONT. LS BELT XXL", []) == "BLING CONT. XXL LS BELT"
      and SC.rename_for("SOFT COLLAR NEOLIFE L", []) == "SOFT COLLAR L NEOLIFE" and SC.rename_for("SOFT COLLAR NEOLIFE L", ["SOFT COLLAR L NEOLIFE X"]) is None
      and not SC.loses_size("L S BELT XL CONT GRAY UNIS") and SC.loses_size("L S BELT CONT GRAY UNISON XXL"))

bad = [n for n, ok in RES if not ok]
print("WALK S768 GREEN" if not bad else "WALK S768 RED (%d): %s" % (len(bad), "; ".join(bad)[:300]))
