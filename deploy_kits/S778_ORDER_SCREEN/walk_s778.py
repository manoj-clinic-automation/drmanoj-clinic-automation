#!/usr/bin/env python3
"""walk_s778.py FILES_DIR SHARED_DIR FINANCE_DIR SCHEMA [--control]
A walk on MADE-UP rows (no live data): porders_s454.py and order_s778.py from FILES_DIR (the kit's, or the live ones for the control),
the rest from FINANCE_DIR. SCHEMA = a finance.db opened read only (its tables' layout only, never a row) or a schema_only.json.
The pages and doors are driven through a Flask test client with a stand-in for porders' sign-in. Last line: 'WALK S778 GREEN' or,
with --control on the live files, 'CONTROL S778 RED as it must be'."""
import datetime as dt
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
import types

FILES, SHARED, FIN, SCHEMA = sys.argv[1:5]
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != HERE]   # the kit folder carries order_s778.py: never imported from there
CONTROL = "--control" in sys.argv
TMP = tempfile.mkdtemp(prefix="w778_")
RUN = os.path.join(TMP, "run")
os.makedirs(RUN)
for f in ("porders_s454.py", "order_s778.py"):
    if os.path.exists(os.path.join(FILES, f)):
        shutil.copyfile(os.path.join(FILES, f), os.path.join(RUN, f))
sys.path[:0] = [RUN, FIN, SHARED]
os.environ["SPINE_DB"] = os.path.join(TMP, "no_spine.db")
os.environ["ORDER_PUSH_NONE"] = "1"                         # a walk never sends a Web Push

DB = os.path.join(TMP, "f.db")
if SCHEMA.endswith(".json"):
    ddl = json.load(open(SCHEMA, encoding="utf-8"))["ddl"]
else:
    s = sqlite3.connect("file:%s?mode=ro" % SCHEMA, uri=True, timeout=30)
    ddl = [r[0] for r in s.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%' "
                                   "ORDER BY CASE type WHEN 'table' THEN 0 ELSE 1 END, name")]
    s.close()
con = sqlite3.connect(DB, timeout=30)
con.row_factory = sqlite3.Row
for q in ddl:
    try:
        con.execute(q)
    except sqlite3.Error:
        pass
con.commit()

RES = []


def check(name, ok):
    RES.append((name, bool(ok)))
    print(("GREEN " if ok else "RED   ") + name)


ROLE = {"kind": "sender", "user": "shavez"}
po = types.ModuleType("porders")
po.S441 = None
po._auth = lambda: (dict(user=ROLE["user"], login=ROLE["user"]), con, ROLE["kind"], None)
po.vendor_of = lambda c: "WALK ORTHO SURGICALS"
sys.modules["porders"] = po

from flask import Flask  # noqa: E402

import order_rules  # noqa: E402
order_rules.RULES_JSON = os.path.join(TMP, "order_rules.json")
import order_sheet as OS  # noqa: E402
OS.ensure(con)
order_rules.ensure(con)
T0 = OS.today()


def back(n):
    """n working days (Sundays not counted) before today."""
    d = T0
    while n > 0:
        d -= dt.timedelta(days=1)
        if d.weekday() != 6:
            n -= 1
    return d


def iso(d, hm="10:00:00"):
    return "%sT%s" % (d.isoformat(), hm)


A, B, K, S = "WALK ALPHA PHARMA", "WALK BETA DRUGS", "WALK KAPPA MEDICOS", "WALK SIGMA FORMULATIONS"
pa = OS._pa()
sk = {v: pa.supplier_key(v) for v in (A, B, K, S)}
for k, v in (("order.source", "marg_sheet"), ("order.track_since", (T0 - dt.timedelta(days=25)).isoformat()), ("order.deliver_days", "2"),
             ("order.deliver_skip", "SUN"), ("order.freeze", ""), ("order.old_show_days", "60"), ("order.sheet_max_age_days", "7")):
    con.execute("INSERT INTO setting (key, value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (k, v))
con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('porders.senders', 'shavez')")


def order(oid, vendor, day, status, lines):
    con.execute("INSERT INTO purchase_order (id, created_at, created_by, vendor, status, supplier_norm, order_src, order_via, section) VALUES (?,?,?,?,?,?,?,?,?)",
                (oid, iso(day), "Shavez", vendor, status, sk[vendor], "s454", "call", "Medicines"))
    for lid, item, packs in lines:
        con.execute("INSERT INTO purchase_order_line (id, order_id, item, packs, pack_size, units) VALUES (?,?,?,?,?,?)", (lid, oid, item, packs, 10, packs * 10))


order(1, B, back(4), "sent", [(11, "WALKCAL 500", 5)])           # late, 4 working days -> orange
order(2, A, T0 - dt.timedelta(days=30), "received", [(21, "WALKGEL", 3)])   # before track_since: its carry stays open
order(3, B, back(2), "sent", [(31, "WALKNEW 2", 2)])             # 2 working days: not old yet
order(5, B, back(5), "sent", [(51, "WALKMED 16", 2)])            # late to Beta, but Kappa brings WALKMED 16: a wrong dealer in the box
con.execute("INSERT INTO order_carry (vendor, supplier_norm, item, from_order_id, from_line_id, qty, pack_size, reason, at) VALUES (?,?,?,?,?,?,?,?,?)",
            (A, sk[A], "WALKGEL", 2, 21, 3, 1, "marg_short", iso(T0 - dt.timedelta(days=29))))
con.execute("INSERT INTO order_sheet (id, md5, name, source, stamp, taken_at, newest_date) VALUES (1,'walk','walk','push',?,?,?)",
            (T0.strftime("%Y%m%d") + "-090000", iso(T0, "09:00:00"), T0.isoformat()))


def sline(lid, entry, item, vendor, qty, state, day):
    con.execute("INSERT INTO order_sheet_line (id, entry_no, item_printed, item, resolved, supplier, supplier_norm, packing, pack_size, line_date, qty, strip, kind, state,"
                " first_sheet, last_sheet, created_at) VALUES (?,?,?,?,1,?,?,'1*10',10,?,?,1,'new',?,1,1,?)",
                (lid, entry, item, item, vendor, sk[vendor], day.isoformat(), qty, state, iso(day)))


sline(101, "E1", "WALKMED 8", S, 4, "to_order", T0)
sline(102, "E1", "WALKDOL SP", S, 2, "to_order", T0)
sline(103, "E2", "WALKZIN", K, 1, "to_order", T0)
sline(104, "E3", "WALKOLD 1", A, 6, "old", T0 - dt.timedelta(days=12))
sline(105, "E1", "WALKMED 16", S, 1, "to_order", T0)
for i, (vendor, item, bill, day) in enumerate(((K, "WALKMED 8", "K1", T0 - dt.timedelta(days=20)), (K, "WALKMED 8", "K2", T0 - dt.timedelta(days=5)),
                                              (S, "WALKDOL SP", "S1", T0 - dt.timedelta(days=40)), (K, "WALKMED 16", "K2", T0 - dt.timedelta(days=5)))):
    con.execute("INSERT INTO purchase_line (id, supplier_norm, bill_no, bill_date, item, qty, source_md5, direction) VALUES (?,?,?,?,?,?,?,?)",
                (i + 1, sk[vendor], bill, day.isoformat(), item, 1, "walk", "PURCHASE"))
con.execute("INSERT INTO order_item_rule (item_norm, item, rule, value, set_by, set_at) VALUES (?,?,?,?,?,?)",
            (pa.norm("WALKDOL SP"), "WALKDOL SP", "max_shelf", 30, "manoj", iso(T0 - dt.timedelta(days=50))))
con.commit()

import porders_s454 as PS  # noqa: E402
app = Flask(__name__)
PS.init(app)
cl = app.test_client()
try:
    import order_s778 as S778  # noqa: E402
except Exception:                                              # noqa: BLE001 -- the control: the module is not there
    S778 = None


def as_(kind):
    ROLE.update(kind=kind, user=("manoj" if kind == "owner" else "shavez"))


def page(u):
    r = cl.get(u)
    return r.status_code, r.get_data(as_text=True)


def post(u, b):
    r = cl.post(u, json=b)
    return r.status_code, (r.get_json(silent=True) or {})


def box(h):
    i = h.find('id="s778box"')
    if i < 0:
        return ""
    j = h.find('id="s778oncard"', i)
    k = h.find('<div class="mut" id="whose"', i)
    ends = [x for x in (j, k, h.find('<a class="big', i)) if x > 0]
    return h[i:min(ends) if ends else len(h)]


def card_lines(sn):
    e = OS.entry_of(con, sn)
    return [(l["item"], l["src"], int(l["qty"])) for l in (e or {}).get("lines", [])]


def safe(name, fn):
    try:
        check(name, fn())
    except Exception as e:                                     # noqa: BLE001
        check("%s (%s: %s)" % (name, type(e).__name__, str(e)[:90]), False)


def q1(q, a=()):
    try:
        r = con.execute(q, a).fetchone()
        return r[0] if r else 0
    except sqlite3.Error:
        return 0


def line_of(h, item):
    m = re.search(r'<div class="s778l" data-kind="(\w+)" data-ref="([^"]+)">(?:(?!<div class="s778l").)*?%s' % re.escape(item), h, re.S)
    return (m.group(1), m.group(2)) if m else (None, None)


# 1 · the red box
as_("sender")
code, h = page("/finance/porders/s454/order")
bx = box(h)
safe("1.1 Order karna hai 200 with the red box at the top", lambda: code == 200 and bx and h.find('id="s778box"') < h.find('id="margopen"') if 'id="margopen"' in h else code == 200 and bool(bx))
safe("1.2 the carry WALKGEL (A, 30 days) in the box, red, its age big", lambda: "WALKGEL" in bx and re.search(r'<div class="s778age">\d+<small>din</small></div><div><div class="it">WALKGEL', bx))
safe("1.3 the late WALKCAL 500 (B, 4 working days) in the box, orange", lambda: re.search(r'<div class="s778age mid">4<small>din</small></div><div><div class="it">WALKCAL 500', bx))
safe("1.4 WALKNEW 2 (2 working days) not in the box", lambda: "WALKNEW 2" not in h[h.find('id="s778box"'):] if bx else False)
safe("1.5 Marg's old WALKOLD 1 in the box with Dobara on S543's reorder door", lambda: "WALKOLD 1" in bx and "/finance/porders/api/s454/reorder" in bx)
safe("1.6 the staff words are Hindi: Purane order, Dobara order karo, Ab nahi milta", lambda: "Purane order" in bx and "Dobara order karo" in bx and "Ab nahi milta" in bx)
as_("owner")
c2, h2 = page("/finance/porders/s454/order")
safe("1.7 the owner reads it in English", lambda: c2 == 200 and "Old orders" in box(h2) and "Order again" in box(h2))
as_("sender")
safe("1.8 workdays: Saturday -> Monday is 1, Monday -> next Monday 6 (Sundays not counted)",
     lambda: S778.workdays("2026-11-07", dt.date(2026, 11, 9)) == 1 and S778.workdays("2026-11-02", dt.date(2026, 11, 9)) == 6)

# 3 · the wrong-dealer check on the card
safe("3.1 Sigma's card warns: WALKMED 8 never came from Sigma, Kappa brings it", lambda: 'class="s778cw" data-item="WALKMED 8"' in h and "Kappa laata hai (2 bill" in h)
safe("3.2 the top line counts the wrong-dealer lines (2)", lambda: 'id="s778wdtop"' in h and "2 dawa galat dealer" in h)
safe("3.3 WALKDOL SP (Sigma has billed it) has no warning", lambda: 'data-item="WALKDOL SP"' not in h)

# 2 · Dobara order karo on a carry of a dealer with no card
k, ref = line_of(bx, "WALKGEL")
c, j = post("/finance/porders/api/s778/again", dict(kind=k, ref=ref))
safe("2.1 Dobara on WALKGEL: 200", lambda: c == 200 and j.get("ok"))
safe("2.2 Alpha now has a card carrying WALKGEL (an S778 line)", lambda: ("WALKGEL", "s778", 3) in card_lines(sk[A]))
code, h = page("/finance/porders/s454/order")
safe("2.3 WALKGEL left the box at once", lambda: code == 200 and "WALKGEL" not in box(h))
safe("2.4 Alpha's card names WALKGEL as old (PURANA)", lambda: re.search(r"WALKGEL <span class=\"s778tag\">PURANA · \d+ din</span>", h))
c, j = post("/finance/porders/api/s454/ordered", dict(sn=sk[A]))
oid = j.get("order_id")
safe("2.5 'Order ho gaya' on Alpha's card makes the order with WALKGEL", lambda: c == 200 and oid and con.execute(
    "SELECT COUNT(*) FROM purchase_order_line WHERE order_id=? AND item='WALKGEL'", (oid,)).fetchone()[0] == 1)
safe("2.6 the again row is done by that order; its note does not say orthotic", lambda: con.execute(
    "SELECT done_order_id FROM order_s778_again WHERE item='WALKGEL'").fetchone()[0] == oid and "orthotic" not in (con.execute(
        "SELECT note FROM purchase_order WHERE id=?", (oid,)).fetchone()[0] or ""))
code, h = page("/finance/porders/s454/order")
safe("2.7 WALKGEL is in neither the box nor a card now", lambda: "WALKGEL" not in box(h) and not card_lines(sk[A]))

# 2b · '<X> ko order karo' from the box: the line leaves the box at once and is never put on a card twice
code, h = page("/finance/porders/s454/order")
bx = box(h)
safe("2.8 the late WALKMED 16 to Beta is in the box with 'Kappa ko order karo' (no Dobara)", lambda: "Kappa ko order karo" in bx and "WALKMED 16" in bx)
c, j = post("/finance/porders/api/s778/again", dict(kind="late", ref="5:51", to=sk[K]))
c2, j2 = post("/finance/porders/api/s778/again", dict(kind="late", ref="5:51", to=sk[K]))
code, h = page("/finance/porders/s454/order")
safe("2.9 after it: WALKMED 16 is on Kappa's card once, gone from the box; a second tap writes nothing", lambda: c == 200 and c2 == 200 and j2.get("already")
     and [x for x in card_lines(sk[K]) if x[0] == "WALKMED 16"] == [("WALKMED 16", "s778", 2)] and "WALKMED 16" not in box(h)
     and q1("SELECT COUNT(*) FROM order_s778_again WHERE item='WALKMED 16'") == 1)

# 4 · Ab nahi milta on a card line, the doctor stops it, a bill lifts it
c, j = post("/finance/porders/api/s778/na", dict(sn=sk[S], src="sheet", ref="102", item="WALKDOL SP"))
safe("4.1 Ab nahi milta on Sigma's WALKDOL SP: 200", lambda: c == 200 and j.get("ok"))
safe("4.2 it left Sigma's card at once", lambda: "WALKDOL SP" not in [x[0] for x in card_lines(sk[S])])
safe("4.2b and off Marg's open order as the papers read it (sheet.pdf / marg.pdf)", lambda: 102 not in [l["id"] for l in OS.open_order(con)["groups"]["to_order"]])
ny = [l for l in order_rules.needs_you_lines(con) if "no longer available" in l.get("text", "")]
safe("4.3 the doctor's Needs-you line: 'Shavez says WALKDOL SP is no longer available (last bought ...)' opening his page",
     lambda: ny and ny[0]["text"].startswith("Shavez says WALKDOL SP is no longer available (last bought ") and ny[0]["href"] == "/finance/porders/s454/abnahi")
nid = q1("SELECT id FROM order_s778_na WHERE item='WALKDOL SP'")
c, j = post("/finance/porders/api/s778/na_answer", dict(id=nid, answer="stop"))
safe("4.4 a sender cannot answer for the doctor (403)", lambda: c == 403)
as_("owner")
c, h = page("/finance/porders/s454/abnahi")
safe("4.5 the doctor's page lists it with Stop it everywhere / Keep ordering", lambda: c == 200 and "WALKDOL SP" in h and "Stop it everywhere" in h and "Keep ordering" in h)
c, j = post("/finance/porders/api/s778/na_answer", dict(id=nid, answer="stop"))
r = con.execute("SELECT rule, note FROM order_item_rule WHERE item_norm=?", (pa.norm("WALKDOL SP"),)).fetchone()
safe("4.6 Stop it everywhere: the rule 'never' marked S778, held from the plan", lambda: c == 200 and r and r[0] == "never" and r[1].startswith("S778")
     and "WALKDOL SP" in order_rules.held_sets(con))
as_("sender")
con.execute("INSERT INTO purchase_line (id, supplier_norm, bill_no, bill_date, item, qty, source_md5, direction) VALUES (49,?,?,?,?,1,'walk','RETURN')",
            (sk[S], "R9", T0.isoformat(), "WALKDOL SP"))
con.commit()
page("/finance/porders/s454/order")
safe("4.6b a purchase RETURN of WALKDOL SP after the tap does not lift the stop", lambda: q1("SELECT rule FROM order_item_rule WHERE item_norm=?", (pa.norm("WALKDOL SP"),)) == "never")
con.execute("INSERT INTO purchase_line (id, supplier_norm, bill_no, bill_date, item, qty, source_md5, direction) VALUES (50,?,?,?,?,1,'walk','PURCHASE')",
            (sk[S], "S9", T0.isoformat(), "WALKDOL SP"))
con.commit()
page("/finance/porders/s454/order")                              # every page read runs the cron pass
r = con.execute("SELECT rule, value FROM order_item_rule WHERE item_norm=?", (pa.norm("WALKDOL SP"),)).fetchone()
safe("4.7 a newer Marg bill of WALKDOL SP lifts the stop and puts back the doctor's own rule (max_shelf 30)", lambda: r and r[0] == "max_shelf" and r[1] == 30
     and con.execute("SELECT cleared_at IS NOT NULL FROM order_s778_na WHERE id=?", (nid,)).fetchone()[0] == 1)
safe("4.8 WALKDOL SP is back on Sigma's card and on Marg's open order", lambda: "WALKDOL SP" in [x[0] for x in card_lines(sk[S])]
     and 102 in [l["id"] for l in OS.open_order(con)["groups"]["to_order"]])

# 5 · Ab nahi milta on a red-box line, Keep ordering; Undo of a stop
code, h = page("/finance/porders/s454/order")
k, ref = line_of(box(h), "WALKCAL 500")
c, j = post("/finance/porders/api/s778/na", dict(kind=k, ref=ref))
code, h = page("/finance/porders/s454/order")
safe("5.1 Ab nahi milta on the late WALKCAL 500: it leaves the box", lambda: c == 200 and "WALKCAL 500" not in box(h))
as_("owner")
n2 = q1("SELECT id FROM order_s778_na WHERE item='WALKCAL 500'")
c, j = post("/finance/porders/api/s778/na_answer", dict(id=n2, answer="keep"))
safe("5.2 Keep ordering: answered keep, no rule written", lambda: c == 200 and con.execute("SELECT status FROM order_s778_na WHERE id=?", (n2,)).fetchone()[0] == "keep"
     and not con.execute("SELECT 1 FROM order_item_rule WHERE item_norm=?", (pa.norm("WALKCAL 500"),)).fetchone())
as_("sender")
c, j = post("/finance/porders/api/s778/na", dict(sn=sk[K], src="sheet", ref="103", item="WALKZIN"))
as_("owner")
n3 = q1("SELECT id FROM order_s778_na WHERE item='WALKZIN'")
post("/finance/porders/api/s778/na_answer", dict(id=n3, answer="stop"))
c, j = post("/finance/porders/api/s778/na_answer", dict(id=n3, answer="undo"))
safe("5.3 Undo of a stop: the rule is gone (there was none before) and WALKZIN is back on Kappa's card", lambda: c == 200 and not con.execute(
    "SELECT 1 FROM order_item_rule WHERE item_norm=?", (pa.norm("WALKZIN"),)).fetchone() and "WALKZIN" in [x[0] for x in card_lines(sk[K])])
as_("sender")

# 6 · the wrong dealer: move, and '<dealer> hi sahi'
c, j = post("/finance/porders/api/s778/move", dict(sn=sk[S], src="sheet", ref="101", item="WALKMED 8", to=sk[B]))
safe("6.1 a move to a dealer who is not the one who brings it is refused (409)", lambda: c == 409)
c, j = post("/finance/porders/api/s778/move", dict(sn=sk[S], src="sheet", ref="101", item="WALKMED 8", to=sk[K]))
safe("6.2 Kappa ke card par bhejo: WALKMED 8 leaves Sigma and is on Kappa's card (4)", lambda: c == 200 and "WALKMED 8" not in [x[0] for x in card_lines(sk[S])]
     and ("WALKMED 8", "s778", 4) in card_lines(sk[K]))
c, j = post("/finance/porders/api/s778/dealer_ok", dict(sn=sk[S], item="WALKMED 16"))
code, h = page("/finance/porders/s454/order")
safe("6.3 Sigma hi sahi on WALKMED 16: remembered, no warning left, no top line", lambda: c == 200 and 'class="s778cw"' not in h and 's778wdtop' not in h)
safe("6.4 the doctor's week: every catch listed with what was done", lambda: [tuple(x) for x in con.execute(
    "SELECT supplier_norm, item, outcome FROM order_s778_wd ORDER BY supplier_norm, item")] == [(sk[B], "WALKMED 16", "moved"), (sk[S], "WALKMED 16", "kept"),
                                                                                             (sk[S], "WALKMED 8", "moved")])
ref = next((x for x in (OS.entry_of(con, sk[K]) or {}).get("lines", []) if x["item"] == "WALKMED 8"), {}).get("ref", "")
c, j = post("/finance/porders/api/s454/qty", dict(src="s778", ref=ref, item="WALKMED 8", delta=1))
safe("6.5 S454's quantity door takes an S778 line (4 -> 5)", lambda: c == 200 and ("WALKMED 8", "s778", 5) in card_lines(sk[K]))
c, h = page("/finance/porders/s454/order/" + sk[S])
safe("6.6 a dealer's own screen: 200, each line with Ab nahi milta", lambda: c == 200 and h.count('class="s778na"') == len(card_lines(sk[S])) > 0)
c, j = post("/finance/porders/api/s454/qty", dict(src="s778", ref=ref, item="WALKMED 8", remove=1, reason="dealer_no"))
safe("6.7 an S778 line removed through S454's door is closed for good (not back tomorrow)", lambda: c == 200
     and "WALKMED 8" not in [x[0] for x in card_lines(sk[K])] and q1("SELECT cleared_by FROM order_s778_again WHERE id=?", (int(ref or 0),)) == "removed")

# 7 · S543's old line, the freeze, the fail-soft
code, h = page("/finance/porders/s454/order")
c, j = post("/finance/porders/api/s454/reorder", dict(line=104))
safe("7.1 Dobara on Marg's old WALKOLD 1 (S543's door): it is on Alpha's card", lambda: c == 200 and "WALKOLD 1" in [x[0] for x in card_lines(sk[A])])
con.execute("UPDATE setting SET value=? WHERE key='order.freeze'", (json.dumps(dict(at=OS.now_iso(), reason="walk")),))
con.commit()
c, j = post("/finance/porders/api/s778/again", dict(kind="late", ref="1:11"))
safe("7.2 ordering frozen: the S778 doors refuse (423) and no S778 card is made", lambda: c == 423 and OS.entries(con) == [])
con.execute("UPDATE setting SET value='' WHERE key='order.freeze'")
con.commit()
before = [(e["vendor"], len(e["lines"])) for e in PS._s778_entries_before(con)] if S778 else None
keep = S778.adjust_entries if S778 else None


def boom(*a, **k):
    raise RuntimeError("walk: S778 broken on purpose")


keep_s = getattr(PS, "_s778", None)
if S778:
    PS._s778 = boom                                            # the module itself unreachable: every wrapper must fall back
code, h = page("/finance/porders/s454/order")
c3, h3 = page("/finance/porders/s454/order/" + sk[S])
after = [(e["vendor"], len(e["lines"])) for e in OS.entries(con)] if S778 else None
ny3 = order_rules.needs_you_lines(con)
cr3 = OS.cron_pass(con, "walk")
safe("7.3 S778 unreachable on purpose: the order page and a dealer's screen open (200) as before, no box, the cards as order_sheet makes them, "
     "Needs-you and the cron pass answer", lambda: S778 is not None and code == 200 and c3 == 200 and 's778box' not in h and 's778na' not in h3
     and before == after and isinstance(ny3, list) and str(cr3.get("s778", "")).startswith("error"))
if S778:
    PS._s778 = keep_s

if S778:                                                       # the kit's undo: every stop lifted, every held / moved line given back
    as_("sender")
    post("/finance/porders/api/s778/na", dict(sn=sk[S], src="sheet", ref="102", item="WALKDOL SP"))
    as_("owner")
    post("/finance/porders/api/s778/na_answer", dict(id=q1("SELECT MAX(id) FROM order_s778_na"), answer="stop"))
    lt = S778.lift_all(con)
    safe("7.4 the undo's lift: the stop lifted to the doctor's own rule, the held line back on Marg's open order",
         lambda: lt.startswith("LIFTED: 1 hold") and q1("SELECT rule FROM order_item_rule WHERE item_norm=?", (pa.norm("WALKDOL SP"),)) == "max_shelf"
         and 102 in [l["id"] for l in OS.open_order(con)["groups"]["to_order"]])
bad = [n for n, ok in RES if not ok]
print("%d/%d green" % (len(RES) - len(bad), len(RES)))
if CONTROL:
    print("CONTROL S778 RED as it must be" if bad else "CONTROL S778 GREEN -- the control proves nothing")
else:
    print("WALK S778 GREEN" if not bad else "WALK S778 RED (%d)" % len(bad))
shutil.rmtree(TMP, ignore_errors=True)
