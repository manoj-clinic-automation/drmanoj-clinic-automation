#!/usr/bin/env python3
# walk_s958.py · kit S958_DARPAN_LISTS · Sanjeevni session 522 · 26-Nov-2026
# On a COPY of finance.db: python walk_s958.py CODE_DIR COPY_DB FROM_DIR [control]. PASS / FAIL / INFO, RESULT last.
# Removes its own rows first (asks / roster day / notice slot by S958WALK); sets its own day; pushes go to a stub file.
import datetime as dt
import importlib.util
import json
import os
import sqlite3
import sys
import tempfile

CODE, DB, OLD = sys.argv[1], sys.argv[2], sys.argv[3]
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path = [CODE] + [x for x in sys.path if os.path.abspath(x or ".") != _HERE]
os.environ["FINANCE_DB"] = DB
STUB = os.path.join(tempfile.mkdtemp(prefix="s958w"), "push.jsonl")
os.environ["ORDER_PUSH_STUB"] = STUB
fails = []


def check(name, ok, info=""):
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name, (" -- " + str(info)) if info else ""))
    if not ok:
        fails.append(name)


def pushes():
    try:
        return [json.loads(x) for x in open(STUB, encoding="utf-8") if x.strip()]
    except OSError:
        return []


def load_old(name):
    spec = importlib.util.spec_from_file_location(name + "_from", os.path.join(OLD, name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


import order_track as OT                                      # noqa: E402
import stock_watch as SW                                      # noqa: E402
import order_rules as OR                                      # noqa: E402
import aaj_seed as AS                                         # noqa: E402
print("INFO  code %s · order_track %s %s · stock_watch %s" % (CODE, OT.VERSION, OT.KIT, SW.VERSION))
check("the versions: order_track 1.3 (S958) · stock_watch 1.14", (OT.VERSION, OT.KIT, SW.VERSION) == ("1.3", "S958_DARPAN_LISTS", "1.14"), (OT.VERSION, OT.KIT, SW.VERSION))
con = sqlite3.connect(DB, timeout=60)
con.execute("DELETE FROM stock_watch_ask WHERE by='S958WALK'")
con.execute("DELETE FROM order_notice WHERE slot='S958W'")
con.commit()
now = dt.datetime.now().replace(microsecond=0)

# ---- A: one not-needed rule
GL, GC = (OT.gone(con) if hasattr(OT, "gone") else ({}, {}))
na_late = {int(str(r[0]).split(":")[1]): r[1] for r in con.execute("SELECT ref, status FROM order_s778_na WHERE kind='late' AND status IN ('asked','stop','came') AND cleared_at IS NULL")}
lat = {int(str(r[0])) for r in con.execute("SELECT ref FROM order_d1053_later WHERE kind='carry'")}
print("INFO  not-needed lines %s · carries %s" % (sorted(GL.items())[:8], sorted(GC.items())[:8]))
check("every stopped / asked / came late line of his and Darpan's is in the one rule", na_late and all(k in GL for k in na_late), (na_late, GL))
check("every 'Abhi nahi chahiye' carry of Darpan's is in the one rule", all(k in GC for k in lat), (lat, GC))
OTO = load_old("order_track")
old_late = {(s["id"], x["id"]) for s in OTO.late_orders(con, now) for x in s["lines"] if x["state"] in ("open", "part")}
new_late = {(s["id"], x["id"]) for s in OT.late_orders(con, now) for x in s["lines"] if x["state"] in ("open", "part")}
gone_late = old_late - new_late
print("INFO  late lines old %d -> new %d; off the call list: %s" % (len(old_late), len(new_late), sorted(gone_late)))
check("the call list loses exactly the lines no longer needed (none added)", new_late <= old_late and all(l in GL or l == 316 for (_o, l) in gone_late), sorted(gone_late))
tol = con.execute("SELECT l.order_id, l.id FROM purchase_order_line l WHERE l.item='TOLTRIS PLUS'").fetchone()
check("TOLTRIS PLUS (Shivaaz, 12-Oct; he stopped it 22-11) is off the call list", tol is not None and tuple(tol) in old_late and tuple(tol) not in new_late, tol)
o28 = next((s for s in OT.light_all(con, now, oids=[int(tol[0])])), None) if tol else None
l71 = next((x for x in (o28 or {}).get("lines", []) if x["id"] == int(tol[1])), None) if tol else None
check("the order itself keeps the stopped line (settled, marked not needed) -- its page still shows it", bool(l71 and l71["state"] == "settled" and l71.get("gone")), (l71 or {}).get("state"))
t_old, t_new = OTO.tiles(OTO.light_all(con, now)), OT.tiles(OT.light_all(con, now))
check("the order page's tiles never count an order no longer needed as 'not arrived' (%s -> %s)" % (t_old["not_arrived"], t_new["not_arrived"]), t_new["not_arrived"] <= t_old["not_arrived"], (t_old, t_new))
aw_old = {s["id"] for s in OTO.awaited(con, now)}
aw_new = {s["id"] for s in OT.awaited(con, now)}
check("the Maal aaya list never gains an order", aw_new <= aw_old, sorted(aw_new - aw_old))
# ---- B: the duplicate line (order 123: XL twice, bill 842 brought 2 on the first line)
o123 = next((s for s in OT.light_all(con, now, oids=[123])), None)
st316 = next((x["state"] for x in (o123 or {}).get("lines", []) if x["id"] == 316), None)
o123o = next((s for s in OTO.light_all(con, now, oids=[123])), None)
st316o = next((x["state"] for x in (o123o or {}).get("lines", []) if x["id"] == 316), None)
check("KNEE SUPPORT XL HINGED, the second line of order 123: came on bill 842 (was %s)" % st316o, st316 == "came" and st316o != "came", (st316o, st316))
others = [(x["id"], x["state"]) for x in (o123 or {}).get("lines", []) if x["id"] != 316]
others_o = [(x["id"], x["state"]) for x in (o123o or {}).get("lines", []) if x["id"] != 316]
check("order 123's other lines unchanged", others == others_o, (others_o, others))
# ---- C: the carry pass on this copy
before = {r[0]: r[1] for r in con.execute("SELECT id, COALESCE(dropped_by,'') FROM order_carry")}
R = OT.carry_pass(con, now, who="S958WALK")
after = {r[0]: r[1] for r in con.execute("SELECT id, COALESCE(dropped_by,'') FROM order_carry")}
moved = {k: (before.get(k), v) for k, v in after.items() if before.get(k) != v}
print("INFO  carry pass: %s · moved %s" % (R, moved))
check("the XL's carry (57) dropped as came; Darpan's 'Abhi nahi chahiye' carry (48) dropped with its reason",
      after.get(57) == "came" and str(after.get(48)).startswith("s958_not_now"), (after.get(57), after.get(48)))
c48 = con.execute("SELECT kind, ref, sheet_key, by, at FROM order_d1053_later WHERE kind='carry' AND ref='48'").fetchone()
if c48:                                                       # his 'keep' (here: the tap taken back) opens the carry again; then put back
    con.execute("DELETE FROM order_d1053_later WHERE kind='carry' AND ref='48'")
    OT.carry_pass(con, now, who="S958WALK")
    back = con.execute("SELECT dropped_at FROM order_carry WHERE id=48").fetchone()
    con.execute("INSERT INTO order_d1053_later (kind, ref, sheet_key, by, at) VALUES (?,?,?,?,?)", tuple(c48))
    con.commit()
    OT.carry_pass(con, now, who="S958WALK")
    again = con.execute("SELECT dropped_by FROM order_carry WHERE id=48").fetchone()
    check("a carry the rule dropped opens again once it is needed again, and drops again", back is not None and back[0] is None and str(again[0]).startswith("s958_"), (back, again))
oc = {r[0] for r in con.execute("SELECT id FROM order_carry WHERE done_at IS NULL AND dropped_at IS NULL")}   # the table itself (the second look)
check("no open carry left in the table that the one rule says is not needed", not (oc & set(GC)), sorted(oc & set(GC)))
k28 = next((s.get("key") for s in OT.light_all(con, now, oids=[int(tol[0])])), None) if tol else None
check("TOLTRIS PLUS's order (every line no longer needed) is 'dropped' -- on no list and no tile", k28 == "dropped", k28)
# ---- D: his next-list asks every morning; pushes
S = SW.settings(con)
d = dt.date.today()
while SW._spot_day(S, d):
    d += dt.timedelta(days=1)                                 # a morning that is NOT a spot day (the walk's own day)
con.execute("DELETE FROM stock_spot_roster WHERE day=?", (d.isoformat(),))
con.execute("UPDATE stock_watch_ask SET roster_id=NULL WHERE roster_id IS NOT NULL AND roster_id NOT IN (SELECT id FROM stock_spot_roster)")
for it in ("JAKMAC 5", "ZUPRINOR 5"):
    if not con.execute("SELECT 1 FROM stock_watch_ask WHERE item=? AND done_at IS NULL AND COALESCE(mode,'next')='next' AND roster_id IS NULL", (it,)).fetchone():
        con.execute("INSERT INTO stock_watch_ask (item_norm, item, by, at, mode) VALUES (?,?,?,?,'next')", (SW.norm_name(it), it, "S958WALK", SW.now_iso()))
con.commit()
nd = SW.next_roster_day(S, d - dt.timedelta(days=1), con) if "con" in SW.next_roster_day.__code__.co_varnames else SW.next_roster_day(S, d - dt.timedelta(days=1))
check("the next-list day is the next morning when his asks wait (%s)" % d, nd == d, nd)
pv = SW.preview_roster(con, d, S)
check("the preview of a non-spot morning holds only his asks", pv and all(x.get("reason") == "you asked for it" for x in pv), [x.get("item") for x in pv])
n0 = len(pushes())
lazy = SW.build_roster(con, d, S, who="S958WALK")              # a page opened on a non-spot day (no asks_ok): writes nothing
check("a page opened on a non-spot day never writes the list (his asks wait for the morning)", not lazy["items"] and len(pushes()) == n0, [x["item"] for x in lazy["items"]])
RV = SW.build_roster(con, d, S, who="S958WALK", asks_ok=True) if "asks_ok" in SW.build_roster.__code__.co_varnames else SW.build_roster(con, d, S, who="S958WALK")
items = [x["item"] for x in RV["items"]]
print("INFO  roster of %s: %s" % (d, items))
check("a non-spot morning builds a list of his asks only (JAKMAC 5, ZUPRINOR 5 among them, nothing ranked)",
      "JAKMAC 5" in items and "ZUPRINOR 5" in items and all(x["reason"] == "you asked for it" for x in RV["items"]), [(x["item"], x["reason"]) for x in RV["items"]])
P1 = pushes()[n0:]
check("one push to Darpan for the list, opening his count screen", len(P1) == 1 and P1[0]["user"] == "darpan" and P1[0]["payload"]["url"] == "/finance/stockmatch", P1)
n1 = len(pushes())
ok, msg, code = SW.ask(con, "CROCAL", "S958WALK", mode="now")
P2 = pushes()[n1:]
check("his Count now reaches Darpan's phone, opening his count screen", ok and len(P2) == 1 and P2[0]["user"] == "darpan" and P2[0]["payload"]["url"] == "/finance/stockmatch"
      and "CROCAL" in P2[0]["payload"]["body"], (msg, P2))
due = AS.DUE.get("darpan.spot_count", "")
con.execute("UPDATE stock_spot_roster SET day=date('now','localtime') WHERE day=?", (d.isoformat(),))
n_due = con.execute(due).fetchone()[0] if due else None
n_ros = con.execute("SELECT COUNT(*) FROM stock_spot_roster WHERE answered_at IS NULL AND day=date('now','localtime')").fetchone()[0]
n_now = con.execute("SELECT COUNT(*) FROM stock_watch_ask WHERE done_at IS NULL AND COALESCE(mode,'next')='now'").fetchone()[0]
check("Aaj ka kaam's count line = today's list (%d) + his Count-now asks (%d, CROCAL among them)" % (n_ros, n_now), n_now >= 1 and n_due == n_ros + n_now, (n_due, n_ros, n_now))
d2 = d + dt.timedelta(days=1)
while SW._spot_day(S, d2):
    d2 += dt.timedelta(days=1)
con.execute("DELETE FROM stock_spot_roster WHERE day=?", (d2.isoformat(),))
waiting = [r[0] for r in con.execute("SELECT id FROM stock_watch_ask WHERE done_at IS NULL AND roster_id IS NULL AND COALESCE(mode,'next')<>'now'")]
for i in waiting:
    con.execute("UPDATE stock_watch_ask SET roster_id=-958 WHERE id=?", (i,))
con.commit()
n3 = len(pushes())
RN = SW.build_roster(con, d2, S, who="S958WALK", asks_ok=True) if "asks_ok" in SW.build_roster.__code__.co_varnames else dict(items=[1])
check("a non-spot morning with nothing asked writes nothing and pushes nothing", not RN["items"] and len(pushes()) == n3, RN.get("items"))
con.execute("UPDATE stock_watch_ask SET roster_id=NULL WHERE roster_id=-958")
con.commit()
con.execute("DELETE FROM stock_watch_ask WHERE by='S958WALK'")
con.execute("DELETE FROM stock_spot_roster WHERE day=date('now','localtime') AND asked_at>=?", ((now - dt.timedelta(minutes=5)).isoformat(),))
con.commit()
# ---- E: Darpan's order notices land on his page
n2 = len(pushes())
OR.send_notice(con, dt.date.today(), "S958W", who="S958WALK", to=["darpan", "shavez"], text="S958 walk")
P3 = {p["user"]: p["payload"]["url"] for p in pushes()[n2:]}
check("the order notice opens Darpan's own page for him, reception's for the others", P3.get("darpan") == "/finance/darpan/kal#order" and P3.get("shavez") == "/finance/porders", P3)
con.execute("DELETE FROM order_notice WHERE slot='S958W'")
con.commit()
# ---- F: the pages and the worker (text)
dk = open(os.path.join(CODE, "darpan_kal.html"), encoding="utf-8").read()
sm = open(os.path.join(CODE, "stockmatch.html"), encoding="utf-8").read()
check("Darpan's page follows #order when already open, and listens for the app's tap", "hashchange" in dk and "s958_nav" in dk and "s958_nav" in sm, "")
swp = os.path.join(CODE, "portal_sw.js")
sw = open(swp, encoding="utf-8").read() if os.path.exists(swp) else ""
check("the app's worker brings up Darpan's open page and tells it where to go", "s958_nav" in sw and "postMessage" in sw, swp)
con.close()
print("RESULT: %s" % ("ALL PASS" if not fails else "%d FAIL" % len(fails)))
