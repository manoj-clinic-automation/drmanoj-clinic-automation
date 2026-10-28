"""walk_s676.py -- kit S676_SECTIONS_BY_FAMILY (Sanjeevni session S362, 28-Oct-2026). Writes nothing outside --scratch.
Loads section_map and stock_app from the root under test and runs them on a COPY of finance.db, on rows the walk writes for itself (F-998).
  python walk_s676.py --new <root holding finance/ as built> --db <a COPY of finance.db> --scratch <dir> [--lib <root of unchanged modules>]
  --old <live root>: the control -- every S676 check red, every older check green.
  --after-data: the sweep has already run on this database (the installer's data step): C3 expects 0 moves and C1 is skipped."""
import argparse, os, shutil, sqlite3, sys, warnings, datetime as dt
warnings.filterwarnings("ignore")
ap = argparse.ArgumentParser()
ap.add_argument("--new"); ap.add_argument("--old"); ap.add_argument("--db"); ap.add_argument("--scratch"); ap.add_argument("--lib")
ap.add_argument("--after-data", action="store_true")
a = ap.parse_args()
ROOT = os.path.abspath(a.old or a.new)
LIB = os.path.abspath(a.lib or a.old or a.new)
a.scratch = os.path.abspath(a.scratch); os.makedirs(a.scratch, exist_ok=True)
DB = os.path.join(a.scratch, "walk.db")
shutil.copyfile(a.db, DB)
FIN = os.path.join(ROOT, "finance")
if LIB != ROOT:
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


def check(name, ok, s676=True, note=""):
    res.append((name, bool(ok), s676, str(note)[:300]))


def con_():
    c = sqlite3.connect(DB, timeout=30)
    c.row_factory = sqlite3.Row
    return c


import flask                                                       # noqa: E402
import section_map, stock_app                                      # noqa: E402
for m in (section_map, stock_app):
    assert os.path.dirname(os.path.abspath(m.__file__)) == FIN, "%s not loaded from the root under test" % m.__name__
sm = section_map
TS = "2099-01-01T10:00:00"
c = con_()
sm.ensure(c)
# the box's state as it is today (the 27-Oct copy predates S669 / S671): the owner's rows of 28-Oct, as the two kits wrote them
for it in ("CAST SHOE S TYNOR", "PRIME CAST SHOE S"):
    c.execute("UPDATE stock_item_section SET section='Orthotics', source='owner', by_user='manoj (28-Oct-2026, S359)' WHERE item_key=? AND source='seed'", (it,))
for it in ("CREPE 8CM 3IN SUNLINE", "CREPE BANDAGE 6CM 2IN", "GLOCREPE", "LEUKOCREPE 6 CM", "LEUKOCREPE 8 CM", "LEUKOCREPE 10CM 4IN", "LEUKOCREPE 15CM 6INC", "TOPCREPE 10 CM", "TOPCREPE 15 CM"):
    c.execute("UPDATE stock_item_section SET section='Medicines', source='owner', by_user='manoj (28-Oct-2026, S359)' WHERE item_key=? AND source='seed'", (it,))
c.commit()
# the walk's OWN rulings (F-998): a cast shoe and a crepe the owner ruled, with seed sisters the word rule filed as consumables
for it, sec, src in (("WALK CAST SHOE S TYNOR", "Orthotics", "owner"), ("WALK CAST SHOE L UM", "Consumables", "seed"), ("WALK CAST SHOE M TYNOR", "Consumables", "seed"),
                     ("WALK LEUKOCREPE 6 CM", "Medicines", "owner"), ("WALK LEUKOCREPE 8 CM", "Consumables", "seed")):
    c.execute("INSERT OR REPLACE INTO stock_item_section (item_key,item,section,source,seeded_as,by_user,at) VALUES (?,?,?,?,?,?,?)",
              (sm.norm_key(it), it, sec, src, "Consumables", "walk", TS))
c.commit()
OWNER0 = c.execute("SELECT item_key, section, at FROM stock_item_section WHERE source='owner' AND item_key NOT LIKE 'WALK %' ORDER BY 1").fetchall()

# ---- A: the family key -------------------------------------------------------------------------------------------------------------
def fam(x):
    try:
        return sm.family(x)
    except Exception as e:                                        # noqa: BLE001
        return "ERR %s" % e
check("A1 CAST SHOE L UM -> CAST SHOE", fam("CAST SHOE L UM") == "CAST SHOE", note=fam("CAST SHOE L UM"))
check("A2 LEUKOCREPE 10CM*4IN -> LEUKOCREPE", fam("LEUKOCREPE 10CM*4IN") == "LEUKOCREPE", note=fam("LEUKOCREPE 10CM*4IN"))
check("A3 L S BELT XL CONT GRAY UNIS -> L S BELT; G DRESS 10 -> G DRESS (a size letter before the product word is not a cut)", fam("L S BELT XL CONT GRAY UNIS") == "L S BELT" and fam("G DRESS 10") == "G DRESS", note=(fam("L S BELT XL CONT GRAY UNIS"), fam("G DRESS 10")))
check("A4 BLING ELASTIC SHOULDER IMMOB S -> ... IMMOB", fam("BLING ELASTIC SHOULDER IMMOB S") == "BLING ELASTIC SHOULDER IMMOB")
check("A5 a name with no size word is its own family", fam("GLOCREPE") == "GLOCREPE" and fam("TAPEASE NS SPRAY") == "TAPEASE NS SPRAY")
check("A6 LINVIZ 600 6T -> LINVIZ; PRIME CAST SHOE S -> PRIME CAST SHOE", fam("LINVIZ 600 6T") == "LINVIZ" and fam("PRIME CAST SHOE S") == "PRIME CAST SHOE")

# ---- B: the owner's families ----------------------------------------------------------------------------------------------------------
try:
    fams, who = sm.owner_families(c)
except Exception as e:                                            # noqa: BLE001
    fams, who = {}, {}
    check("B0 owner_families runs", False, note=e)
check("B1 WALK CAST SHOE -> Orthotics, taught by the walk's own ruled row", fams.get("WALK CAST SHOE") == "Orthotics" and who.get("WALK CAST SHOE") == "WALK CAST SHOE S TYNOR", note=(fams.get("WALK CAST SHOE"), who.get("WALK CAST SHOE")))
check("B2 WALK LEUKOCREPE -> Medicines; the box's own CAST SHOE / LEUKOCREPE rulings read the same way", fams.get("WALK LEUKOCREPE") == "Medicines" and fams.get("CAST SHOE") == "Orthotics" and fams.get("LEUKOCREPE") == "Medicines")
# a family ruled in two sections rules nothing (own rows)
c.execute("INSERT OR REPLACE INTO stock_item_section (item_key,item,section,source,seeded_as,by_user,at) VALUES ('WALK SPLIT FAM S','WALK SPLIT FAM S','Orthotics','owner',NULL,'walk',?)", (TS,))
c.execute("INSERT OR REPLACE INTO stock_item_section (item_key,item,section,source,seeded_as,by_user,at) VALUES ('WALK SPLIT FAM L','WALK SPLIT FAM L','Medicines','owner',NULL,'walk',?)", (TS,))
c.commit()
try:
    fams, who = sm.owner_families(c)
except Exception:                                                 # noqa: BLE001
    fams = {}
check("B3 a family the owner ruled in two sections rules nothing", bool(fams) and "WALK SPLIT FAM" not in fams)

# ---- C: the sweep (the installer's data step) ------------------------------------------------------------------------------------------
before = {r[0]: (r[1], r[2]) for r in c.execute("SELECT item, section, source FROM stock_item_section")}
try:
    moves = sm.sweep_families(c, by_user="walk", ts=TS); c.commit()
except Exception as e:                                            # noqa: BLE001
    moves = None
    check("C0 sweep_families runs", False, note=e)
OWN = {"WALK CAST SHOE L UM", "WALK CAST SHOE M TYNOR", "WALK LEUKOCREPE 8 CM"}
if moves is not None:
    got = {m[0] for m in moves}
    fams_now, _w = sm.owner_families(c)
    if not a.after_data:
        check("C1 the sweep moves the walk's three seed sisters; every other move is a non-owner sister of a family the owner ruled (the box's state, listed)",
              OWN <= got and all(before[m[0]][1] != "owner" and fams_now.get(sm.family(m[0])) == m[2] for m in moves),
              note="moved: %s" % sorted(got - OWN))
    check("C2 every move is seed -> the owner's section, source 'family', seeded_as kept",
          all(before[m[0]][1] != "owner" and c.execute("SELECT section, source, seeded_as FROM stock_item_section WHERE item=?", (m[0],)).fetchone()[:3] == (m[2], "family", before[m[0]][0]) for m in moves) if moves else a.after_data,
          note=moves)
    try:
        again = sm.sweep_families(c, by_user="walk", ts=TS); c.commit()
    except Exception as e:                                        # noqa: BLE001
        again = None
    check("C3 a second sweep moves nothing", again == [], note=again)
    print("  --  the sweep on this database moved: %s" % ("; ".join("%s %s -> %s" % (m[0], m[1], m[2]) for m in moves) or "nothing"))
check("C4 the owner's rows are untouched by the sweep", (moves is not None) and c.execute("SELECT item_key, section, at FROM stock_item_section WHERE source='owner' AND item_key NOT LIKE 'WALK %' ORDER BY 1").fetchall() == OWNER0)

# ---- D: seeding a new name ------------------------------------------------------------------------------------------------------------
NEW = ["WALK CAST SHOE XL TYNOR", "WALK LEUKOCREPE 12 CM", "WALK NEW TAB 10", "WALK KNEE CAP L", "WALK CAST SHOE S TYNOR", "WALK ZZZ GAUZE 6 CM", "WALK ZZZ GAUZE 8 CM"]
try:
    added, kept = sm.seed(c, NEW, by_user="walk-seed", ts=TS); c.commit()
except Exception as e:                                            # noqa: BLE001
    added, kept = None, None
    check("D0 seed runs", False, note=e)
row = lambda it: c.execute("SELECT section, source, seeded_as, by_user FROM stock_item_section WHERE item_key=?", (sm.norm_key(it),)).fetchone()  # noqa: E731
check("D1 a new CAST SHOE size takes his Orthotics (family), the word rule's Consumables kept as seeded_as", tuple(row("WALK CAST SHOE XL TYNOR") or ())[:3] == ("Orthotics", "family", "Consumables"), note=tuple(row("WALK CAST SHOE XL TYNOR") or ()))
check("D2 a new LEUKOCREPE size takes his Medicines (family)", tuple(row("WALK LEUKOCREPE 12 CM") or ())[:3] == ("Medicines", "family", "Consumables"), note=tuple(row("WALK LEUKOCREPE 12 CM") or ()))
check("D3 a name of no ruled family takes the word rule as before (seed)", tuple(row("WALK NEW TAB 10") or ())[:3] == ("Medicines", "seed", "Medicines") and tuple(row("WALK KNEE CAP L") or ())[:3] == ("Orthotics", "seed", "Orthotics"), s676=False)
check("D4 a name that has a row is kept, never overwritten", added == 6 and kept == 1 and row("WALK CAST SHOE S TYNOR")[1] == "owner", s676=False, note=(added, kept))
check("D5 the family row names the teaching row", "WALK CAST SHOE S TYNOR" in (row("WALK CAST SHOE XL TYNOR") or ["", "", "", ""])[3])

# ---- E: his tap reaches the sisters -------------------------------------------------------------------------------------------------
ok, msg = sm.set_section(c, "WALK ZZZ GAUZE 6 CM", "Medicines", by_user="manoj", ts=TS); c.commit()
check("E1 set_section still sets the row (owner)", ok and tuple(row("WALK ZZZ GAUZE 6 CM"))[:2] == ("Medicines", "owner"), s676=False, note=msg)
check("E2 ... and the sister size follows at once (family), the message says so", tuple(row("WALK ZZZ GAUZE 8 CM") or ())[:2] == ("Medicines", "family") and "1 sister" in msg, note=(tuple(row("WALK ZZZ GAUZE 8 CM") or ()), msg))
ok2, msg2 = sm.set_section(c, "WALK ZZZ GAUZE 8 CM", "Orthotics", by_user="manoj", ts=TS); c.commit()
check("E3 a second ruling on the sister splits the family: both stay his word, nothing else moves", hasattr(sm, "sweep_families") and tuple(row("WALK ZZZ GAUZE 8 CM"))[:2] == ("Orthotics", "owner") and tuple(row("WALK ZZZ GAUZE 6 CM"))[:2] == ("Medicines", "owner") and "sister" not in msg2, note=msg2)

# ---- F: the closing's door (stock_app.api_snapshot) ------------------------------------------------------------------------------------
WHO = {"user": "walk_s676", "roles": ["checker"], "role": "checker"}
app = flask.Flask("walk_s676")
stock_app.init(app, con_, lambda *r, **k: (dict(WHO), None), marg_token="walk-s676-token")
cl = app.test_client()
as_on0, items0 = sm.snapshot_items(c)
body_items = [dict(item=it, qty=1, packing="1*10", pack_size=10) for it in items0]
body_items += [dict(item="WALK CAST SHOE XXL UM", qty=2, packing="1*1", pack_size=1), dict(item="WALK FRESH KNEE CAP M", qty=1, packing="1*1", pack_size=1)]
r = cl.post("/finance/stock/api/snapshot", json=dict(as_on="01-01-2099", source="push_snapshot walk", items=body_items), headers={"X-Finance-Marg": "walk-s676-token"})
check("F0 the closing is accepted as before", r.status_code == 200 and (r.get_json() or {}).get("ok") is True, s676=False, note=(r.status_code, (r.get_json() or {}).get("error")))
check("F1 a new name on the closing has its row by the time the closing is stored -- the family rule first", tuple(row("WALK CAST SHOE XXL UM") or ())[:2] == ("Orthotics", "family") and (row("WALK CAST SHOE XXL UM") or ["", "", "", ""])[3].startswith("closing 01-01-2099"), note=tuple(row("WALK CAST SHOE XXL UM") or ()))
check("F2 ... the word rule second", tuple(row("WALK FRESH KNEE CAP M") or ())[:3] == ("Orthotics", "seed", "Orthotics"), note=tuple(row("WALK FRESH KNEE CAP M") or ()))
n_before = c.execute("SELECT COUNT(*) FROM stock_item_section").fetchone()[0]
r2 = cl.post("/finance/stock/api/snapshot", json=dict(as_on="02-01-2099", source="push_expected walk", items=body_items + [dict(item="WALK EXPECTED ONLY", qty=1, packing="1*1", pack_size=1)]), headers={"X-Finance-Marg": "walk-s676-token"})
n_after = c.execute("SELECT COUNT(*) FROM stock_item_section").fetchone()[0]
check("F3 the computed feed (push_expected) seeds nothing", r2.status_code == 200 and n_before == n_after and row("WALK EXPECTED ONLY") is None, s676=False, note=(r2.status_code, n_before, n_after))
# the door is fail-soft: a broken map must not refuse the closing
if hasattr(sm, "on_closing"):
    keep = sm.on_closing
    sm.on_closing = lambda *x, **k: (_ for _ in ()).throw(RuntimeError("walk: the map is broken"))
    r3 = cl.post("/finance/stock/api/snapshot", json=dict(as_on="03-01-2099", source="push_snapshot walk", items=body_items), headers={"X-Finance-Marg": "walk-s676-token"})
    sm.on_closing = keep
    check("F4 a fault in the map never refuses the closing (fail-soft)", r3.status_code == 200 and (r3.get_json() or {}).get("ok") is True and c.execute("SELECT COUNT(*) FROM stock_snapshot WHERE as_on='03-01-2099'").fetchone()[0] == len(body_items), note=r3.status_code)
else:
    check("F4 a fault in the map never refuses the closing (fail-soft)", False, note="no on_closing")

# ---- G: older behaviour unchanged --------------------------------------------------------------------------------------------------------
check("G1 classify: the S268 word rule as before", sm.classify("ZIG ZAG COTTON 500GM") == "Consumables" and sm.classify("KNEE SUPPORT HINGED M") == "Orthotics" and sm.classify("ACILOC 300") == "Medicines", s676=False)
check("G2 is_orthotic / is_consumable as before (S662: DYNA a whole word)", not sm.is_orthotic("DYNAPAR QPS PLUS") and sm.is_consumable("CREPE BANDAGE 6CM*2IN"), s676=False)
ok3, msg3 = sm.inherit(c, "WALK KNEE CAP L", "WALK KNEE CAP L NEW", by_user="walk", ts=TS); c.commit()
check("G3 inherit (a rename keeps its section) as before", ok3 and tuple(row("WALK KNEE CAP L NEW"))[:2] == ("Orthotics", "rename"), s676=False, note=msg3)
check("G4 summary / rows / items_in answer", sm.summary(c)["total"] > 300 and any(x["item"] == "CAST SHOE S TYNOR" for x in sm.rows(c, limit=2000)) and "CAST SHOE S TYNOR" in sm.items_in(c, "Orthotics"), s676=False)
check("G5 stock_app's own lists are untouched (count #1's record)", stock_app._is_consumable("CREPE BANDAGE 6CM*2IN") and not stock_app._is_orthotic("CAST SHOE S TYNOR"), s676=False)
c.close()

# ---- the verdict ------------------------------------------------------------------------------------------------------------------------
for n, ok, s, note in res:
    print(("  ok  " if ok else "  RED ") + n + ("" if ok else ("   | " + note if note else "")))
g = sum(1 for _, ok, _, _ in res if ok)
if a.old:
    red676 = sum(1 for _, ok, s, _ in res if not ok and s); redold = sum(1 for _, ok, s, _ in res if not ok and not s)
    print("%d S676 check(s) red · %d older red · %d green" % (red676, redold, g))
else:
    print("%d of %d green" % (g, len(res)))
