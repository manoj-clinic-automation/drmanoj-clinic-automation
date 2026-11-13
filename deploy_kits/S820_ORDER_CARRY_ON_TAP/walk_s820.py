#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s820.py DIR FINANCE SHARED DB [--control] -- kit S820_ORDER_CARRY_ON_TAP (13-Nov-2026, Sanjeevni session 451).

DIR holds order_sheet.py, order_s778.py, porders_s454.py, order_track.py and order_track_page.py (the built ones, or the live ones for --control); every other module comes
from FINANCE / SHARED. The walk works on a COPY of DB with MADE-UP rows only (a dealer named WALK S820 PHARMA): one sheet line on
today's card (Marg's open order is stood in for), and one medicine of that dealer that did not come (an order_carry row made today).
Nothing is sent, nothing of the real database is touched.
  G1 with the setting at its default, the undelivered medicine is NOT on the dealer's card (so not in its WhatsApp nor its print)
  G2 it IS in the red 'Purane order' box at once (age 0), kind carry
  G3 the default of order.carry_on_card is 0 and the owner's settings card accepts 0 and 1, refuses 2
  G4 'Dobara order karo' on it puts it on the dealer's card (src s778), the box no longer shows it
  G5 with the setting at 1 the old way stands: the medicine rides on the card (src carry) and the box does not show it before 3 days
  G6 the sheet line itself is on the card in every case
  G7 the words follow the setting: the order list's short line, the owner's Needs-you line and the short section's note
  G8 the red box as the screen draws it carries the line and its two buttons
Last line: 'WALK S820 GREEN' / 'WALK S820 RED n' ; with --control: 'CONTROL S820 RED as it must be' when any check is red."""
import os, shutil, sqlite3, sys, tempfile, warnings

warnings.filterwarnings("ignore")
D, FIN, SH, DB = sys.argv[1:5]
CONTROL = "--control" in sys.argv[5:]
sys.path[:0] = [D, FIN, SH]
sys.dont_write_bytecode = True
TMP = tempfile.mkdtemp(prefix="w820_")
DBC = os.path.join(TMP, "f.db")
shutil.copyfile(DB, DBC)
import order_sheet as OS      # noqa: E402
import order_s778 as S        # noqa: E402
import porders_s454 as PO     # noqa: E402
import order_track as OT      # noqa: E402
import order_track_page as TP  # noqa: E402
for m, n in ((OS, "order_sheet.py"), (S, "order_s778.py"), (PO, "porders_s454.py"), (OT, "order_track.py"), (TP, "order_track_page.py")):
    if os.path.dirname(os.path.abspath(m.__file__)) != os.path.abspath(D):
        sys.exit("STOP: %s was not taken from %s" % (n, D))

VENDOR = "WALK S820 PHARMA"
con = sqlite3.connect(DBC)
con.row_factory = sqlite3.Row
OS.ensure(con)
S.ensure(con)
SN = OS._pa().supplier_key(VENDOR)
TODAY = OS.today()
SHEET = dict(id=-8201, supplier_norm=SN, supplier=VENDOR, item="WALK S820 TAB", qty=5, loose=0, strip=1, pack_size=10, packing="1*10",
             rate_p=1000, entry_no="W820", reorder_day=None, line_date=TODAY.isoformat(), state="new")
_real_open = OS.open_order


def fake_open(con_, t=None):
    g = _real_open(con_, t) if False else None              # noqa: F841 -- the real sheet is not used: a made-up one stands in
    return {"groups": {"to_order": [dict(SHEET)], "old": []}}


OS.open_order = fake_open
con.execute("DELETE FROM setting WHERE key='order.carry_on_card'")
con.execute("INSERT INTO order_carry (vendor, supplier_norm, item, from_order_id, from_line_id, qty, pack_size, reason, at) "
            "VALUES (?,?,?,?,?,?,?,?,?)", (VENDOR, SN, "WALK S820 SYRUP", -8200, -820001, 2, 1, "tapped_missing", OS.now_iso()))
CID = str(con.execute("SELECT id FROM order_carry WHERE from_line_id=-820001").fetchone()[0])
con.commit()
red = []


def check(name, ok, why=""):
    print(("GREEN " if ok else "RED   ") + name + ("" if ok else "  -- " + why))
    if not ok:
        red.append(name)


def card():
    return next((e for e in S.adjust_entries(con, OS.entries(con)) if e["sn"] == SN), None)


def box():
    return [c for c in S.red_lines(con) if c["sn"] == SN]


c = card()
srcs = sorted((l["src"], l["item"]) for l in (c or {}).get("lines", []))
check("G6 the sheet line is on the dealer's card", ("sheet", "WALK S820 TAB") in srcs, str(srcs))
check("G1 the undelivered medicine is NOT on the card by itself", not any(s == "carry" for s, _i in srcs), str(srcs))
sw = OT.short_words(con, dict(sn=SN), dict(id=-820001, item="WALK S820 SYRUP"), False)
check("G7a the order list's short line says it waits in the box", "Purane order box" in sw, sw)
ol = (OT.owner_line(con, OS.now()) or {}).get("text", "")
check("G7b the owner's Needs-you line says Old orders box", "Old orders box" in ol, ol)
try:
    g7c = "Purane order box" in TP._L(False, "s820_sh_s") and "Old orders box" in TP._L(True, "s820_sh_s")
except Exception as ex:                                   # noqa: BLE001 -- the live file has no such words: red, not a crash
    g7c = False
check("G7c the short section's note (staff and owner) names the box", g7c)
html = S.red_box(con, False)
check("G8 the red box draws the line with Dobara order karo", "WALK S820 SYRUP" in html and "Dobara order karo" in html)
b = box()
hit = [x for x in b if x["kind"] == "carry" and x["ref"] == CID]
check("G2 it is in the Purane order box at once", len(hit) == 1 and hit[0]["age"] == 0, str([(x["kind"], x["ref"], x["age"]) for x in b]))
check("G3a the setting order.carry_on_card exists, default 0", OS.SETTINGS.get("order.carry_on_card", ("?",))[0] == "0")
check("G3b the settings card accepts 0 and 1, refuses 2",
      PO._valid("order.carry_on_card", "0")[0] and PO._valid("order.carry_on_card", "1")[0] and not PO._valid("order.carry_on_card", "2")[0])
if hit:
    body, code = S.again(con, "walk_s820", "carry", CID)
    c = card()
    srcs = sorted((l["src"], l["item"]) for l in (c or {}).get("lines", []))
    check("G4a Dobara order karo puts it on the card", code == 200 and body.get("ok") and ("s778", "WALK S820 SYRUP") in srcs, "%s %s %s" % (code, body, srcs))
    check("G4b the box no longer shows it", not [x for x in box() if x["kind"] == "carry" and x["ref"] == CID])
    con.execute("UPDATE order_s778_again SET cleared_at=?, cleared_by='walk' WHERE kind='carry' AND ref=?", (OS.now_iso(), CID))
    con.commit()
else:
    check("G4 Dobara order karo (not reached: the line is not in the box)", False)
con.execute("INSERT INTO setting (key, value, note) VALUES ('order.carry_on_card','1','walk') ON CONFLICT(key) DO UPDATE SET value='1'")
con.commit()
c = card()
srcs = sorted((l["src"], l["item"]) for l in (c or {}).get("lines", []))
check("G5a with the setting at 1 the medicine rides on the card (as before)", ("carry", "WALK S820 SYRUP") in srcs, str(srcs))
check("G5b with the setting at 1 the box keeps its three-day rule", not [x for x in box() if x["kind"] == "carry" and x["ref"] == CID])
check("G6b the sheet line is still on the card", ("sheet", "WALK S820 TAB") in srcs, str(srcs))
sw = OT.short_words(con, dict(sn=SN), dict(id=-820001, item="WALK S820 SYRUP"), False)
check("G7d with the setting at 1 the old words stand", "agle order mein khud jud jayega" in sw, sw)
con.close()
shutil.rmtree(TMP, ignore_errors=True)
if CONTROL:
    print("CONTROL S820 RED as it must be" if red else "CONTROL S820 GREEN -- the control did not go red")
else:
    print("WALK S820 GREEN" if not red else "WALK S820 RED %d" % len(red))
