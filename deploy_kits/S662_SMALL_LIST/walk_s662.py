"""walk_s662.py -- kit S662_SMALL_LIST (Sanjeevni session S359, 26-Oct-2026). Writes nothing outside --scratch.
Loads porders, purchase_app, order_rules, section_map and stock_app from the root under test and runs them on a COPY of finance.db,
on rows the walk writes for itself (F-998) where a fix is about a case.
  python walk_s662.py --new <root holding finance/ as built> --db <a COPY of finance.db> --scratch <dir> [--lib <root of unchanged modules>]
  --old <live root>: the control -- the live files under test: every S662 check red, every older check green."""
import argparse, os, shutil, sqlite3, sys, warnings, datetime as dt
warnings.filterwarnings("ignore")
ap = argparse.ArgumentParser()
ap.add_argument("--new"); ap.add_argument("--old"); ap.add_argument("--db"); ap.add_argument("--scratch"); ap.add_argument("--lib")
a = ap.parse_args()
ROOT = os.path.abspath(a.old or a.new)
LIB = os.path.abspath(a.lib or a.old or a.new)
a.scratch = os.path.abspath(a.scratch); os.makedirs(a.scratch, exist_ok=True)
DB = os.path.join(a.scratch, "walk.db")
shutil.copyfile(a.db, DB)
FIN = os.path.join(ROOT, "finance")
if LIB != ROOT:                                                    # the files under test beside every unchanged sibling (symlinks; nothing copied)
    FIN = os.path.join(a.scratch, "overlay", "finance"); os.makedirs(FIN)
    for e in os.listdir(os.path.join(LIB, "finance")):
        if not os.path.exists(os.path.join(ROOT, "finance", e)):
            os.symlink(os.path.join(LIB, "finance", e), os.path.join(FIN, e))
    for e in os.listdir(os.path.join(ROOT, "finance")):
        if e.endswith(".py"):
            shutil.copyfile(os.path.join(ROOT, "finance", e), os.path.join(FIN, e))
sys.path[:0] = [FIN]
os.chdir(a.scratch)
res = []


def check(name, ok, s662=True, note=""):
    res.append((name, bool(ok), s662, str(note)[:300]))


def con_():
    c = sqlite3.connect(DB, timeout=30)
    c.row_factory = sqlite3.Row
    return c


import flask                                                       # noqa: E402
import porders, purchase_app, order_rules, section_map, stock_app  # noqa: E402
for m in (porders, purchase_app, order_rules, section_map, stock_app):
    assert os.path.dirname(os.path.abspath(m.__file__)) == FIN, "%s not loaded from the root under test" % m.__name__
WHO = {"user": "walk_s662", "roles": ["checker"], "role": "checker"}
app = flask.Flask("walk_s662")
porders.init(app, con_, lambda *r, **k: (dict(WHO), None))
purchase_app.init(app, con_, lambda *r, **k: (dict(WHO), None))
cl = app.test_client()

# ---- A: F-987's residual (porders.api_scan_amount) on the walk's own bills -----------------------------------------------------------
c = con_()
porders.ensure_schema(c); purchase_app._ensure_s439(c)
MONTH = "2099-01"
SC = {}


def own_bill(n, marg_p, verdict=None, wrong_p=None, scan_p=None):
    bid = 990000 + n; sid = 980000 + n
    c.execute("INSERT INTO purchase_bill (id, supplier_norm, supplier, bill_no, bill_date, month, amount_p, verdict, verdict_by, verdict_at, wrong_amount_p, reason) "
              "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (bid, "WALK S662 DEALER", "WALK S662 DEALER", "W%d" % n, "2099-01-0%d" % n, MONTH, marg_p, verdict,
                                                   "earlier" if verdict else None, "2099-01-01T10:00:00" if verdict else None, wrong_p, "the first scan" if verdict else None))
    c.execute("INSERT INTO purchase_scan_link (bill_id, asset_bill_id, grade, matched_on, linked_at) VALUES (?,?,?,?,?)", (bid, sid, "PROBABLE", "walk", "2099-01-01T10:00:00"))
    SC[sid] = dict(id=sid, vendor="WALK S662 DEALER", bill_no="W%d" % n, bill_date="", amount_p=scan_p, stamp="#%d" % sid, age=0)
    return bid, sid


b1, s1 = own_bill(1, 1000000, "WRONG", 1050000, 1050000)     # already WRONG at Rs 10,500 (Marg Rs 10,000); rescanned, the paper reads 10,500
b2, s2 = own_bill(2, 2000000, None, None, 2100000)           # no verdict; paper = scan Rs 21,000, Marg Rs 20,000 -> marg_wrong (as before)
b3, s3 = own_bill(3, 3000000, "WRONG", 3100000, 3200000)     # WRONG at 31,000; this paper says 32,000 -> the owner (as before)
b4, s4 = own_bill(4, 4000000, None, None, 4100000)           # paper = Marg -> scan_wrong (as before)
c.commit()
porders._s440_scans = lambda con: dict(SC)                     # the asset app's scans: the walk's own four


def amount(sid, paper):
    r = cl.post("/finance/porders/api/scan/amount", json={"scan": sid, "paper": paper})
    return r.status_code, (r.get_json() or {})


before1 = tuple(con_().execute("SELECT verdict, verdict_by, verdict_at, wrong_amount_p, reason FROM purchase_bill WHERE id=?", (b1,)).fetchone())
code, j = amount(s1, "10500")
after1 = tuple(con_().execute("SELECT verdict, verdict_by, verdict_at, wrong_amount_p, reason FROM purchase_bill WHERE id=?", (b1,)).fetchone())
st1 = con_().execute("SELECT amount_state FROM purchase_scan_state WHERE asset_bill_id=?", (s1,)).fetchone()
check("A1 a rescan at the paper amount the bill is already WRONG at stands with the verdict (marg_wrong, not the owner's list)",
      code == 200 and j.get("outcome") == "marg_wrong" and st1 and st1[0] == "marg_wrong", note=(code, j.get("outcome"), st1 and st1[0]))
check("A2 ... and nothing is written to that bill (verdict, by, at, amount, reason as they were)", before1 == after1, note=(before1, after1))
code, j = amount(s2, "21000")
v2 = con_().execute("SELECT verdict, wrong_amount_p FROM purchase_bill WHERE id=?", (b2,)).fetchone()
check("A3 a first scan, paper = scan, Marg different: Marg galat, the verdict written (unchanged)", j.get("outcome") == "marg_wrong" and tuple(v2) == ("WRONG", 2100000), s662=False, note=(j, tuple(v2)))
code, j = amount(s3, "32000")
check("A4 a WRONG bill whose new paper says another amount still goes to the owner (unchanged)", j.get("outcome") == "owner", s662=False, note=j)
code, j = amount(s4, "40000")
check("A5 paper = Marg: the scan was misread (unchanged)", j.get("outcome") == "scan_wrong", s662=False, note=j)
code, j = amount(s1, "10500")
check("A6 the same scan again: already settled, 409 (unchanged)", code == 409 and j.get("error") == "settled", s662=False, note=(code, j))

# ---- B: the purchase page's staff_send door ------------------------------------------------------------------------------------------
n0 = con_().execute("SELECT COUNT(*) FROM purchase_order").fetchone()[0]
r = cl.post("/finance/purchase/api/order", json={"action": "staff_send", "vendor": "WALK S662 DEALER", "lines": [{"item": "WALK ITEM", "qty": 1}]})
j = r.get_json() or {}
n1 = con_().execute("SELECT COUNT(*) FROM purchase_order").fetchone()[0]
check("B1 the purchase page's staff_send answers 409 send_via_order_list and writes no order", r.status_code == 409 and j.get("error") == "send_via_order_list" and n1 == n0,
      note=(r.status_code, j.get("error"), n0, n1))
src = open(os.path.join(FIN, "purchase_app.py"), encoding="utf-8").read()
check("B2 the page has no Send on WhatsApp button; its sentence names the order list", 'onclick="sendWA(' not in src and "one order list (<b>Order karna hai</b>)" in src)
check("B3 the internal _staff_send the order list uses is still there (order_rules and porders call it)",
      callable(getattr(purchase_app, "_staff_send", None)) and "pa._staff_send(" in open(os.path.join(FIN, "order_rules.py"), encoding="utf-8").read(), s662=False)
r = cl.post("/finance/purchase/api/order", json={"action": "arrive"})
check("B4 the other actions of the same door still reach their code (arrive: not refused as a send)", (r.get_json() or {}).get("error") != "send_via_order_list", s662=False,
      note=(r.status_code, (r.get_json() or {}).get("error")))

# ---- C: the learnt lead needs three orders ----------------------------------------------------------------------------------------
c = con_()
TODAY = dt.date(2026, 11, 1)
sups = [r[0] for r in c.execute("SELECT supplier_norm FROM order_supplier_rule ORDER BY supplier_norm")]
ll = {s: order_rules.lead_learned(c, s, TODAY) for s in sups}
check("C1 every supplier's learnt lead stands on 3 orders or more, or on none", all(n == 0 or n >= 3 for _v, n in ll.values()),
      note={s[:14]: v for s, v in ll.items() if 0 < v[1] < 3})
check("C2 ... and a supplier with 3 or more orders still learns (at least one on this copy)", any(n >= 3 and v is not None for v, n in ll.values()), s662=False,
      note={s[:14]: v for s, v in ll.items() if v[1] >= 3})
try:
    order_rules.rhythm(c, TODAY)
    SPINE = "the live spine"
except Exception:                                                  # noqa: BLE001 -- offline: no spine.db beside the code; the rows' own rhythm stands in
    SPINE = "the rules' own rhythm (no spine here)"
    _rh = {r["supplier_norm"]: dict(supplier=r["supplier"], cadence=r["cadence"] if r["cadence"] in order_rules.GAP else "weekly", bills90=r["bills90"],
                                    gap=r["rhythm_days"], avg_month_p=r["avg_month_p"], how=r["cadence_how"], bill_days90=r["bill_days90"])
           for r in c.execute("SELECT * FROM order_supplier_rule")}
    order_rules.rhythm = lambda con, today=None: dict(_rh)
order_rules.reseed(c, TODAY, "walk_s662")
rows = [dict(r) for r in c.execute("SELECT supplier_norm, lead_days, lead_learned, lead_n, owner_fields FROM order_supplier_rule")]
check("C3 the 1-Nov reseed (on " + SPINE + "): a supplier's lead moves to 2 only on 3 orders or more", all(r["lead_days"] == 1 or (r["lead_n"] or 0) >= 3 or "lead_days" in (r["owner_fields"] or "") for r in rows),
      note=[(r["supplier_norm"][:14], r["lead_days"], r["lead_n"]) for r in rows if r["lead_days"] != 1])
check("C4 the rule's words read (no 'learned from 1 order')", all("learned from 1 order)" not in order_rules.rule_words(c, r) and "learned from 2 orders" not in order_rules.rule_words(c, r)
                                                                for r in [dict(x) for x in c.execute("SELECT * FROM order_supplier_rule")]))

# ---- D: F-1023, DYNA a whole word -----------------------------------------------------------------------------------------------------
check("D1 DYNAPAR QPS PLUS is a medicine (section_map.classify)", section_map.classify("DYNAPAR QPS PLUS") == "Medicines", note=section_map.classify("DYNAPAR QPS PLUS"))
check("D2 ... and not an orthotic to stock_app either", not stock_app._is_orthotic("DYNAPAR QPS PLUS"))
dyna = ["ANKLE BINDER M DYNA", "ARM SLING M DYNA", "DYNA WRIST BRACE REVER LONG", "DYNA LS BELT", "TENNIS ELBOW DYNA"]
check("D3 the Dyna orthotics stay orthotics in both lists", all(section_map.classify(x) == "Orthotics" and stock_app._is_orthotic(x) for x in dyna), s662=False)
seeded = [(r[0], r[1]) for r in con_().execute("SELECT item, seeded_as FROM stock_item_section WHERE seeded_as IS NOT NULL")]
bad = [x for x, s in seeded if section_map.classify(x) != s]
check("D4 every item the owner's section table seeded classifies as it was seeded (%d items)" % len(seeded), not bad, s662=False, note=bad[:5])
names = set()
cc = con_()
for (t,) in cc.execute("SELECT name FROM sqlite_master WHERE type='table'"):
    cols = [r[1] for r in cc.execute("PRAGMA table_info('%s')" % t)]
    if "item" in cols:
        names |= {r[0] for r in cc.execute("SELECT DISTINCT item FROM '%s' WHERE item IS NOT NULL" % t)}
OLDW = tuple("DYNA" if w == " DYNA " else w for w in section_map._ORTHOTIC_WORDS)
was = dict(section_map.__dict__)
moved = []
for x in sorted(names):
    now = section_map.classify(x)
    section_map._ORTHOTIC_WORDS = OLDW
    old = section_map.classify(x)
    section_map._ORTHOTIC_WORDS = was["_ORTHOTIC_WORDS"]
    if now != old:
        moved.append(x)
check("D5 over every item name in the database (%d), only DYNAPAR QPS PLUS changes section" % len(names), moved == ["DYNAPAR QPS PLUS"], note=moved[:6])

# ---- the verdict --------------------------------------------------------------------------------------------------------------------
for n, ok, s, note in res:
    print("%s  %s%s" % ("green" if ok else "RED  ", n, "" if ok else "   -- " + note))
g = sum(1 for _n, ok, _s, _x in res if ok)
if a.old:
    r662 = sum(1 for _n, ok, s, _x in res if s and not ok); rold = sum(1 for _n, ok, s, _x in res if not s and not ok)
    print("%d S662 check(s) red · %d older red · %d green" % (r662, rold, g))
else:
    print("%d of %d green" % (g, len(res)))
