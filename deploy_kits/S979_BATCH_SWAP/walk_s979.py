#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s979.py -- S979_BATCH_SWAP: the walk on MADE-UP data (never a live database).
    python3 walk_s979.py FINDIR
FINDIR holds the files to judge (expiry_watch.py, stockmatch.py, stockmatch.html, batch_swap.py and their neighbours). On the FROM files
(no batch_swap.py, the old three) the S979 checks go red at A1. Last line: WALK passed/total."""
import datetime as dt
import importlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

FIN = os.path.abspath(sys.argv[1])
_ME = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [FIN] + [p for p in sys.path if os.path.abspath(p or ".") not in (_ME, FIN)]   # the files judged, never the kit's own copies
TMP = tempfile.mkdtemp(prefix="walk_s979_")
STUB = os.path.join(TMP, "push.jsonl")
os.environ["ORDER_PUSH_STUB"] = STUB
os.environ["FINANCE_DB"] = os.path.join(TMP, "never_opened.db")
P, F = [], []


def check(name, cond, detail=""):
    (P if cond else F).append(name)
    print(("PASS  " if cond else "FAIL  ") + name + (("  -- " + str(detail)[:240]) if (detail and not cond) else ""))


def pushes():
    if not os.path.exists(STUB):
        return []
    return [json.loads(x) for x in open(STUB, encoding="utf-8") if x.strip()]


def mkdb(path):
    con = sqlite3.connect(path)
    con.executescript("""
    CREATE TABLE setting (key TEXT PRIMARY KEY, value TEXT, note TEXT);
    CREATE TABLE audit_log (id INTEGER PRIMARY KEY, table_name TEXT, row_id INTEGER, action TEXT, before_json TEXT, after_json TEXT, by_whom TEXT, at TEXT);
    CREATE TABLE mi_sale_line (md5 TEXT, bill_date TEXT, bill_no TEXT, is_return INTEGER, seq INTEGER, item_name TEXT, pack TEXT, qty_raw TEXT,
        qty_strips INTEGER, qty_loose INTEGER, amount_p INTEGER, expiry_ym TEXT, batch TEXT);
    INSERT INTO setting VALUES ('expiry.near_days','90','');
    """)
    con.execute("""CREATE TABLE stock_batch_now (
        id INTEGER PRIMARY KEY, run_id INTEGER NOT NULL, at TEXT, as_on TEXT, sales_after TEXT, sales_to TEXT, k20 TEXT NOT NULL, item TEXT,
        batch TEXT, expiry TEXT, units INTEGER, printed INTEGER, sold INTEGER, bought INTEGER, new INTEGER, pack INTEGER, packing TEXT)""")
    con.commit()
    return con


BATCHES = [  # item, batch, expiry, units, sold, pack
    ("ALPHA TAB", "A1X", "2026-12", 8, 0, 10), ("ALPHA TAB", "A2X", "2027-08", 80, 4, 10), ("ALPHA TAB", "A3X", "2027-09", 90, 0, 10),
    ("BETA SYP", "B-77", "2026-12", 1, 0, 1), ("BETA SYP", "B88", "2029-03", 2, 0, 1),
    ("GAMMA TAB", "G1", "2026-12", 5, 2, 10), ("GAMMA TAB", "G2", "2027-06", 30, 1, 10),
    ("DELTA TAB", "D1", "2027-01", 12, 0, 10),
    ("EPS TAB", "C1255", "2027-01", 1, 0, 10), ("EPS TAB", "C-1255", "2027-01", 8, 44, 10),
    ("ZETA TAB", "Z0", "2026-12", 5, 0, 10), ("ZETA TAB", "Z1", "2027-01", 10, 0, 10),
    ("ETA TAB", "H1", "2028-06", 9, 0, 10), ("ETA TAB", "H2", "2029-06", 9, 3, 10),
    ("THETA GEL", "T1", "2026-12", 0, 0, 1), ("THETA GEL", "T2", "2028-01", 4, 1, 1),
]


def fill(con, rows=BATCHES, run_id=7):
    con.execute("DELETE FROM stock_batch_now")
    for it, b, e, u, s, p in rows:
        con.execute("INSERT INTO stock_batch_now (run_id, at, as_on, sales_after, sales_to, k20, item, batch, expiry, units, printed, sold, bought, "
                    "new, pack, packing) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,0,0,?,?)",
                    (run_id, "2026-11-27T23:57:00", "2026-11-23", "2026-11-22", "2026-11-26", it[:20], it, b, e, u, u + s, s, p, "1*%d" % p))
    con.commit()


def sale(con, day, bill, ret, item, qty_raw, strips, loose, amt, batch, pack="1*10"):
    con.execute("INSERT INTO mi_sale_line VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("m" + day, day, bill, ret, 1, item, pack, qty_raw, strips, loose, amt, "", batch))
    con.commit()


T = lambda y, mo, d, h=9, mi=0: dt.datetime(y, mo, d, h, mi)   # noqa: E731
D28 = dt.date(2026, 11, 28)

# ---------------------------------------------------------------- A: the module, the finder
try:
    B = importlib.import_module("batch_swap")
    check("A1 batch_swap.py present, kit S979", getattr(B, "KIT", "") == "S979_BATCH_SWAP")
except Exception as ex:                                       # noqa: BLE001
    B = None
    check("A1 batch_swap.py present, kit S979", False, "%s: %s" % (type(ex).__name__, ex))
check("A0 importing it opens no database (F-1722)", not os.path.exists(os.environ["FINANCE_DB"]))
if B is None:
    print("WALK %d/%d" % (len(P), len(P) + len(F) + 60))
    sys.exit(1)

dbp = os.path.join(TMP, "f.db")
con = mkdb(dbp)
fill(con)
with con:
    st = B.find(con, D28, T(2026, 11, 27, 23, 57))
cs = {(c["k20"], c["old_key"]): c for c in B._rows(con)}
check("A2 three cases: ALPHA A1X, BETA B77, ZETA Z0", st["new"] == 3 and set(cs) == {("ALPHA TAB", "A1X"), ("BETA SYP", "B77"), ("ZETA TAB", "Z0")}, sorted(cs))
check("A3 sold since the export / one batch / same batch two ways / far / no stock are never cases",
      not any(k[0] in ("GAMMA TAB", "DELTA TAB", "EPS TAB", "ETA TAB", "THETA GEL") for k in cs))
check("A4 the partner is the selling newer batch (ALPHA -> A2X); a later batch only (ZETA -> Z1)",
      cs[("ALPHA TAB", "A1X")]["new_batch"] == "A2X" and cs[("ZETA TAB", "Z0")]["new_batch"] == "Z1")
check("A5 the case carries the last selling day and the paper quantity",
      cs[("ALPHA TAB", "A1X")]["last_sell"] == "2026-11-30" and cs[("ALPHA TAB", "A1X")]["paper_units"] == 8 and cs[("ALPHA TAB", "A1X")]["swap_units"] == 8)
with con:
    st2 = B.find(con, D28, T(2026, 11, 28, 10))
check("A6 the same list again: nothing new", st2["new"] == 0 and len(B._rows(con)) == 3, st2)
rows2 = [list(r) for r in BATCHES]
rows2[0][3] = 7
fill(con, [tuple(r) for r in rows2])
with con:
    st3 = B.find(con, D28, T(2026, 11, 28, 10, 5))
a = [c for c in B._rows(con) if c["k20"] == "ALPHA TAB"][0]
check("A7 an untouched case follows the newest paper figure", st3["refreshed"] == 1 and a["paper_units"] == 7 and a["swap_units"] == 7, st3)
fill(con)
with con:
    B.find(con, D28, T(2026, 11, 28, 10, 6))
n_audit = con.execute("SELECT COUNT(*) FROM audit_log WHERE table_name='expiry_swap_case'").fetchone()[0]
check("A8 every write audited (table expiry_swap_case)", n_audit >= 4, n_audit)
check("A9 the settings seeded", con.execute("SELECT value FROM setting WHERE key='swap.answer_by'").fetchone()[0] == "13:00")

ID = {c["k20"]: c["id"] for c in B._rows(con)}

dbw = os.path.join(TMP, "w.db")
cw = mkdb(dbw)
cw.execute("INSERT INTO setting VALUES ('stock.whole_unit_items', '[\"OMEGA = bottle\"]', '')")
cw.commit()
fill(cw, [("OMEGA", "W1", "2026-12", 2, 0, 40), ("OMEGA", "W2", "2027-10", 5, 1, 40),
          ("PI TAB", "1255", "2026-12", 3, 0, 10), ("PI TAB", "C1255", "2027-06", 30, 2, 10)])
with cw:
    B.find(cw, D28, T(2026, 11, 28, 1))
ow = [c for c in B._rows(cw) if c["k20"] == "OMEGA"]
check("A10 a whole-unit item (OMEGA = bottle, packing 1*40): found at pack 1, its 2 bottles as Marg prints them",
      len(ow) == 1 and ow[0]["pack"] == 1 and ow[0]["paper_units"] == 2, ow)
if ow:
    vw = B.darpan_view(cw, T(2026, 11, 29, 9))
    okw, msgw, _cw = B.answer(cw, ow[0]["id"], "hai", {"pcs": "1"}, "darpan")
    ow2 = B._rows(cw, "id=?", (ow[0]["id"],))[0]
    check("A11 his card says '2 nag'; 'Hai 1' leaves 1 bottle to swap (never 40)", [x["paper_hi"] for x in vw["ask"]] == ["2 nag"]
          and ow2["answer_n"] == 1 and ow2["swap_units"] == 1 and ow2["state"] == "open", (vw["ask"], ow2))
check("A12 a batch whose letters end another's (1255 / C1255) is one batch printed two ways: never a case",
      not [c for c in B._rows(cw) if c["k20"] == "PI TAB"])
cw.close()

# ---------------------------------------------------------------- B: Darpan's answers
v = B.darpan_view(con, T(2026, 11, 29, 8, 0))
check("B1 the shelf questions: 3, no bills before he is asked", len(v["ask"]) == 3 and v["bills"] is None, v)
alpha = [x for x in v["ask"] if x["item"] == "ALPHA TAB"][0]
check("B2 his words: 'Marg mein 8 goli', last selling day 30-11, a pack-1 item in nag",
      alpha["paper_hi"] == "8 goli" and alpha["last_sell"] == "30-11" and [x for x in v["ask"] if x["item"] == "BETA SYP"][0]["paper_hi"] == "1 nag")
ok, msg, code = B.answer(con, ID["ALPHA TAB"], "nahi", {}, "darpan")
v = B.darpan_view(con, T(2026, 11, 29, 9, 0))
check("B3 Nahi hai -> on the two bills, the whole paper quantity", ok and v["bills"] and [x["item"] for x in v["bills"]["sale"]] == ["ALPHA TAB"]
      and v["bills"]["sale"][0]["swap_hi"] == "8 goli" and v["bills"]["ret"][0]["new_batch"] == "A2X", (ok, msg, v.get("bills")))
ok, msg, code = B.answer(con, ID["ZETA TAB"], "hai", {"strips": "0", "loose": "2"}, "darpan")
z = B._rows(con, "id=?", (ID["ZETA TAB"],))[0]
check("B4 Hai 2 of 5 -> only the missing 3 swapped, the case open", ok and z["answer_n"] == 2 and z["swap_units"] == 3 and z["state"] == "open", (msg, z))
na = con.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
ok2, msg2, _c = B.answer(con, ID["ZETA TAB"], "hai", {"strips": "0", "loose": "2"}, "darpan")
check("B5 a repeat tap writes nothing", ok2 and con.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0] == na and "pehle" in msg2)
ok, msg, code = B.answer(con, ID["BETA SYP"], "hai", {"pcs": "3"}, "darpan")
b_ = B._rows(con, "id=?", (ID["BETA SYP"],))[0]
check("B6 Hai with all of it -> 'shelf': never swapped, marked on Near expiry", ok and b_["state"] == "shelf" and b_["swap_units"] == 0
      and B.near_marks(con).get(("BETA SYP", "B77")) == 3, (msg, b_))
okx, msgx, codex = B.answer(con, ID["BETA SYP"], "nahi", {}, "darpan")
check("B7 a finished case refuses a new answer (409)", not okx and codex == 409)
okh, msgh, codeh = B.answer(con, ID["ALPHA TAB"], "hai", {}, "darpan")
check("B8 Hai with nothing typed is refused (400)", not okh and codeh == 400)

# ---------------------------------------------------------------- C: the 13:00 rule
fill(con, BATCHES + [("IOTA TAB", "I1", "2027-01", 6, 0, 10), ("IOTA TAB", "I2", "2027-12", 40, 2, 10)])
with con:
    B.find(con, D28, T(2026, 11, 28, 11))
iota = [c for c in B._rows(con) if c["k20"] == "IOTA TAB"][0]
con.execute("UPDATE expiry_swap_case SET asked_at=? WHERE id=?", ("2026-11-29T08:30:00", iota["id"]))
con.commit()
iota = B._rows(con, "id=?", (iota["id"],))[0]
check("C1 not answered: not on the bills at 12:59, on them from 13:00",
      not B.to_bill(con, iota, T(2026, 11, 29, 12, 59)) and B.to_bill(con, iota, T(2026, 11, 29, 13, 0)))
con.execute("UPDATE expiry_swap_case SET asked_at=? WHERE id=?", ("2026-11-29T14:00:00", iota["id"]))
con.commit()
iota = B._rows(con, "id=?", (iota["id"],))[0]
check("C2 first asked after 13:00: the next day's 13:00", not B.to_bill(con, iota, T(2026, 11, 29, 18)) and B.to_bill(con, iota, T(2026, 11, 30, 13, 1)))
check("C3 never asked: never billed without his answer", not B.to_bill(con, dict(iota, asked_at=None), T(2026, 12, 5)))

# ---------------------------------------------------------------- D: Dono bill bana diye
ok, msg, code = B.bills_made(con, [ID["ALPHA TAB"], 999], "darpan", T(2026, 11, 29, 11, 15))
a = B._rows(con, "id=?", (ID["ALPHA TAB"],))[0]
check("D1 his tap recorded on the card's cases only; it closes nothing", ok and a["bills_at"] and a["state"] == "open" and not a["closed_at"])
okd, msgd, coded = B.bills_made(con, [ID["ALPHA TAB"]], "darpan", T(2026, 11, 29, 11, 20))
check("D2 a second tap on the same card is refused (the card moved on)", not okd and coded == 409)
v = B.darpan_view(con, T(2026, 11, 29, 11, 30))
check("D3 his card says 'bana diye', the two bills gone", [x["item"] for x in v["made"]] == ["ALPHA TAB"] and not (v["bills"] and ID["ALPHA TAB"] in v["bills"]["ids"]))
okn, msgn, coden = B.answer(con, ID["ALPHA TAB"], "hai", {"loose": "1"}, "darpan")
check("D4 after the bills no shelf answer is taken", not okn and coden == 409)

# ---------------------------------------------------------------- E: the judge on the sale report
sale(con, "2026-11-26", "A004990", 0, "ALPHA TAB", "0:8", 0, 8, 4000, "A1X")          # before the case was found
sale(con, "2026-11-28", "A005101", 0, "ALPHA TAB", "0:7", 0, 7, 3500, "A1X")          # another quantity, before his tap day
with con:
    j = B.judge(con, {}, T(2026, 11, 30, 10))
a = B._rows(con, "id=?", (ID["ALPHA TAB"],))[0]
check("E1 a line before the case and a line of another quantity are not the swap", j["closed"] == 0 and not a["sale_date"], a)
sale(con, "2026-11-29", "A005102", 0, "ALPHA TAB", "0:8", 0, 8, 4000, "A-1X")         # the STOCK sale, batch printed with a dash
with con:
    j = B.judge(con, {}, T(2026, 11, 30, 10, 5))
a = B._rows(con, "id=?", (ID["ALPHA TAB"],))[0]
check("E2 the sale on the old batch (printed 'A-1X') seen; one half -> 'half', red", a["sale_bill"] == "A005102" and a["state"] == "open"
      and B.half_of(a) == "ret" and B.red_of(con, a, dt.date(2026, 11, 30), "2026-11-29") == "half", a)
v = B.darpan_view(con, T(2026, 11, 30, 10, 6))
check("E3 Darpan's card: 'STOCK bill adhoora' -- the return on A2X", [(x["item"], x["missing"], x["new_batch"]) for x in v["half"]] == [("ALPHA TAB", "ret", "A2X")], v["half"])
sale(con, "2026-11-30", "CN00401", 1, "ALPHA TAB", "0:8", 0, 8, 4000, "A2X")
with con:
    j = B.judge(con, {}, T(2026, 12, 1, 10))
a = B._rows(con, "id=?", (ID["ALPHA TAB"],))[0]
check("E4 the return on the newer batch closes it", j["closed"] == 1 and a["state"] == "closed" and a["ret_bill"] == "CN00401" and a["sale_p"] == 4000 and a["closed_at"], a)
# the alias: a sale line under Marg's other name is the item's
fill(con, BATCHES + [("KAPPA OINT", "K1", "2026-12", 2, 0, 1), ("KAPPA OINT", "K2", "2028-01", 6, 1, 1)])
with con:
    B.find(con, D28, T(2026, 11, 28, 12))
kc = [c for c in B._rows(con) if c["k20"] == "KAPPA OINT"][0]
B.answer(con, kc["id"], "nahi", {}, "darpan")
sale(con, "2026-11-28", "A005200", 0, "KAPPA OINTMENT 15G", "2.0", None, None, 9000, "K1", "1")
sale(con, "2026-11-28", "CN00410", 1, "KAPPA OINTMENT 15G", "2.0", None, None, 9000, "K2", "1")
with con:
    j = B.judge(con, {"KAPPA OINTMENT 15G": "KAPPA OINT"}, T(2026, 11, 29, 10))
kc = B._rows(con, "id=?", (kc["id"],))[0]
check("E5 Marg's other name through the spine's alias; a '2.0' piece line; both on one day closes", kc["state"] == "closed", kc)
sale(con, "2026-11-29", "CN00420", 1, "ZETA TAB", "0:3", 0, 3, 1500, "Z1")              # a customer's return of the same quantity
with con:
    B.judge(con, {}, T(2026, 11, 30, 10))
z = B._rows(con, "id=?", (ID["ZETA TAB"],))[0]
check("E6 a customer's return alone (no 'bana diye') is never half a swap", not z["ret_date"] and not z["sale_date"] and B.half_of(z) is None, z)
sale(con, "2026-11-30", "A005150", 0, "ZETA TAB", "0:3", 0, 3, 1500, "Z0")
sale(con, "2026-11-30", "CN00430", 1, "ZETA TAB", "0:3", 0, 3, 1500, "Z1")
with con:
    B.judge(con, {}, T(2026, 12, 1, 10))
z = B._rows(con, "id=?", (ID["ZETA TAB"],))[0]
check("E7 the same-day pair closes it without his tap (the sale on Z0, the return on Z1, the 30th's)", z["state"] == "closed" and z["ret_bill"] == "CN00430", z)
dbe = os.path.join(TMP, "e9.db")
ce = mkdb(dbe)
fill(ce, [("NU TAB", "N1", "2027-01", 4, 0, 10), ("NU TAB", "N2", "2027-08", 40, 2, 10), ("XI TAB", "X1", "2027-01", 5, 0, 10),
          ("XI TAB", "X2", "2027-08", 50, 2, 10), ("OMI TAB", "O1", "2027-01", 3, 0, 10), ("OMI TAB", "O2", "2027-08", 30, 2, 10),
          ("RHO TAB", "R1", "2026-12", 6, 0, 10), ("RHO TAB", "R2", "2027-01", 90, 0, 10), ("RHO TAB", "R3", "2028-01", 20, 3, 10)])
with ce:
    B.find(ce, D28, T(2026, 11, 28, 1))
E9 = {c["k20"]: c["id"] for c in B._rows(ce)}
r3 = B._rows(ce, "id=?", (E9.get("RHO TAB", 0),))
check("A13 a partner itself near expiry and unsold (R2) is the last choice: RHO swaps into R3", r3 and r3[0]["new_batch"] == "R3", r3)
for k in ("NU TAB", "XI TAB", "OMI TAB"):
    B.answer(ce, E9[k], "nahi", {}, "darpan")
sale(ce, "2026-11-29", "CN00501", 1, "NU TAB", "0:4", 0, 4, 800, "N2")                 # the return one day ...
sale(ce, "2026-11-30", "A005501", 0, "NU TAB", "0:4", 0, 4, 800, "N1")                 # ... the sale the next
B.bills_made(ce, [E9["NU TAB"], E9["XI TAB"]], "darpan", T(2026, 11, 30, 12))
sale(ce, "2026-11-29", "A005502", 0, "XI TAB", "0:5", 0, 5, 900, "X1")                 # XI: the sale on the 29th, his tap on the 30th
with ce:
    j9 = B.judge(ce, {}, T(2026, 12, 1, 10))
st9 = {c["k20"]: c for c in B._rows(ce)}
check("E9 split days with his tap: the return on the 29th and the sale on the 30th close it (no second return asked)",
      st9["NU TAB"]["state"] == "closed", st9["NU TAB"])
check("E10 one bill on the 29th, his tap on the 30th, the 30th's report without the other: half (the return), the tap kept",
      st9["XI TAB"]["sale_date"] == "2026-11-29" and B.half_of(st9["XI TAB"]) == "ret" and st9["XI TAB"]["bills_at"], st9["XI TAB"])
sale(ce, "2026-11-29", "A005503", 0, "OMI TAB", "0:3", 0, 3, 600, "O1")                 # OMI: the STOCK sale, no tap, no return
fill(ce, [("NU TAB", "N2", "2027-08", 44, 2, 10), ("XI TAB", "X2", "2027-08", 50, 2, 10), ("OMI TAB", "O1", "2027-01", 0, 3, 10),
          ("OMI TAB", "O2", "2027-08", 30, 2, 10), ("RHO TAB", "R1", "2026-12", 6, 0, 10), ("RHO TAB", "R2", "2027-01", 90, 0, 10),
          ("RHO TAB", "R3", "2028-01", 20, 3, 10)])
with ce:
    B.after_run(ce, 9, dt.date(2026, 12, 1), None, {}, log=lambda *_: None)
om = B._rows(ce, "id=?", (E9["OMI TAB"],))[0]
check("E11 no tap, his STOCK sale alone (the old batch now sold): half (red), never 'gone'",
      om["state"] == "open" and om["sale_date"] == "2026-11-29" and B.red_of(ce, om, dt.date(2026, 12, 1), "2026-11-30") == "half", om)
ce2 = sqlite3.connect(dbe)
fill(ce2, [("PSI TAB", "P1", "2027-01", 7, 0, 10), ("PSI TAB", "P2", "2027-08", 40, 2, 10), ("TAU TAB", "U1", "2027-01", 2, 0, 10),
           ("TAU TAB", "U2", "2027-08", 40, 2, 10)])
with ce2:
    B.find(ce2, D28, T(2026, 11, 28, 2))
psi = [c for c in B._rows(ce2) if c["k20"] == "PSI TAB"][0]
tau = [c for c in B._rows(ce2) if c["k20"] == "TAU TAB"][0]
B.answer(ce2, psi["id"], "nahi", {}, "darpan")
sale(ce2, "2026-11-29", "CN00601", 1, "PSI TAB", "0:7", 0, 7, 700, "P2")                # his return first, no tap ...
with ce2:
    B.judge(ce2, {}, T(2026, 11, 30, 10))
sale(ce2, "2026-11-30", "A005601", 0, "PSI TAB", "0:7", 0, 7, 700, "P1")                # ... the sale the next day
with ce2:
    B.judge(ce2, {}, T(2026, 12, 1, 10))
psi = B._rows(ce2, "id=?", (psi["id"],))[0]
check("E12 return first, sale the next day, no tap: closed (never a second return asked)", psi["state"] == "closed", psi)
sale(ce2, "2026-11-29", "A005602", 0, "TAU TAB", "0:2", 0, 2, 200, "U1")                # a customer's sale billed on the old batch
with ce2:
    B.judge(ce2, {}, T(2026, 11, 30, 10))
tau = B._rows(ce2, "id=?", (tau["id"],))[0]
check("E13 no shelf answer, no tap: a sale on the old batch is not taken as his STOCK bill", not tau["sale_date"], tau)
ce2.close()
fill(con, BATCHES + [("MU TAB", "M1", "2027-01", 6, 0, 10), ("MU TAB", "M2", "2027-09", 40, 1, 10)])
with con:
    B.find(con, D28, T(2026, 11, 28, 13))
mc = [c for c in B._rows(con) if c["k20"] == "MU TAB"][0]
B.answer(con, mc["id"], "nahi", {}, "darpan")
B.bills_made(con, [mc["id"]], "darpan", T(2026, 11, 30, 11))
sale(con, "2026-12-01", "A005700", 0, "OTHER TAB", "0:1", 0, 1, 100, "X1")             # the next day's report: the 30th's was whole
with con:
    jj = B.judge(con, {}, T(2026, 12, 1, 10))
mc = B._rows(con, "id=?", (mc["id"],))[0]
check("E8 'bana diye' on the 30th, the reports after it hold neither bill: back on his card, the tap cleared",
      jj.get("unseen") == 1 and not mc["bills_at"] and B.to_bill(con, mc, T(2026, 12, 1, 10)), (jj, mc.get("note")))

# ---------------------------------------------------------------- F/G: missed, late
fill(con, BATCHES + [("LAMBDA TAB", "L1", "2026-12", 4, 0, 10), ("LAMBDA TAB", "L2", "2027-09", 50, 3, 10)])
with con:
    B.find(con, D28, T(2026, 11, 28, 12, 30))
lc = [c for c in B._rows(con) if c["k20"] == "LAMBDA TAB"][0]
check("G1 last selling day 30-11, today 28-11, no sale: 'late' (red)", B.red_of(con, lc, D28, None) == "late")
check("G2 'Dono bill bana diye' takes it off 'late'", B.red_of(con, dict(lc, bills_at="2026-11-29T11:00:00"), D28, None) is None)
check("G3 a case 3 days out is not late", B.red_of(con, lc, dt.date(2026, 11, 27), None) is None)
con.execute("DELETE FROM mi_sale_line WHERE bill_date >= '2026-11-30'")
con.commit()
with con:
    m1 = B.missed(con, dt.date(2026, 12, 1))
lc = B._rows(con, "id=?", (lc["id"],))[0]
check("F1 1-Dec before the 30-Nov sale report is in: still open", m1 == 0 and lc["state"] == "open", lc["state"])
sale(con, "2026-11-30", "A005300", 0, "OTHER TAB", "0:1", 0, 1, 100, "X1")
with con:
    m2 = B.missed(con, dt.date(2026, 12, 1))
lc = B._rows(con, "id=?", (lc["id"],))[0]
check("F2 the 30-Nov report in, no sale: 'missed' (red)", m2 >= 1 and lc["state"] == "missed" and B.red_of(con, lc, dt.date(2026, 12, 1), None) == "missed")
dbf = os.path.join(TMP, "f3.db")
cf = mkdb(dbf)
fill(cf, BATCHES)
with cf:
    B.find(cf, D28, T(2026, 11, 28, 1))
af = [c for c in B._rows(cf) if c["k20"] == "ALPHA TAB"][0]
B.answer(cf, af["id"], "nahi", {}, "darpan")
sale(cf, "2026-11-30", "A005400", 0, "OTHER TAB", "0:1", 0, 1, 100, "X1")
with cf:
    B.after_run(cf, 99, dt.date(2026, 12, 1), None, {}, log=lambda *_: None)
st_ = {c["k20"]: c["state"] for c in B._rows(cf)}
check("F3 the watch's run on the 1st: an unswapped case is 'missed' (red), never 'gone'", st_.get("ALPHA TAB") == "missed" and st_.get("ZETA TAB") == "missed", st_)
cf.close()

# ---------------------------------------------------------------- H: the tick and its pushes
dbt = os.path.join(TMP, "t.db")
ct = mkdb(dbt)
fill(ct, BATCHES)
with ct:
    B.find(ct, D28, T(2026, 11, 28, 23, 57))
ct.close()
open(STUB, "w").close()
B.tick(dbt, os.path.join(TMP, "nospine.db"), T(2026, 11, 29, 7, 50), log=lambda *_: None)
check("H1 07:50: no push (outside the hours)", pushes() == [])
B.tick(dbt, os.path.join(TMP, "nospine.db"), T(2026, 11, 29, 8, 10), log=lambda *_: None)
ps = pushes()
check("H2 08:10: ONE red push to the owner naming the late ones; nothing to Darpan before 08:30",
      len(ps) == 1 and ps[0]["user"] == "manoj" and "ALPHA TAB" in ps[0]["payload"]["body"] and ps[0]["payload"]["url"] == "/finance/sanjeevni/expiry", ps)
B.tick(dbt, os.path.join(TMP, "nospine.db"), T(2026, 11, 29, 8, 40), log=lambda *_: None)
ps = pushes()
check("H3 08:40: ONE push to Darpan (3 shelf checks), the owner not again",
      len(ps) == 2 and ps[1]["user"] == "darpan" and "3 purane batch" in ps[1]["payload"]["body"] and ps[1]["payload"]["url"] == "/finance/stockmatch", ps[1:])
B.tick(dbt, os.path.join(TMP, "nospine.db"), T(2026, 11, 29, 9, 0), log=lambda *_: None)
check("H4 09:00: nothing again the same day", len(pushes()) == 2)
ct = sqlite3.connect(dbt)
asked = ct.execute("SELECT COUNT(*) FROM expiry_swap_case WHERE asked_at LIKE '2026-11-29T08:40%'").fetchone()[0]
check("H5 the push marks the day he was asked (the 13:00 rule reads it)", asked == 3, asked)
B.tick(dbt, os.path.join(TMP, "nospine.db"), T(2026, 11, 29, 22, 0), log=lambda *_: None)
check("H6 22:00: no push", len(pushes()) == 2)
B.tick(dbt, os.path.join(TMP, "nospine.db"), T(2026, 11, 30, 8, 35), log=lambda *_: None)
ps = pushes()
check("H7 the next morning: Darpan again for what still waits; the owner not again for the same reason",
      len(ps) == 3 and ps[2]["user"] == "darpan", [p["user"] for p in ps])
open(os.path.join(TMP, "S979_OFF_probe"), "w").close()
ct.execute("UPDATE setting SET value='0' WHERE key='swap.on'")
ct.commit()
B.tick(dbt, os.path.join(TMP, "nospine.db"), T(2026, 11, 30, 9, 35), log=lambda *_: None)
check("H8 swap.on = 0: the tick does nothing", len(pushes()) == 3)
ct.close()

# ---------------------------------------------------------------- I: gone / reopened
dbg = os.path.join(TMP, "g.db")
cg = mkdb(dbg)
fill(cg, BATCHES)
with cg:
    B.find(cg, D28, T(2026, 11, 28, 1))
zid = [c for c in B._rows(cg) if c["k20"] == "ZETA TAB"][0]["id"]
aid = [c for c in B._rows(cg) if c["k20"] == "ALPHA TAB"][0]["id"]
B.answer(cg, aid, "nahi", {}, "darpan")
cg.execute("UPDATE expiry_swap_case SET bills_at='2026-11-28T10:00:00' WHERE id=?", (aid,))
cg.commit()
fill(cg, [r for r in BATCHES if r[0] not in ("ZETA TAB", "ALPHA TAB")])
with cg:
    sg = B.find(cg, D28, T(2026, 11, 28, 2))
check("I1 an untouched case no longer on paper -> 'gone'; a case with bills made stays open",
      B._rows(cg, "id=?", (zid,))[0]["state"] == "gone" and B._rows(cg, "id=?", (aid,))[0]["state"] == "open" and sg["gone"] == 1, sg)
fill(cg, BATCHES)
with cg:
    sr = B.find(cg, D28, T(2026, 11, 28, 3))
check("I2 on paper again -> reopened, asked afresh", sr["reopened"] == 1 and B._rows(cg, "id=?", (zid,))[0]["state"] == "open")
cg.close()

# ---------------------------------------------------------------- J: the owner's page parts
h = B.owner_section(con, dt.date(2026, 12, 1), T(2026, 12, 1, 18))
check("J1 the section is collapsed, counts in its one line, the table's columns", h.startswith('<details class="s979">') and " open " in h and "closed this month" in h
      and "Darpan &middot; shelf" not in h and "Darpan · shelf" in h and "Swap into" in h and "<details open" not in h)
check("J2 a closed case shows 'closed', a shelf case 'on the shelf', a missed one red", "closed 01-12" in h and "on the shelf" in h and "missed" in h)
ny = B.needs_you(con, dt.date(2026, 12, 1))
check("J3 a Needs-you line names the red", len(ny) == 1 and ny[0]["href"] == "/finance/sanjeevni/expiry" and "LAMBDA TAB" in ny[0]["text"], ny)

# ---------------------------------------------------------------- K: expiry_watch's hooks
EW = importlib.import_module("expiry_watch")
check("K0 expiry_watch carries the S979 hooks", getattr(EW, "KIT_S979", "") == "S979_BATCH_SWAP" and hasattr(EW, "_s979_section"))
dbk = os.path.join(TMP, "k.db")
ck = mkdb(dbk)
ck.close()
sp = os.path.join(TMP, "spine.db")
s_ = sqlite3.connect(sp)
s_.executescript("CREATE TABLE sp_alias (alias TEXT, k20 TEXT); CREATE TABLE sp_close (k20 TEXT, as_on TEXT, units INTEGER);"
                 "CREATE TABLE sp_move (k20 TEXT, date TEXT, kind TEXT, units INTEGER); CREATE TABLE sp_sale_line (date TEXT, k20 TEXT, batch TEXT, expiry TEXT, units INTEGER, bill TEXT);"
                 "CREATE TABLE sp_sale_bill (date TEXT, bill TEXT, credit_note INTEGER);")
s_.close()
bt = {}
for it, b, e, u, s2, p in BATCHES:
    bt[(it[:20], b)] = dict(item=it, k20=it[:20], batch=b, expiry=e, units=u, printed=u + s2, sold=s2, bought=0, pack=p, packing="1*%d" % p)
_orig_compute = EW.compute
EW.compute = lambda con, sp_, alias, archive, today: (dict(at="2026-11-28T23:57:00", today=today.isoformat(), ok=1, kit=EW.KIT, note="walk",
                                                            export_as_on="2026-11-23", _bt=bt, _sales_after="2026-11-22", sales_to="2026-11-27",
                                                            counts="{}"), [dict(section="near", seq=1, part="2026-12", k20="BETA SYP", item="BETA SYP",
                                                                                 batch="B-77", expiry="2026-12", units=1, pack=1, packing="1*1",
                                                                                 last_sale=None, last_buy=None, info="{}")])
logs = []
try:
    EW.run(dbk, sp, os.path.join(TMP, "arch"), D28, log=logs.append)
except Exception as ex:                                       # noqa: BLE001
    logs.append("RAISED %s" % ex)
EW.compute = _orig_compute
ck = sqlite3.connect(dbk)
has = ck.execute("SELECT name FROM sqlite_master WHERE name='expiry_swap_case'").fetchone()
n_k = ck.execute("SELECT COUNT(*) FROM expiry_swap_case").fetchone()[0] if has else 0
check("K1 the watch's run finds the cases on its own batches (never a push)", n_k == 3 and not pushes()[3:], (n_k, [l for l in logs if "swap" in l][:2]))
bid = ck.execute("SELECT id FROM expiry_swap_case WHERE k20='BETA SYP'").fetchone() if has else None
if bid:
    B.answer(ck, bid[0], "hai", {"pcs": "1"}, "darpan")
page = EW.owner_page(ck, D28)
i1, i2 = page.find("Batch swaps"), page.find("2 &middot; Near expiry")
check("K2 the owner's page: Batch swaps above Near expiry, collapsed", 0 < i1 < i2 and '<details class="s979">' in page)
check("K3 Near expiry keeps the batch as listed, marked 'Darpan found it'", "BETA SYP" in page[i2:] and "Darpan found it" in page[i2:])
ck.execute("CREATE TABLE IF NOT EXISTS mi_file (type TEXT, verdict TEXT, received_at TEXT, md5 TEXT)")
ck.commit()
ny2 = EW.needs_you_lines(ck, D28)
check("K4 the Needs-you lines carry the swap's red", any("Batch swaps" in x["text"] for x in ny2), ny2)
ck.close()

# ---------------------------------------------------------------- L: Darpan's page and doors
try:
    from flask import Flask
    SM = importlib.import_module("stockmatch")
    app = Flask("walk_s979")
    dbl = os.path.join(TMP, "l.db")
    cl_ = mkdb(dbl)
    fill(cl_)
    with cl_:
        B.find(cl_, D28, T(2026, 11, 28, 23, 57))
    cl_.close()

    def getdb():
        c = sqlite3.connect(dbl)
        c.row_factory = sqlite3.Row
        return c
    WHO = {"u": "darpan"}

    def req(*roles, unit=None):
        return dict(user=WHO["u"], roles=["maker"] if WHO["u"] == "darpan" else ["checker"]), None
    SM.init(app, getdb, req)
    SM.root_of = lambda con, cid=None: 1
    SM.report = lambda con, root: dict(count_id=1)
    SM.section_state = lambda con, d, for_owner=False: dict(ok=True, lines=[], pairs=[], progress=dict(all=False, need=0))
    SM._s418_extra = lambda con, cid: {}
    SM._sw_view = lambda con, who=None: None
    c = app.test_client()
    r = c.get("/finance/stockmatch/api/state")
    j = r.get_json() or {}
    check("L1 the state carries the swap card (3 shelf questions)", r.status_code == 200 and len(((j.get("swap") or {}).get("ask") or [])) == 3, r.status_code)
    q = [x for x in j["swap"]["ask"] if x["item"] == "ALPHA TAB"][0]
    r = c.post("/finance/stockmatch/api/swap", json={"case": q["id"], "answer": "nahi"})
    j = r.get_json() or {}
    check("L2 POST /api/swap Nahi hai -> the bills on his card", r.status_code == 200 and j.get("saved", {}).get("kind") == "swap" and j["swap"]["bills"]
          and q["id"] in j["swap"]["bills"]["ids"], r.status_code)
    r = c.post("/finance/stockmatch/api/swap", json={"case": "x", "answer": "nahi"})
    check("L3 a bad case is refused (400)", r.status_code == 400)
    r = c.post("/finance/stockmatch/api/swap/bills", json={"ids": j["swap"]["bills"]["ids"]})
    j2 = r.get_json() or {}
    check("L4 POST /api/swap/bills records the tap", r.status_code == 200 and [x["item"] for x in j2["swap"]["made"]] == ["ALPHA TAB"], r.status_code)
    r = c.post("/finance/stockmatch/api/swap/bills", json={"ids": j["swap"]["bills"]["ids"]})
    check("L5 the same tap again is refused (409)", r.status_code == 409)
    pg = c.get("/finance/stockmatch")
    check("L6 the page carries the swap card above Aaj ki ginti", pg.status_code == 200 and b"h+=swapCards(s);" in pg.data and pg.data.find(b"h+=swapCards(s);") < pg.data.find(b"h+=s428Top(s);"))
    html_ = pg.data.decode("utf-8")
    js = html_.split("<script>", 1)[1].rsplit("</script>", 1)[0]
    jsp = os.path.join(TMP, "p.js")
    st_ = json.dumps(dict(swap=j["swap"] | dict(half=[dict(q, missing="ret", swap_hi="8 goli")]), watch=None))
    open(jsp, "w", encoding="utf-8").write("var document={getElementById:function(){return {innerHTML:'',textContent:''};}},location={search:''},window={scrollTo:function(){}},navigator={};"
                                            "var fetch=function(){return new Promise(function(){});};" + js.replace("load();", "") +
                                            "\nvar o=swapCards(%s);console.log(JSON.stringify(o));" % st_)
    try:
        out = subprocess.run(["node", jsp], capture_output=True, text=True, timeout=30)
        o = json.loads(out.stdout.strip().splitlines()[-1]) if out.stdout.strip() else ""
        check("L7 the card draws: Expiry batch / Batch badlo / STOCK bill adhoora, Nahi hai, Hai, Bhej do", all(k in o for k in (
            "Expiry batch &mdash; shelf par dekhiye", "STOCK bill adhoora", "Nahi hai", "Bhej do", "Bill 2 &middot; SALE RETURN")), (out.stderr or "")[:200])
        st0 = json.dumps(dict(swap=dict(ok=True, ask=[], bills=None, half=[], made=[])))
        open(jsp, "a", encoding="utf-8").write("\nconsole.log(JSON.stringify(swapCards(%s)));console.log(JSON.stringify(swapCards({})));" % st0)
        out = subprocess.run(["node", jsp], capture_output=True, text=True, timeout=30)
        ls_ = out.stdout.strip().splitlines()
        check("L8 nothing waiting / no swap in the state: the card draws nothing", ls_[-2:] == ['""', '""'], ls_[-2:])
    except FileNotFoundError:
        check("L7 node present to draw the card", False, "node not found")
except Exception as ex:                                       # noqa: BLE001
    check("L0 the stockmatch doors", False, "%s: %s" % (type(ex).__name__, str(ex)[:200]))

shutil.rmtree(TMP, ignore_errors=True)
print("WALK %d/%d" % (len(P), len(P) + len(F)))
sys.exit(0 if not F else 1)
