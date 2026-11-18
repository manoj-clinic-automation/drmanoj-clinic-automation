#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s866.py -- kit S866 (the parent, S480, 18-Nov-2026). On a MADE-UP shelf (an empty sqlite built by packs.ensure, made-up
card files): the card rows and cells say the true reason; the electricity row names the card statement it waits on; the page's
template renders. Control: the live packs.py goes red.     python3 walk_s866.py <dir holding packs.py + packs.html> <scratch>"""
import os, sqlite3, sys
d, scr = sys.argv[1:3]
here = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != here]          # F-1441: never the kit's own copy by accident
sys.path.insert(0, d)
os.makedirs(scr, exist_ok=True)
ok, n = 0, 0


def chk(name, cond):
    global ok, n
    n += 1
    ok += bool(cond)
    print(("ok   " if cond else "FAIL ") + name)


try:
    import packs as p
except Exception as e:                                   # noqa: BLE001
    print("FAIL import packs: %s" % e)
    print("WALK 0/18")
    sys.exit(1)
db = os.path.join(scr, "made_up.db")
if os.path.exists(db):
    os.remove(db)
con = sqlite3.connect(db)
con.row_factory = sqlite3.Row
p.ensure(con)
sid = {r["key"]: r["id"] for r in con.execute("SELECT id, key FROM stmt_slot WHERE kind='card'")}


def add(slot, folder, sub, name, pf, pt, rs, locked=0, unl=""):
    con.execute("INSERT INTO stmt_file (drive_id, name, mtime, size, folder, subfolder, slot_id, period_from, period_to, read_status, "
                "matched_status, locked, unlocked_path) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("made-up-%s" % name, name, pt + "T06:25:00", 1000, folder, sub, sid[slot], pf, pt, rs, "", locked, unl))


# made-up shelf, the month under test = 2031-03 (no real date)
add("card_hdfc_regalia", "cards", "HDFC Made-up", "h_mar.pdf", "2031-03-15", "2031-03-15", "locked -- no password", 1)
add("card_icici_amazon", "decrypted", "Amazon Made-up", "a_feb.pdf", "2031-01-13", "2031-02-12", "read")
add("card_icici_amazon", "cards", "Amazon Made-up", "a_apr.pdf", "2031-04-13", "2031-04-13", "locked -- no password", 1)
add("card_icici_coral", "decrypted", "Coral Made-up", "c_mar.pdf", "2031-02-03", "2031-03-02", "read")
add("card_icici_coral", "cards", "Coral Made-up", "c_apr.pdf", "2031-04-02", "2031-04-02", "locked -- no password", 1)
con.commit()
M = "2031-03"
cl = {c["slot"]: c for c in p.cells(con, M) if c["kind"] == "card"}
WHY = getattr(p, "_s866_card_why", lambda *a: ("", ""))          # the control (the live file) has none: red, never a crash
ELEC = getattr(p, "_s866_elec_wait", lambda *a: "")
try:
    W = {k: WHY(con, c, M) for k, c in cl.items()}
except Exception as e:                                   # noqa: BLE001
    W = {}
    print("FAIL _s866_card_why: %s" % e)
h = W.get("card_hdfc_regalia", ("", ""))
chk("C1 a locked statement of the month: missing, 'here but locked', the password step named", h[0] == "missing" and "dated 15-Mar-2031 is here but locked" in h[1] and "Statement passwords" in h[1])
a = W.get("card_icici_amazon", ("", ""))
chk("C2 the bank never mailed the month's: 'no statement dated March 2031 came', the next one named", a[0] == "missing" and "no statement dated March 2031 came from the bank" in a[1] and "13-Apr-2031" in a[1])
chk("C3 ... where to put it: the card's own Drive folder", "Credit Card Statements > Amazon Made-up" in a[1])
chk("C4 ... and that the next one is locked too", "locked too" in a[1])
c = W.get("card_icici_coral", ("", ""))
chk("C5 the month's statement read: READY (a newer locked one never makes it late), the newer one named", c[0] == "ready" and c[1].startswith("statement dated 02-Mar-2031") and "02-Apr-2031" in c[1])
chk("C6 the cells carry the note; never 'decrypted twin'", all(cl[k].get("note") for k in cl) and not any("twin" in (cl[k].get("note") or "") for k in cl))
# a later month with nothing at all: 'has not come yet'
c9 = {c["slot"]: c for c in p.cells(con, "2031-09") if c["kind"] == "card"}
chk("C7 nothing at all for the month: 'has not come yet'", WHY(con, c9["card_hdfc_regalia"], "2031-09") == ("missing", "the statement dated September 2031 has not come yet"))
# a later READ statement, none in the month, nothing locked: no 'locked too'
con.execute("UPDATE stmt_file SET folder='decrypted', locked=0, read_status='read' WHERE name='a_apr.pdf'")
con.commit()
cla = {c["slot"]: c for c in p.cells(con, M) if c["kind"] == "card"}
a2 = WHY(con, cla["card_icici_amazon"], M)
chk("C8 next one read, month's never mailed: named, no 'locked too'", a2[0] == "missing" and "no statement dated March 2031" in a2[1] and "locked too" not in a2[1])
con.execute("UPDATE stmt_file SET folder='cards', locked=1, read_status='locked -- no password' WHERE name='a_apr.pdf'")
con.commit()
# the pack's rows
r = p.pack_rows(con, M, light=True)
rows = {x["key"]: x for x in (r[0] if isinstance(r, tuple) else r)}
chk("C9 rows: HDFC missing / Amazon missing / Coral ready", (rows["card:card_hdfc_regalia"]["status"], rows["card:card_icici_amazon"]["status"], rows["card:card_icici_coral"]["status"]) == ("missing", "missing", "ready"))
chk("C10 no row says 'decrypted twin' or 'decrypted copy not yet made'", not any(("twin" in (x["why"] or "")) or ("decrypted copy not yet made" in (x["why"] or "")) for x in rows.values()))
e = rows["electricity"]["why"]
chk("C11 electricity short: names the Amazon Pay card's statement it waits on", rows["electricity"]["status"] == "missing" and "the bill the ICICI Amazon Pay card pays is read from that card's statement: no statement dated March 2031" in e)
chk("C12 ... and never names the other cards", "HDFC" not in e and "Coral" not in e)
# Amazon's month statement arrives (read): the electricity line no longer blames the card
add("card_icici_amazon", "decrypted", "Amazon Made-up", "a_mar.pdf", "2031-02-13", "2031-03-12", "read")
con.commit()
cl3 = [c for c in p.cells(con, M)]
chk("C13 the card's statement read: the electricity line says nothing of it", ELEC(con, cl3, M) == "" and hasattr(p, "_s866_elec_wait"))
try:
    con.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT)")
    con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('packs.electricity_cards', 'card_hdfc_regalia')")
    con.commit()
    w14 = ELEC(con, cl3, M)
    con.execute("DELETE FROM setting WHERE key='packs.electricity_cards'")
    con.commit()
except Exception as ex:                                  # noqa: BLE001
    w14 = "error %s" % ex
chk("C14 the setting names another card: that card is the one named, not Amazon", "HDFC Business Regalia card pays" in w14 and "Amazon" not in w14)
# the page's template renders and shows the note, not the twin line
try:
    import jinja2
    html = open(os.path.join(d, "packs.html"), encoding="utf-8").read()
    out = jinja2.Environment().from_string(html).render(month=M, me="made-up")
    chk("C15 packs.html renders; the cell shows c.note", "c.note" in out and "newest original has no decrypted twin" not in out)
except Exception as ex:                                  # noqa: BLE001
    chk("C15 packs.html renders: %s" % ex, False)
chk("C16 never raises on a bad card row", WHY(con, {"slot_id": None, "file": None}, "bad")[0] == "missing")
# review SHOULD: an original on the shelf for the month that the unlock step never marked ('locked original') -> 'not opened yet'
add("card_hdfc_regalia", "cards", "HDFC Made-up", "h_jun.pdf", "2031-06-15", "2031-06-15", "locked original", 1)
con.commit()
c6 = {c["slot"]: c for c in p.cells(con, "2031-06") if c["kind"] == "card"}
w17 = WHY(con, c6["card_hdfc_regalia"], "2031-06")
chk("C17 a file of the month the shelf has not marked: 'on the shelf but not opened yet', never 'not come'", w17[0] == "missing" and "on the shelf but not opened yet" in w17[1] and "not come" not in w17[1])
# review LOW 1: a stored password that did not open it is named as such
try:
    con.execute("INSERT OR REPLACE INTO stmt_secret (bank, secret, set_by, set_at) VALUES ('CARD:card_hdfc_regalia', 'made-up', 'walk', '2031-01-01')")
    con.commit()
    w18 = WHY(con, cl["card_hdfc_regalia"], M)[1]
    con.execute("DELETE FROM stmt_secret WHERE bank='CARD:card_hdfc_regalia'")
    con.commit()
except Exception as ex:                                  # noqa: BLE001
    w18 = "error %s" % ex
chk("C18 a stored password that did not open it: 'does not open it -- replace it', not 'no password stored'", "does not open it" in w18 and "no password is stored" not in w18)
print("WALK %d/%d" % (ok, n))
